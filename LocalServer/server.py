import sys, os

from uvicorn import lifespan

from server_backup import connect_db
from datetime import datetime


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fastapi
from PythonModule.models.settings import PROGRESSDICT
from PythonModule.models.responses import (
    MessageResponse,
    CreateResponse,
    CreatePlaylistMediaResponse,
    LoginResponse,
    PlaylistResponse,
    DownloadedMediaResponse,
    SettingsResponse,
    PlaylistMediaResponse,
    UserResponse
)
from PythonModule.models.requests import SearchRequest, DownloadRequest, CommandRequest, CreateUserRequest, CreatePlaylistRequest, CreateDownloadedMediaRequest, CreateSettingsRequest, CreatePlaylistMediaRequest, DeletePlaylistMediaRequest, RegisterRequest, LoginRequest
from PythonModule.serverservices import downloadProcessor, commandProcessor, searchProcessor, utils
from PythonModule.core.request import Session
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import  time, re, json, uuid
from datetime import datetime
import bcrypt

import platform, subprocess

import os
import asyncio
import sqlite3
import secrets

#Global Variables
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_path)
db_path = os.path.join(current_path, "Data", "data.db")
load_dotenv()
ADMIN_KEY = os.getenv("ADMIN_KEY")

log_dir = os.path.join(project_root, "LocalServer", "logs")
log_file = os.path.join(log_dir, "server_runtime.log")
os.makedirs(log_dir, exist_ok=True)

ses = Session.Session()

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

log_queue = asyncio.Queue(maxsize=5000)
quit_event = asyncio.Event()

download_jobs = set()
search_jobs = set()
download_progress = {}


class SearchError(Exception): ...
class CommandError(Exception): ...
class DownloadError(Exception): ...


async def logger(quit_event: asyncio.Event, log_queue: asyncio.Queue):
    global log_file

    while not quit_event.is_set():
        try:
            message = await log_queue.get()

            if not isinstance(message, str):
                message = json.dumps(message, ensure_ascii=False)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{str(timestamp)}] " + message + "\n")

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(e)


download_limiter = asyncio.Semaphore(50)


@app.get("/")
async def root():
    return {
        "message": "Server startup successful!",
    }


#'@app.on_event("startup")
#async def startup_event():
 #   global quit_event, log_queue
#
 #   asyncio.create_task(logger(quit_event, log_queue))
  #  log_queue.put_nowait("[INFO] Server started successfully")
   # create_app_tables()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global quit_event, log_queue
    asyncio.create_task(logger(quit_event, log_queue))
    log_queue.put_nowait("[INFO] Server started successfully")
    create_app_tables()
    yield

app = FastAPI(lifespan=lifespan)

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

        log_queue.put_nowait(f"[INFO] Command '{data.command}' executed successfully")

    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error handling command {data.command}.\nError Message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download")
async def receive_download(data: DownloadRequest):
 
    global log_queue, ses, download_limiter
    task_id = str(uuid.uuid4())
    try:
        ses.reloadCookies()
        utils.validate_url(session=ses, url=data.url)

        download_progress[task_id] = PROGRESSDICT.copy()
        download_progress[task_id]['id'] = task_id


        
    
        task = asyncio.create_task(downloadProcessor.DownloadProcessor(
            downloadRequest=data,
            progressDict=download_progress[task_id],
            session=ses,
            downloadLimiter=download_limiter,
            logQueue=log_queue
            ).run(),
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
        raise HTTPException(status_code=400, detail=f"Invalid type for {str(e)}")

    except Exception as e:
        log_queue.put_nowait(f"[ERROR] failed to create download task with arguments given: provider {data.provider}, url: {data.url}, filepath {data.download_path}.\nError Message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/progress/{task_id}")
async def get_download_progress(task_id: str):
    progress = download_progress.get(task_id)
    if not progress:
        log_queue.put_nowait(f"[ERROR] Tried to access resource /download/progress/{task_id} which doesn't exist")
        raise HTTPException(status_code=404, detail=f"No such ressource /download/progress/{task_id}")
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
        raise HTTPException(status_code=500, detail=str(e))


start_time = time.time()

@app.get("/health")
def health():
    try:
        uptime_seconds = time.time() - start_time
        try:
            mem = self_memory_mb()
        except Exception:
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
        raise HTTPException(status_code=500, detail=str(e))


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
        text=True, encoding="utf-8", errors="replace"
    ).strip()

    if not out:
        return []

    data = json.loads(out)
    if isinstance(data, dict):
        data = [data]

    return [{"pid": int(p["ProcessId"]), "name": p["Name"]} for p in data]


#---------------- DB management ------------------------

def create_app_tables():
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS Users (
                        Identifier TEXT NOT NULL PRIMARY KEY,
                        Username TEXT NOT NULL UNIQUE,
                        PasswordHash TEXT NOT NULL,
                        CreatedAt TEXT NOT NULL,
                        LoggedIn BOOLEAN NOT NULL,
                        LastLoggedIn TEXT NOT NULL)""")

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS DownloadedMedias
                   (
                       Identifier TEXT NOT NULL PRIMARY KEY,
                       UserIdentifier TEXT NOT NULL,
                       Url TEXT,
                       Title TEXT NOT NULL,
                       MediaType TEXT NOT NULL,
                       DownloadedAt TEXT,
                       DownloadPath TEXT NOT NULL UNIQUE,
                       IsPlayable BOOLEAN NOT NULL,
                       FOREIGN KEY (UserIdentifier) REFERENCES Users (Identifier) ON DELETE CASCADE
                   )""")

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS Playlists
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
                       UserIdentifier TEXT NOT NULL UNIQUE,
                       DownloadPath TEXT NOT NULL,
                       DarkModeEnabled BOOLEAN NOT NULL,
                       ScanFolderOnStartup BOOLEAN NOT NULL,
                       FOREIGN KEY (UserIdentifier) REFERENCES Users (Identifier) ON DELETE CASCADE
                   )""")

    conn.commit()
    conn.close()

def connect_db():
    conn = sqlite3.connect(db_path, timeout=20.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn

class PlaylistModel(BaseModel):
    Identifier: str
    Name: str
    Description: Optional[str] = None

class MediaModel(BaseModel):
    Identifier: str
    Url: str
    MediaType: str
    DownloadedAt: str
    DownloadPath: str
    IsPlayable: bool
    Title: str

class PlaylistMediaModel(BaseModel):
    PlaylistIdentifier: str
    MediaIdentifier: str
    Position: int

class SettingsModel(BaseModel):
    Identifier: str
    DownloadPath: str
    DarkModeEnabled: bool
    ScanFolderOnStartup: bool

class SaveUserDataRequest(BaseModel):
    user_identifier: str
    playlists: List[PlaylistModel]
    medias: List[MediaModel]
    playlist_medias: List[PlaylistMediaModel]
    setting: SettingsModel


def save_user_data(request: SaveUserDataRequest):
    user_identifier = request.user_identifier
    playlists = request.playlists
    medias = request.medias
    playlist_medias = request.playlist_medias
    setting = request.setting

    conn = connect_db()
    cursor = conn.cursor()

    try:
        for media in medias:
            cursor.execute(
                """INSERT INTO DownloadedMedias 
                   (Identifier, UserIdentifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable, Title)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(Identifier) DO UPDATE SET
                   Url = excluded.Url,
                   MediaType = excluded.MediaType,
                   DownloadedAt = excluded.DownloadedAt,
                   DownloadPath = excluded.DownloadPath,
                   IsPlayable = excluded.IsPlayable,
                   Title = excluded.Title""",
                (media.Identifier, user_identifier, media.Url, media.MediaType,
                 media.DownloadedAt, media.DownloadPath, media.IsPlayable, media.Title)
            )

        for playlist in playlists:
            cursor.execute(
                """INSERT INTO Playlists (Identifier, UserIdentifier, Name, Description)
                   VALUES (?, ?, ?, ?) ON CONFLICT(Identifier) DO
                UPDATE SET
                    Name = excluded.Name,
                    Description = excluded.Description""",
                (playlist.Identifier, user_identifier, playlist.Name, playlist.Description)
            )

        for playlist_media in playlist_medias:
            cursor.execute(
                """INSERT INTO PlaylistMedias (PlaylistIdentifier, MediaIdentifier, Position)
                   VALUES (?, ?, ?) ON CONFLICT(PlaylistIdentifier, MediaIdentifier) DO
                UPDATE SET
                    Position = excluded.Position""",
                (playlist_media.PlaylistIdentifier, playlist_media.MediaIdentifier, playlist_media.Position)
            )

        cursor.execute(
            """INSERT INTO Settings
               (Identifier, UserIdentifier, DownloadPath, DarkModeEnabled, ScanFolderOnStartup)
               VALUES (?, ?, ?, ?, ?) ON CONFLICT(Identifier) DO
            UPDATE SET
                DownloadPath = excluded.DownloadPath,
                DarkModeEnabled = excluded.DarkModeEnabled,
                ScanFolderOnStartup = excluded.ScanFolderOnStartup""",
            (setting.Identifier, user_identifier, setting.DownloadPath,
             setting.DarkModeEnabled, setting.ScanFolderOnStartup)
        )

        conn.commit()
        conn.close()
    except Exception as e:
        raise fastapi.HTTPException(status_code=400, detail=str(e))

@app.post("/save")
async def handle_save_user_data(req: SaveUserDataRequest):

    # Validiere user_identifier
    if not req.user_identifier or len(req.user_identifier) > 100:
        raise fastapi.HTTPException(status_code=400, detail="Invalid user identifier")

    # Validiere Größen (DoS Prevention)
    if len(req.playlists) > 1000:
        raise fastapi.HTTPException(status_code=400, detail="Too many playlists")

    if len(req.medias) > 10000:
        raise fastapi.HTTPException(status_code=400, detail="Too many medias")

    try:
        save_user_data(req)
        log_queue.put_nowait(f"[INFO] User data for '{req.user_identifier}' saved successfully")
        return {"message": "User data saved successfully"}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error saving user data for '{req.user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))

# ---------------- User Endpoints ----------------

def create_user(username: str, password: str, identifier: str, created_at: str):
    conn = connect_db()
    cursor = conn.cursor()

    date = datetime.now()
    formatted = date.isoformat()

    cursor.execute("""INSERT INTO Users (Username, PasswordHash, Identifier, CreatedAt, LoggedIn, LastLoggedIn) VALUES (?, ?, ?, ?, ?, ?)""", (username, password, identifier, created_at, False, formatted))
    conn.commit()
    conn.close()


@app.post("/set/user/loggedIn/{key}")
async def handle_set_logged_in(key: str, identifier: str = Query(...)):
    try:
        if key != ADMIN_KEY:
            raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""SELECT LoggedIn FROM Users WHERE Identifier = ?""", (identifier,))
        logged_in = cursor.fetchone()[0]

        if logged_in is None:
            log_queue.put_nowait(f"[ERROR] User with identifier '{identifier}' not found")
            raise fastapi.HTTPException(status_code=404, detail=f"User with identifier '{identifier}' not found")

        if logged_in:
            cursor.execute("""UPDATE Users SET LoggedIn = 0 WHERE Identifier = ?""", (identifier,))
            conn.commit()
        else:
            cursor.execute("""UPDATE Users SET LoggedIn = 1 WHERE Identifier = ?""", (identifier,))
            conn.commit()

    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error setting user logged-in status for '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.post("/set/user/lastLoggedIn/{key}")
async def handle_set_last_logged_in(key: str, identifier: str = Query(None)):
    try:
        if key != ADMIN_KEY:
            raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

        conn = connect_db()
        cursor = conn.cursor()
        date = datetime.now()
        formatted = date.isoformat()

        cursor.execute("""SELECT Username FROM Users WHERE Identifier = ?""", (identifier,))
        username = cursor.fetchone()

        if username is None:
            log_queue.put_nowait(f"[ERROR] User with identifier '{identifier}' not found")
            raise fastapi.HTTPException(status_code=404, detail=f"User with identifier '{identifier}' not found")

        cursor.execute("""UPDATE Users SET LastLoggedIn = ? WHERE Identifier = ?""", (formatted, identifier))

        conn.commit()
        conn.close()
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error setting user last logged-in status for '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/get/user/{identifier}", response_model=UserResponse)
async def get_users(identifier: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, Username, CreatedAt FROM Users WHERE Identifier = ?", (identifier,))
        row = cursor.fetchone()

        if row is None:
            cursor.execute("SELECT Identifier, Username, CreatedAt FROM Users WHERE Username = ?", (identifier,))
            row = cursor.fetchone()

            if row is None:
                conn.close()
                log_queue.put_nowait(f"[ERROR] User lookup failed for identifier/username '{identifier}'")
                raise fastapi.HTTPException(status_code=404, detail="User not found")

        conn.close()
        log_queue.put_nowait(f"[INFO] User '{identifier}' retrieved successfully")
        return dict(row)
    except fastapi.HTTPException:
        raise
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving user '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/getall/users/{key}", response_model=List[UserResponse])
async def get_all_users(key: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, Username, CreatedAt FROM Users")
        rows = cursor.fetchall()
        conn.close()

        log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} users")
        return [dict(row) for row in rows]
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving all users: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.post("/create-tables/{key}", response_model=MessageResponse)
async def create_table(key: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        create_app_tables()
        log_queue.put_nowait("[INFO] Tables created successfully")
        return {"message": "Tables created successfully"}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error creating tables: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.post("/create/user/{key}", response_model=CreateResponse)
async def handle_create_user_req(key: str, req: CreateUserRequest):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        identifier = str(uuid.uuid4())
        username = req.username
        password = req.password
        created_at = datetime.now().isoformat()

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        create_user(username, password_hash, identifier, created_at)

        log_queue.put_nowait(f"[INFO] User '{username}' created successfully with id {identifier}")
        return {"message": "User created successfully", "identifier": identifier}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error creating user '{req.username}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@app.post("/delete/user/{key}", response_model=MessageResponse)
async def handle_delete_user_req(key: str, identifier: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""DELETE FROM Users WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] User '{identifier}' deleted successfully")
        return {"message": "User deleted successfully"}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error deleting user '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ---------------- Playlist Endpoints ----------------

@app.get("/get/playlists/{identifier}", response_model=List[PlaylistResponse])
async def get_playlists(identifier: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, Name, Description FROM Playlists WHERE Identifier = ?", (identifier,))
        rows = cursor.fetchall()
        conn.close()

        log_queue.put_nowait(f"[INFO] Retrieved playlist(s) for identifier '{identifier}'")
        return [dict(row) for row in rows]
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving playlists for '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.post("/create/playlist/{key}", response_model=CreateResponse)
async def handle_create_playlist_req(key: str, req: CreatePlaylistRequest):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        identifier = str(uuid.uuid4())

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""INSERT INTO Playlists (Identifier, UserIdentifier, Name, Description) VALUES (?, ?, ?, ?)""", (identifier, req.user_identifier, req.name, req.description))
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] Playlist '{req.name}' created successfully with id {identifier}")
        return {"message": "Playlist created successfully", "identifier": identifier}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error creating playlist '{req.name}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@app.post("/delete/playlist/{key}", response_model=MessageResponse)
async def handle_delete_playlist_req(key: str, identifier: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""DELETE FROM Playlists WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] Playlist '{identifier}' deleted successfully")
        return {"message": "Playlist deleted successfully"}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error deleting playlist '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/getall/playlists/{key}", response_model=List[PlaylistResponse])
async def get_all_playlists(key: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, Name, Description FROM Playlists")
        rows = cursor.fetchall()
        conn.close()

        log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} playlists")
        return [dict(row) for row in rows]
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving all playlists: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ---------------- DownloadedMedia Endpoints ----------------

@app.post("/create/downloadedmedia/{key}", response_model=CreateResponse)
async def handle_create_downloaded_media_req(key: str, req: CreateDownloadedMediaRequest):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        identifier = str(uuid.uuid4())

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO DownloadedMedias (Identifier, UserIdentifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable, Title) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (identifier, req.user_identifier, req.url, req.mediatype, req.downloaded_at, req.download_path, req.is_playable, req.title)
        )
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] Downloaded media '{req.title}' created successfully with id {identifier}")
        return {"message": "Downloaded media created successfully", "identifier": identifier}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error creating downloaded media '{req.title}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@app.post("/delete/downloadedmedia/{key}", response_model=MessageResponse)
async def handle_delete_downloaded_media_req(key: str, identifier: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""DELETE FROM DownloadedMedias WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] Downloaded media '{identifier}' deleted successfully")
        return {"message": "Downloaded media deleted successfully"}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error deleting downloaded media '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/get/downloadedmedia/{identifier}", response_model=DownloadedMediaResponse)
async def get_downloaded_media(identifier: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable, Title FROM DownloadedMedias WHERE Identifier = ?", (identifier,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            log_queue.put_nowait(f"[ERROR] Downloaded media '{identifier}' not found")
            raise fastapi.HTTPException(status_code=404, detail="Downloaded media not found")

        log_queue.put_nowait(f"[INFO] Downloaded media '{identifier}' retrieved successfully")
        return dict(row)
    except fastapi.HTTPException:
        raise
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving downloaded media '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/getall/downloadedmedias/{key}", response_model=List[DownloadedMediaResponse])
async def get_all_downloaded_media(key: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable, Title FROM DownloadedMedias")
        rows = cursor.fetchall()
        conn.close()

        log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} downloaded medias")
        return [dict(row) for row in rows]
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving all downloaded medias: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/getuser/downloadedmedias/{user_identifier}", response_model=List[DownloadedMediaResponse])
async def get_user_downloaded_medias(user_identifier: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, Title, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable FROM DownloadedMedias WHERE UserIdentifier = ?", (user_identifier,))
        rows = cursor.fetchall()
        conn.close()

        log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} downloaded medias for user '{user_identifier}'")
        return [dict(row) for row in rows]
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving downloaded medias for user '{user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ---------------- Settings Endpoints ----------------

@app.post("/create/settings/{key}", response_model=CreateResponse)
async def handle_create_setting_req(key: str, req: CreateSettingsRequest):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        identifier = str(uuid.uuid4())

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO Settings (Identifier, UserIdentifier, DownloadPath, DarkModeEnabled, ScanFolderOnStartup) VALUES (?, ?, ?, ?, ?)""",
            (identifier, req.user_identifier, req.default_download_path, req.dark_mode_enabled, req.scan_folder_on_startup)
        )
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] Settings created successfully for user '{req.user_identifier}' with id {identifier}")
        return {"message": "Setting created successfully", "identifier": identifier}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error creating settings for user '{req.user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@app.post("/delete/settings/{key}", response_model=MessageResponse)
async def handle_delete_setting_req(key: str, identifier: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""DELETE FROM Settings WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] Settings '{identifier}' deleted successfully")
        return {"message": "Setting deleted successfully"}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error deleting settings '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/get/settings/{user_identifier}", response_model=SettingsResponse)
async def get_setting(user_identifier: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, DownloadPath, DarkModeEnabled, ScanFolderOnStartup FROM Settings WHERE UserIdentifier = ?", (user_identifier,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            log_queue.put_nowait(f"[INFO] No settings found for user '{user_identifier}' (expected for new users)")
            raise fastapi.HTTPException(status_code=404, detail="Setting not found")

        log_queue.put_nowait(f"[INFO] Settings retrieved for user '{user_identifier}'")
        return dict(row)
    except fastapi.HTTPException:
        raise
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving settings for user '{user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/getall/settings/{key}", response_model=List[SettingsResponse])
async def get_all_settings(key: str):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, DownloadPath, DarkModeEnabled, ScanFolderOnStartup FROM Settings")
        rows = cursor.fetchall()
        conn.close()

        log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} settings entries")
        return [dict(row) for row in rows]
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving all settings: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ---------------- PlaylistMedia Endpoints ----------------

@app.post("/create/playlistmedia/{key}", response_model=CreatePlaylistMediaResponse)
async def handle_create_playlist_media_req(key: str, req: CreatePlaylistMediaRequest):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM PlaylistMedias WHERE PlaylistIdentifier = ? AND MediaIdentifier = ?", (req.playlist_identifier, req.media_identifier))
        count = cursor.fetchone()[0]

        if count > 0:
            conn.close()
            log_queue.put_nowait(f"[ERROR] Media '{req.media_identifier}' already exists in playlist '{req.playlist_identifier}'")
            raise fastapi.HTTPException(status_code=400, detail="Media already exists in the playlist")

        cursor.execute("SELECT MAX(Position) FROM PlaylistMedias WHERE PlaylistIdentifier = ?", (req.playlist_identifier,))
        max_position_row = cursor.fetchone()
        max_position = max_position_row[0] if max_position_row[0] is not None else 0
        new_position = max_position + 1

        cursor.execute("""INSERT INTO PlaylistMedias (PlaylistIdentifier, MediaIdentifier, Position) VALUES (?, ?, ?)""", (req.playlist_identifier, req.media_identifier, new_position))
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] Media '{req.media_identifier}' added to playlist '{req.playlist_identifier}' at position {new_position}")
        return {"message": "Media added to playlist successfully", "position": new_position}
    except fastapi.HTTPException:
        raise
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error adding media '{req.media_identifier}' to playlist '{req.playlist_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@app.post("/delete/playlistmedia/{key}", response_model=MessageResponse)
async def handle_delete_playlist_media_req(key: str, req: DeletePlaylistMediaRequest):
    if key != ADMIN_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM PlaylistMedias WHERE PlaylistIdentifier = ? AND MediaIdentifier = ?", (req.playlist_identifier, req.media_identifier))
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] Media '{req.media_identifier}' removed from playlist '{req.playlist_identifier}'")
        return {"message": "Media removed from playlist successfully"}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error removing media '{req.media_identifier}' from playlist '{req.playlist_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/get/playlistmedias/{playlist_identifier}", response_model=List[PlaylistMediaResponse])
async def get_playlist_medias(playlist_identifier: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT PlaylistIdentifier, MediaIdentifier, Position FROM PlaylistMedias WHERE PlaylistIdentifier = ? ORDER BY Position", (playlist_identifier,))
        rows = cursor.fetchall()
        conn.close()

        log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} media entries for playlist '{playlist_identifier}'")
        return [dict(row) for row in rows]
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving media for playlist '{playlist_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.get("/getuser/playlists/{user_identifier}", response_model=List[PlaylistResponse])
async def get_user_playlists(user_identifier: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, Name, Description FROM Playlists WHERE UserIdentifier = ?", (user_identifier,))
        rows = cursor.fetchall()
        conn.close()

        log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} playlists for user '{user_identifier}'")
        return [dict(row) for row in rows]
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error retrieving playlists for user '{user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ---------------- Login ----------------

@app.post("/login", response_model=LoginResponse)
async def handle_login_req(req: LoginRequest):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, PasswordHash FROM Users WHERE Username = ?", (req.username,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            log_queue.put_nowait(f"[ERROR] Login failed: user '{req.username}' not found")
            raise fastapi.HTTPException(status_code=404, detail="User not found")

        identifier, password_hash = row["Identifier"], row["PasswordHash"]

        if not bcrypt.checkpw(req.password.encode("utf-8"), password_hash.encode("utf-8")):
            log_queue.put_nowait(f"[ERROR] Login failed: invalid password for user '{req.username}'")
            raise fastapi.HTTPException(status_code=401, detail="Invalid password")

        log_queue.put_nowait(f"[INFO] User '{req.username}' logged in successfully")
        return {"message": "Login successful", "identifier": identifier}
    except fastapi.HTTPException:
        raise
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error during login for user '{req.username}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.post("/register")
async def handle_register_req(req: RegisterRequest):
    try:

        create_user_req = CreateUserRequest(username=req.username, password=req.password)
        response = await handle_create_user_req(ADMIN_KEY, create_user_req)

        if response:
            log_queue.put_nowait(f"[INFO] User '{req.username}' registered successfully")
            return {"message": "User registered successfully", "identifier" : response["identifier"]}
    except fastapi.HTTPException:
        raise
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error during registration for user '{req.username}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.post("/logout/{identifier}")
async def handle_logout_req(identifier: str):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""UPDATE Users SET LoggedIn = 0 WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        log_queue.put_nowait(f"[INFO] User '{identifier}' logged out successfully")
        return {"message": "Logout successful"}
    except Exception as e:
        log_queue.put_nowait(f"[ERROR] Error during logout for user '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))