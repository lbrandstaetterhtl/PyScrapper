from os import mkdir

import fastapi
from PythonModule.models.settings import PROGRESSDICT
from PythonModule.models.requests import SearchRequest, DownloadRequest, CommandRequest, CreateUserRequest
from PythonModule.serverservices import downloadProcessor, commandProcessor, searchProcessor, utils
from PythonModule import Session
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys, time, re, json, uuid
from datetime import datetime
import bcrypt


import urllib.error, urllib.request
import platform, subprocess

import os
import asyncio
import sqlite3
from contextlib import asynccontextmanager

#Global Variables
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_path)
db_path = os.path.join(current_path, "Data", "data.db")
load_dotenv()
print(repr(os.getenv("ADMIN_KEY")))
ADMIN_KEY = os.getenv("ADMIN_KEY")

#Runtime Logs will be saved under this path
log_dir = os.path.join(project_root, "LocalServer", "logs")
log_file = os.path.join(log_dir, "server_runtime.log")
#Make sure it exists and if it doesn't it will create it
os.makedirs(log_dir, exist_ok=True)


#Session for cookies and stuff which will be used to request ressources
ses = Session.Session()

#The app
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Queues
log_queue = asyncio.Queue(maxsize=5000)


#Events
quit_event = asyncio.Event()

#Sets
download_jobs = set()
search_jobs = set()
download_progress = {}





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

            


                


#Limits the parralel downloads to 50 at a time, change value for more or less downlaods
download_limiter = asyncio.Semaphore(50)
#Starts download from a user

        
        
        





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

    create_app_tables()

    







@app.post("/command")
async def receive_command(data: CommandRequest):
    global log_file, log_queue, quit_event
    try:
    
        await commandProcessor.CommandProcessor(
            command=data.command,
            logFile=log_file,
            logQueue=log_queue,
            quitEvent=quit_event
        ).run()

    except Exception as e:
        log_queue.put_nowait([f"[ERROR] Error handling command {data.command}.\nError Message: {str(e)}"])
        raise HTTPException(status_code=500, detail=str(e))





@app.post("/download")
async def receive_download(data: DownloadRequest):
    global log_queue, ses, download_limiter
    task_id = str(uuid.uuid4())
    try:
        
        utils.validate_url(session=ses, url=data.url)
        
        

        download_progress[task_id] = PROGRESSDICT.copy()
        download_progress[task_id]['id'] = task_id

        task = asyncio.create_task(downloadProcessor.DownloadProcessor(
            downloadRequest=data,
            progressDict=download_progress[task_id],
            session=ses,
            downloadLimiter=download_limiter,
            logQueue=log_queue
            ).run()
            ,
            name=task_id)
        
        def done(t: asyncio.Task):
            download_jobs.discard(t)
            asyncio.create_task(utils.cleanup_progress(
                download_progess=download_progress,
                task_id=task_id,
                delay=60
            ))

        task.add_done_callback(done)
        download_jobs.add(task)


        log_queue.put_nowait(f"[INFO] Created download task with id {task_id} for provider {data.provider} with url {data.url}")
        return {"id": task_id, "message": f"Request received for download, you can view progress under /download/progress/{task_id}"}
        
    
    except (ValueError, TypeError) as e:
        log_queue.put_nowait(f"[ERROR] failed to create download task with arguments given: provider {data.provider}, url: {data.url}, filepath {data.download_path}.\nError Message: Invalid type for {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type for {str(e)}"
        )
        

    except Exception as e:
        log_queue.put_nowait(f"[ERROR] failed to create download task with arguments given: provider {data.provider}, url: {data.url}, filepath {data.download_path}.\nError Message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )




@app.get("/download/progress/{task_id}")
async def get_download_progress(task_id: str):
    progress = download_progress.get(task_id)
    if not progress:
        log_queue.put_nowait(f"[ERROR] Tried to access resource /download/progress/{task_id} which doesn't exist")

        raise HTTPException(
            status_code=404,
            detail=f"No such ressource /download/progress/{task_id}"
        )
    return progress







@app.post("/search")

async def receive_search(data: SearchRequest):
    global ses
    search_id = str(uuid.uuid4())
    try:
        
        response = await searchProcessor.SearchProcessor(
            searchRequest=data,
            session=ses,
            ).run()
        

        log_queue.put_nowait(f"[INFO] Search succesfull for job {search_id} with query {data.search} and provider {data.provider}")
        return response
    
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Failed search task with given arguments: id {search_id} provider {data.provider} and searchinput {data.search}.\n Error Message:{str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )











start_time = time.time()

@app.get("/health")
def health():
    try:
        uptime_seconds = time.time() - start_time
        try:
            mem = self_memory_mb()
        except Exception as e:
            mem = None
        
        active_downloads = [v for v in download_progress.values() if v["status"] not in ("complete", "error")]

        downloads_with_errors = [v for v in download_progress.values() if v["status"] == "error"]
    
        error_messages = [v["errorMessage"] for v in downloads_with_errors if v["errorMessage"]]
    
        return {
            "ok": True,
            "uptime_seconds": round(uptime_seconds, 2),
            "memory_mb": mem,
            "pid": os.getpid(),
            "processes": list_python_processes(),
            "active_downloads": active_downloads,
            "error_messages": error_messages
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

def self_memory_mb():
    pid = os.getpid()
    try:
        if platform.system() == "Windows":
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
                text=True, errors="replace"
            )
            line = out.splitlines()[1]
            mem = line.split(",")[-1]
            digits = re.sub(r"\D", "", mem)
            if not digits:
                return None
            return round(int(digits) / 1024, 2)
        else:
            # Linux: /proc/{pid}/status auslesen
            with open(f"/proc/{pid}/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        kb = int(line.split()[1])
                        return round(kb / 1024, 2)
            return None
    except Exception:
        return None

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

#db management

def create_app_tables():

    if not os.path.exists(db_path):
        mkdir(os.path.dirname(db_path))

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS Users (
                                                        Identifier TEXT NOT NULL PRIMARY KEY,
                                                        Username TEXT NOT NULL,
                                                        PasswordHash TEXT NOT NULL,
                                                        CreatedAt TEXT NOT NULL)""")

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS DownloadedMedias
                   (
                       Identifier TEXT NOT NULL PRIMARY KEY,
                       UserIdentifier TEXT NOT NULL,
                       Url TEXT,
                       MediaType TEXT NOT NULL,
                       DownloadedAt Text,
                       DownloadPath TEXT NOT NULL,
                       IsPlayable BOOLEAN NOT NULL,
                       FOREIGN KEY (UserIdentifier) REFERENCES Users (Identifier) ON DELETE CASCADE
                   )""")

    cursor.execute("""
                   Create table IF NOT EXISTS Playlists
                   (
                       Identifier TEXT NOT NULL PRIMARY KEY,
                       UserIdentifier TEXT NOT NULL,
                       Name TEXT NOT NULL,
                       Description TEXT,
                       FOREIGN KEY (UserIdentifier) REFERENCES Users (Identifier) ON DELETE CASCADE
                   )""")

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS PlaylistMedias
                   (
                       PlaylistIdentifier TEXT NOT NULL,
                       MediaIdentifier TEXT NOT NULL,
                       Position INTEGER NOT NULL,
                       PRIMARY KEY (PlaylistIdentifier, MediaIdentifier),
                       FOREIGN KEY (PlaylistIdentifier) REFERENCES Playlists (Identifier) ON DELETE CASCADE,
                       FOREIGN KEY (MediaIdentifier) REFERENCES DownloadedMedias (Identifier) ON DELETE CASCADE
                   )""")

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS Settings
                   (
                       Identifier TEXT NOT NULL PRIMARY KEY,
                       UserIdentifier TEXT NOT NULL,
                       DefaultDownloadPath TEXT NOT NULL,
                       DarkModeEnabled BOOLEAN NOT NULL,
                       ScanFolderOnStartup BOOLEAN NOT NULL,
                       FOREIGN KEY (UserIdentifier) REFERENCES Users (Identifier) ON DELETE CASCADE
                   )""")

    conn.commit()
    conn.close()

def create_user(username: str, password: str, identifier: str, created_at: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""INSERT INTO Users (Username, PasswordHash, Identifier, CreatedAt) VALUES (?, ?, ?, ?)""", (username, password, identifier, created_at))
    conn.commit()
    conn.close()

def connect_db():
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/users/{identifier}")
async def get_users(identifier: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT Identifier, Username, CreatedAt FROM Users WHERE Identifier = ?", (identifier,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise fastapi.HTTPException(status_code=404, detail="User not found")

    return dict(row)

@app.post("/create-tables/{key}")
async def create_table(key: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")
    create_app_tables()

@app.post("/create/user/{key}")
async def handle_create_user_req(key: str, req: CreateUserRequest):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    identifier = str(uuid.uuid4())
    username = req.username
    password = req.password
    created_at = datetime.now().isoformat()

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    create_user(username, password_hash, identifier, created_at)