from fastapi import FastAPI
from pydantic import BaseModel  

import os, signal
import asyncio

#Module imports
import Session, Suno

class CommandRequest(BaseModel):
    command: str
class DownloadRequest(BaseModel):
    provider: str
    url: str
    mediatype: str = ".mp3"  # Default to .mp3, can be overridden by client

ses = Session.Session()
app = FastAPI()
#Queues
command_queue = asyncio.Queue()
download_queue = asyncio.Queue()

last_download = None


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





async def process_downloads(url: str, provider: str):
    global last_download
    if provider.lower() in ("suno", "suno.com"):
        
        last_download = Suno.download(session=ses, url=url, mediatype=".mp3")
    return last_download
          




@app.get("/")
async def root():
    return {
        "message": "Server startup successful!",
        "last_download": last_download
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
    await download_queue.put(data.url, data.provider, data.mediatype)
    return {"message": "Download request received!"}





@app.get("/health")
def health():
    return {"ok": True, "version": app.version}
 