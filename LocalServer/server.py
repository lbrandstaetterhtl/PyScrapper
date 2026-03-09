import sys, time, re, json, uuid
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

import platform
import subprocess


import os, signal
import asyncio

#Module imports for scrapping
from PythonModule import Session, Suno, Youtube 




#Global Variables
#Downlaod path
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_path)

#Runtime Logs will be saved under this path
log_dir = os.path.join(project_root, "LocalServer", "logs")
log_file = os.path.join(log_dir, "server_runtime.log")
#Make sure it exists and if it doesn't it will create it
os.makedirs(log_dir, exist_ok=True)


supported_providers = ["suno", "suno.com", "youtube", "youtube.com"]




#Session for cookies and stuff which will be used to request ressources
ses = Session.Session()

#The app
app = FastAPI()


#Queues
log_queue = asyncio.Queue(maxsize=5000)


#Events
quit_event = asyncio.Event()

#Sets
download_jobs = set()
search_jobs = set()
download_progress = {}



class CommandRequest(BaseModel):
    command: str


class DownloadRequest(BaseModel):
    provider: str
    url: str
    mediatype: str = ".mp3"
    download_path: str = os.path.join(project_root, "downloads")

class SearchRequest(BaseModel):
    provider: str
    search: str
    top: int = 5

class SearchError(Exception): ...
class CommandError(Exception): ...
class DownloadError(Exception): ...


async def logger(
        quit_event: asyncio.Event,
        log_queue: asyncio.Queue
        ):
#Setting up files where logs will be written to
    global log_file


    while not quit_event.is_set():
        try:
#Waits till something gets put into the queue
            message = await log_queue.get()

            if not isinstance(message, str):
                message = json.dumps(message, ensure_ascii=False)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{str(timestamp)}] " + message + "\n")

        except asyncio.CancelledError:
            break
#Just in case something will break the logger it will be output in terminal and not crash the server
        except Exception as e:
            print(e)
    




#Processes the commands from a user
async def process_commands(line: str, job_id:str):
    global quit_event, log_queue, log_file
    match line.lower():
        case "quit":
            
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                f.write(f"[{str(timestamp)}] " + "[INFO] Server shutting down..." + "\n")

            quit_event.set()
            if os.name == "nt":
                os._exit(0)
        case _:
            raise CommandError("PROCESS_COMMANDS: UNKNOWN COMMAND")
            


                


#Limits the parralel downloads to 50 at a time, change value for more or less downlaods
download_limiter = asyncio.Semaphore(50)
#Starts download from a user
async def process_downloads(
        download_request: DownloadRequest,
        progress_dict: dict
          ):
    global ses, supported_providers, log_queue
    
    os.makedirs(download_request.download_path, exist_ok=True)

    try:
        if download_request.provider.lower() not in supported_providers:
            raise DownloadError(f"Unknown provider {download_request.provider}")


        if download_request.provider.lower() in ("suno", "suno.com"):
            async with download_limiter:
                await asyncio.to_thread(Suno.download, session=ses, url=download_request.url, out_path=download_request.download_path,  mediatype=download_request.mediatype, progress_dict=progress_dict)
                

        elif download_request.provider.lower() in ("youtube", "youtube.com"):
            async with download_limiter:
                if download_request.mediatype.lower() == ".mp4":
                    await asyncio.to_thread(Youtube.download, url=download_request.url, out_path=download_request.download_path, progress_dict=progress_dict)
                else:
                    await asyncio.to_thread(Youtube.download_audio_only, url=download_request.url, out_path=download_request.download_path, progress_dict=progress_dict)

        log_queue.put_nowait(f"[INFO] Successfully completed downloadjob {progress_dict.get('id')}")
        

              
            

    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Failed download for job {progress_dict.get('id')}.\nError Message: {str(e)}")
        progress_dict["status"] = "error"
        progress_dict["errorMessage"] = str(e)
       
        
        
        

async def process_search(search_request: SearchRequest, search_id:str):
    global ses, supported_providers

    try:
        if search_request.provider.lower() not in supported_providers:
            raise SearchError("PROCESS_SEARCH: No supported provider was given")




        if search_request.provider.lower() in ("youtube", "youtube.com"):
            results = await asyncio.to_thread(Youtube.search, session=ses, search=search_request.search, top=search_request.top)

        response = {
                    "provider": search_request.provider,
                    "query": search_request.search,
                    "results": results
                }
        return response
    

        

    except Exception as e:
        raise SearchError(f"SEARCH_ERROR: {str(e)}")




@app.get("/")
async def root():
    return {
        "message": "Server startup successful!",
    }





@app.on_event("startup")
async def startup_event():
    global quit_event, log_queue
   
    asyncio.create_task(logger(quit_event, log_queue))

    log_queue.put_nowait("[INFO] Server started successfully")
    
    







@app.post("/command")
async def receive_command(data: CommandRequest):
    try:
        task_id = str(uuid.uuid4())
        response = await process_commands(data.command, task_id)
        return response
    except Exception as e:
        log_queue.put([f"[ERROR] Error handling command {data.command}.\nError Message: {str(e)}"])





@app.post("/download")
async def receive_download(data: DownloadRequest):
    global log_queue
    try:
        task_id = str(uuid.uuid4())

        download_progress[task_id] = {
            "id": task_id,
            "status": "queued",
            "downloadProgress": "0%",
            "errorMessage": ""
        }

        task = asyncio.create_task(process_downloads(data, download_progress[task_id]), name=task_id)
        task.add_done_callback(lambda t: download_jobs.discard(t))
        download_jobs.add(task)
        log_queue.put_nowait(f"[INFO] Created download task with id {task_id} for provider {data.provider} with url {data.url}")

        return {"id": task_id, "message": f"Request received for download, you can view progress under /download/progress/{task_id}"}, 200
        
    
    except (ValueError, TypeError) as e:
        log_queue.put_nowait(f"[ERROR] failed to create download task with arguments given: provider {data.provider}, url: {data.url}, filepath {data.download_path}.\nError Message: Invalid type for {str(e)}")
        return {"error": f"Invalid type for {str(e)}"}, 400

    except Exception as e:
        log_queue.put_nowait(f"[ERROR] failed to create download task with arguments given: provider {data.provider}, url: {data.url}, filepath {data.download_path}.\nError Message: {str(e)}")
        return {"error": str(e)}, 400




@app.get("/download/progress/{task_id}")
async def get_download_progress(task_id: str):
    progress = download_progress.get(task_id)
    if not progress:
        log_queue(f"[ERROR] Tried to access resource /download/progress/{task_id} which doesn't exist")
        return {"error": "No such task"}, 404
    return progress, 200







@app.post("/search")
async def receive_search(data: SearchRequest):
    try:
        search_id = str(uuid.uuid4())
        response = await process_search(data, search_id)
        log_queue.put_nowait(f"[INFO] Search succesfull for job {search_id} with query {data.search} and provider {data.provider}")
        return response
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Failed search task with given arguments: id {search_id} provider {data.provider} and searchinput {data.search}.\n Error Message:{str(e)}")
        return {"error": str(e)}, 400





start_time = time.time()

@app.get("/health")
def health():
    uptime_seconds = time.time() - start_time
    try:
        mem = self_memory_mb()
    except Exception as e:
        mem = None

    return {
        "ok": True,
        "uptime_seconds": round(uptime_seconds, 2),
        "memory_mb": mem,
        "pid": os.getpid(),
        "processes": list_python_processes()
    }, 200

def self_memory_mb():
    pid = os.getpid()
    out = subprocess.check_output(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
        text=True,
        errors="replace"
    )
    line = out.splitlines()[1]
    mem = line.split(",")[-1]
    digits = re.sub(r"\D", "", mem) 
    if not digits:
        return None
    kb = int(digits)
    return round(kb / 1024, 2)

def list_python_processes():
    if platform.system() != "Windows":
        out = subprocess.check_output(["ps", "-eo", "pid,comm"], text=True)
        procs = []
        for line in out.splitlines()[1:]:
            pid, name = line.strip().split(None, 1)
            if name.lower().startswith("python"):
                procs.append({"pid": int(pid), "name": name})
        return procs

    ps = r"""
Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" |
Select-Object ProcessId, Name |
ConvertTo-Json
""".strip()

    out = subprocess.check_output(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        text=True,
        encoding="utf-8",
        errors="replace"
    ).strip()

    if not out:
        return []

    data = json.loads(out)
    if isinstance(data, dict):
        data = [data]

    return [{"pid": int(p["ProcessId"]), "name": p["Name"]} for p in data]