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





class CommandRequest(BaseModel):
    command: str


class DownloadRequest(BaseModel):
    provider: str
    url: str
    mediatype: str = ".mp3"
    download_path: str = os.path.join(project_root, "downloads")

class JobResponse(BaseModel):
    id: str
    jobtype: str
    status: str 
    message: dict





async def logger(
        quit_event: asyncio.Event,
        log_queue: asyncio.Queue
        ):
#Setting up files where logs will be written to
    global log_dir
    log_file = os.path.join(log_dir, "server_runtime.log")


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
    global quit_event
    match line.lower():
        case "quit":
            quit_event.set()
            if os.name == "nt":
                os._exit(0)
        case _:
            response = JobResponse(
                id= job_id,
                jobtype= "command",
                status= "error",
                message= {
                    "error": "unknown command", "command": line
                }
            )
            try:
                log_queue.put_nowait(response.model_dump_json())
            except asyncio.QueueFull:
                pass
            return response


                


#Limits the parralel downloads to 50 at a time, change value for more or less downlaods
download_limiter = asyncio.Semaphore(50)
#Starts download from a user
async def process_downloads(download_request: DownloadRequest, job_id:str):
    global ses, supported_providers
    
    os.makedirs(download_request.download_path, exist_ok=True)

    try:
        if download_request.provider.lower() not in supported_providers:
            response = JobResponse(
             id=job_id,
                jobtype="download",
                status="error",
                message={"error": f"Unknown provider {download_request.provider}"}  
           )


        if download_request.provider.lower() in ("suno", "suno.com"):
            async with download_limiter:
                last_download, identifier = await asyncio.to_thread(Suno.download, session=ses, url=download_request.url, out_path=download_request.download_path,  mediatype=download_request.mediatype)
                

        elif download_request.provider.lower() in ("youtube", "youtube.com"):
            async with download_limiter:
                if download_request.mediatype.lower() == ".mp4":
                    last_download, identifier = await asyncio.to_thread(Youtube.download, url=download_request.url, out_path=download_request.download_path)
                else:
                    last_download, identifier = await asyncio.to_thread(Youtube.download_audio_only, url=download_request.url, out_path=download_request.download_path)

        response = JobResponse(
                            id=job_id,
                            jobtype="download",
                            status="done",
                            message={
                                "provider": download_request.provider,
                                "identifier": identifier,
                                "file": last_download.get('file'),
                                "raw status": last_download.get('status')
        
                            } 
                )
        
        try:  
            log_queue.put_nowait(response.model_dump_json())
        except asyncio.QueueFull:
            pass
        return response

              
            

    except Exception as e:
        response = JobResponse(
            id=job_id,
            jobtype="download",
            status= "error",
            message={"error": str(e), "url": download_request.url}
        )
        try:
            log_queue.put_nowait(response.model_dump_json())
        except asyncio.QueueFull:
            pass
        return response
       
        
        
        

@app.get("/")
async def root():
    return {
        "message": "Server startup successful!",
    }





@app.on_event("startup")
async def startup_event():
    global quit_event, log_queue
   
    asyncio.create_task(logger(quit_event, log_queue))
    
    







@app.post("/command")
async def receive_command(data: CommandRequest):
    task_id = str(uuid.uuid4())
    response = await process_commands(data.command, task_id)
    return response





@app.post("/download")
async def receive_download(data: DownloadRequest):
    try:
        task_id = str(uuid.uuid4())
        response = await process_downloads(data, task_id)
        return response
        
    
    except (ValueError, TypeError) as e:
        return {"ERROR": f"Invalid type for {str(e)}"}

    except Exception as e:
        return {"ERROR": str(e)}






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
    }

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