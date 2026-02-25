import sys
import time

from fastapi import FastAPI
from pydantic import BaseModel

import os, signal
import asyncio

#Module imports for scrapping
from PythonModule import Session, Suno


class CommandRequest(BaseModel):
    command: str
class DownloadRequest(BaseModel):
    provider: str
    url: str
    mediatype: str = ".mp3"  # Default to .mp3, can be overridden by client

#Global Variables
#Downlaod path
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_path)


out_path = os.path.join(project_root, "Downloads")


#Make sure it exists and if it doesn't it will create it
os.makedirs(out_path, exist_ok=True)

#Session for cookies and stuff which will be used to request ressources
ses = Session.Session()

#The app
app = FastAPI()


#Queues
command_queue = asyncio.Queue()
download_queue = asyncio.Queue()

last_download = None
identifier = None


#Events
quit_event = asyncio.Event()





async def server_run(quit_event: asyncio.Event, command_queue: asyncio.Queue, download_queue: asyncio.Queue):
    tasks = set()
    while not quit_event.is_set():
        get_cmd = asyncio.create_task(command_queue.get())
        get_download = asyncio.create_task(download_queue.get())

        try:
            done, pending = await asyncio.wait(
                {get_cmd, get_download},
                return_when=asyncio.FIRST_COMPLETED
            )

            for t in pending:
                t.cancel()

            for t in done:
                if t is get_cmd:
                    line = t.result()
                    task = asyncio.create_task(process_commands(line))
                    tasks.add(task)
                    task.add_done_callback(tasks.discard)

                elif t is get_download:
                    download_request = t.result()
                    task = asyncio.create_task(process_downloads(download_request))
                    tasks.add(task)
                    task.add_done_callback(tasks.discard)

        except asyncio.CancelledError:
            print("Server run task cancelled.")
            break

        except Exception as e:
            print(f"Error processing command: {e}")





async def process_commands(line: str):
    global quit_event
    match line:
        case "quit":
            quit_event.set()
            if os.name == "nt":
                os._exit(0)


                try:
                    os.kill(os.getppid(), signal.SIGTERM)
                except Exception:
                    os.kill(os.getpid(), signal.SIGTERM)

                return {"Status": "Server shutting down"}





async def process_downloads(download_request: str):
    global last_download, out_path, ses, identifier
    try:
        if download_request.provider in ("suno", "suno.com"):

            last_download, identifier = Suno.download(session=ses, url=download_request.url, out_path=out_path,  mediatype=download_request.mediatype)
        return last_download, identifier
    except Exception as e:
        print(f"Error processing download: {e}")
        return None, None





@app.get("/")
async def root():
    return {
        "message": "Server startup successful!",
        "last_download": last_download,
        "identifier": identifier
    }





@app.on_event("startup")
async def startup_event():
    #Task

    asyncio.create_task(server_run(quit_event, command_queue, download_queue))







@app.post("/command")
async def receive_command(data: CommandRequest):
    await command_queue.put(data.command)
    return {"message": f"Command received! {data.command}"}





@app.post("/download")
async def receive_download(data: DownloadRequest):
    await download_queue.put(data)
    return {"message": "Download request received!"}





start_time = time.time()

@app.get("/health")
def health():
    uptime_seconds = time.time() - start_time
    return {
        "ok": True,
        "version": app.version,
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_human": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s",
        "queue_sizes": {
            "command_queue": command_queue.qsize(),
            "download_queue": download_queue.qsize()
        },
        "last_download": last_download,
        "last_identifier": identifier,
        "server_shutting_down": quit_event.is_set(),
        "python_version": sys.version,
    }