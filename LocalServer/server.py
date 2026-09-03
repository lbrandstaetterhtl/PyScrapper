# Python Default Imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import platform, subprocess
import time, re, json, uuid

from dataclasses import dataclass, field

print("DISPLAY:", os.environ.get("DISPLAY"))

import asyncio
import sqlite3
import secrets
from typing import Optional, List

# Python Pip Imports
from uvicorn import lifespan

from fastapi.security import APIKeyHeader

import fastapi
from dotenv import load_dotenv
import bcrypt
from fastapi import FastAPI, HTTPException, Query, Depends, Security, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi.responses import StreamingResponse

# PythonModule imports

from PythonModule.models.requests import SaveUserDataRequest
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

from PythonModule.models import requests as requests
from PythonModule.models import responses as responses
from PythonModule.models import settings

import PythonModule.core as core
from PythonModule.core.network import file, html

import PythonModule.providers.models as providermodels
from PythonModule.core.network.Session import Session

from PythonModule.serverservices import commandProcessor, searchProcessor, utils

from contextlib import asynccontextmanager

import hashlib

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


@dataclass
class ServerStream:
    stream_id: str
    context: core.models.Download.DownloadContext

    segments: list | None = None
    audio_segments: list | None = None


@dataclass
class ServerJob:
    job_id: str

    download_information: core.models.Download.DownloadInformation

    creation_timestamp: float

    stream_jobs: dict[str, ServerStream] = field(default_factory=dict)


@dataclass
class ServerState:
    jobs: dict[str, ServerJob] = field(default_factory=dict)

    log_queue: asyncio.Queue = field(
        default_factory=lambda: asyncio.Queue(maxsize=5000)
    )

    quit_event: asyncio.Event = field(
        default_factory=lambda: asyncio.Event()
    )

    download_limiter: asyncio.Semaphore = field(
        default_factory=lambda: asyncio.Semaphore(10)
    )

    search_limiter: asyncio.Semaphore = field(
        default_factory=lambda: asyncio.Semaphore(10)
    )

    download_path: str = field(
        default_factory=lambda: os.path.dirname(__file__)
    )


# Global Variables
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_path)
db_path = os.path.join(current_path, "Data", "data.db")

env_path = os.path.join(current_path, ".env")
load_dotenv(dotenv_path=env_path)

ADMIN_KEY = os.getenv("ADMIN_KEY")

log_dir = os.path.join(project_root, "LocalServer", "logs")
log_file = os.path.join(log_dir, "server_runtime.log")

cookie_path = os.path.join(project_root, "LocalServer", "cookies")

os.makedirs(cookie_path, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)
user_key_header = APIKeyHeader(name="X-User-Key", auto_error=False)
auth_header = APIKeyHeader(name="Auth", auto_error=False)


def require_admin(key: str | None = Security(admin_key_header)) -> bool:
    """Client-Key aus der .env. Schuetzt den Server als Ganzes."""
    if not key or not secrets.compare_digest(key, ADMIN_KEY):
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")
    return True


def require_user(request: Request, key: str | None = Security(user_key_header),
                 auth: str | None = Security(auth_header)):
    """Authentifiziert einen User ueber Identifier + API-Key.

    In der Datenbank liegt ausschliesslich SHA-256(ApiKey). Der vom Client
    gesendete Klartext-Key wird fuer die aktuelle Anfrage gehasht und dieser
    Hash wird constant-time mit dem gespeicherten Hash verglichen.

    Der Klartext-Key wird NICHT gespeichert. Er wird nur im Rueckgabeobjekt
    dieser Dependency fuer die Lebensdauer der aktuellen Anfrage mitgefuehrt,
    damit /get/user ihn bei Bedarf an denselben Client zurueckgeben kann.
    """
    if not key or not key.strip():
        raise fastapi.HTTPException(status_code=401, detail="Missing X-User-Key")

    if not auth or not auth.strip():
        raise fastapi.HTTPException(status_code=401, detail="Missing Auth header")

    request_api_key = key.strip()
    auth_identifier = auth.strip()
    request_api_key_hash = hash_api_key(request_api_key)

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT Identifier, Username, CreatedAt, ApiKey FROM Users WHERE Identifier = ?",
        (auth_identifier,)
    )
    row = cursor.fetchone()
    conn.close()

    # Absichtlich fuer unbekannten Identifier und falschen Key dieselbe Antwort,
    # damit man gueltige Identifier nicht ueber die Fehlermeldung enumerieren kann.
    if row is None:
        server_state.log_queue.put_nowait(
            f"[WARN] Invalid user authentication for identifier '{auth_identifier}'"
        )
        raise fastapi.HTTPException(status_code=401, detail="Invalid user key")

    if not secrets.compare_digest(request_api_key, row["ApiKey"]):
        server_state.log_queue.put_nowait(
            f"[WARN] Invalid user authentication for identifier '{auth_identifier}'"
        )
        raise fastapi.HTTPException(status_code=401, detail="Invalid user key")

    # sqlite3.Row erweitern wir nicht direkt, daher ein normales dict.
    # _PlainApiKey existiert nur fuer diese eine Request-Verarbeitung.
    authenticated_user = dict(row)
    authenticated_user["_PlainApiKey"] = request_api_key
    return authenticated_user


def require_auth(auth: str | None = Security(auth_header)) -> str:
    """User-Identifier aus dem Auth-Header.

    Prueft nur, dass der Header da ist. Ob er zum angefragten Datensatz passt,
    entscheidet check_user_identifier im jeweiligen Endpoint.
    """
    if not auth or not auth.strip():
        raise fastapi.HTTPException(status_code=401, detail="Missing Auth header")
    return auth.strip()


def check_user_identifier(user, auth_identifier: str) -> bool:
    """Vergleicht den Identifier aus dem Auth-Header mit dem des Datensatzes."""
    if user is None or not auth_identifier:
        return False
    return user["Identifier"] == auth_identifier


def check_owner(owner_identifier: str | None, auth_identifier: str) -> bool:
    """Wie check_user_identifier, aber fuer Datensaetze mit UserIdentifier-Spalte."""
    if not owner_identifier or not auth_identifier:
        return False
    return owner_identifier == auth_identifier


# Tabellen, in denen eine Besitzpruefung ueber UserIdentifier erlaubt ist.
# Dient als Allowlist, damit der Tabellenname nie ungeprueft ins SQL geht.
OWNED_TABLES = ("DownloadedMedias", "Settings", "Playlists")


def owns_record(table: str, identifier: str, auth_identifier: str) -> bool:
    """Prueft, ob ein Datensatz dem Aufrufer gehoert.

    Gibt False zurueck, wenn es den Datensatz nicht gibt - der Aufrufer
    erfaehrt dadurch nicht, ob ein fremder Identifier existiert.
    """
    if table not in OWNED_TABLES:
        raise ValueError(f"Unsupported table for ownership check: {table}")

    if not identifier or not auth_identifier:
        return False

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT UserIdentifier FROM {table} WHERE Identifier = ?", (identifier,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return False

    return check_owner(row["UserIdentifier"], auth_identifier)


def owns_playlist(playlist_identifier: str, auth_identifier: str) -> bool:
    """Prueft, ob eine Playlist dem Aufrufer gehoert."""
    return owns_record("Playlists", playlist_identifier, auth_identifier)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger_task = asyncio.create_task(
        logger(server_state.quit_event, server_state.log_queue)
    )

    cleanup_task = asyncio.create_task(
        cleanup_loop()
    )

    server_state.log_queue.put_nowait("[INFO] Server started successfully")

    create_app_tables()
    yield
    cleanup_task.cancel()
    logger_task.cancel()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

server_state = ServerState(
    download_path=os.path.join(project_root, "downloads")
)


# "http://localhost:5173",
#       "http://127.0.0.1:5173"


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


@app.get("/")
async def root():
    return {
        "message": "Server startup successful!",
    }


# '@app.on_event("startup")
# async def startup_event():
#   global quit_event, log_queue
#
#   asyncio.create_task(logger(quit_event, log_queue))
#  log_queue.put_nowait("[INFO] Server started successfully")
# create_app_tables()

async def cleanup_server(CLEANUP_AFTER_SECONDS):
    now = time.monotonic()

    for job_id, job in list(server_state.jobs.items()):
        if now - job.creation_timestamp > CLEANUP_AFTER_SECONDS:
            server_state.jobs.pop(job_id, None)

    server_state.log_queue.put_nowait("[INFO] ended server cleanup!")


async def cleanup_download(
        delay: float,
        *,
        task_id: str,
        stream_id: str | None = None
):
    await asyncio.sleep(delay)

    job = server_state.jobs.get(task_id)

    if job is None: return

    if stream_id is None:
        server_state.jobs.pop(task_id, None)
        return

    job.stream_jobs.pop(stream_id, None)

    job.download_information.contexts = [
        context for context in job.download_information.contexts
        if context.context_id != stream_id
    ]

    if (
            not job.stream_jobs
            and not job.download_information.contexts
    ):
        server_state.jobs.pop(task_id, None)


async def cleanup_loop():
    try:
        CHECK_INTERVAL = 60 * 10
        JOB_AGE_LIMIT = 24 * 60 * 60

        while True:
            await cleanup_server(JOB_AGE_LIMIT)
            await asyncio.sleep(CHECK_INTERVAL)

    except asyncio.QueueFull:
        pass


@app.post("/command")
async def receive_command(data: requests.CommandRequest, user=Security(require_user)):
    global log_file
    try:
        await commandProcessor.CommandProcessor(
            command=data.command,
            logFile=log_file,
            logQueue=server_state.log_queue,
            quitEvent=server_state.quit_event
        ).run()

        server_state.log_queue.put_nowait(f"[INFO] Command '{data.command}' executed successfully")

    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error handling command {data.command}.\nError Message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _resolve_provider(request, searchFunc):
    async with server_state.search_limiter:
        result: providermodels.ProviderResult = await asyncio.to_thread(
            searchFunc,
            request
        )
        return result


async def _resolveMediaAndCreateContexts(
        data: requests.DownloadRequest,
        session: Session,
        task_id: str,
):
    searchFunc = _resolveProviderSearchFunction(data.provider)

    contexts: list[core.models.Download.DownloadContext] = []

    tasks = []

    for url, filename in zip(data.urls, data.filenames):
        request = providermodels.ProviderResultRequest(
            url,
            ses=session,
            extra_headers=data.extra_headers,
            preferred_file=data.preferred_file,
            preferred_type=data.preferred_type
        )
        tasks.append(_resolve_provider(request, searchFunc))

    results = await asyncio.gather(*tasks)

    for result, url, filename in zip(
            results,
            data.urls,
            data.filenames
    ):
        result: providermodels.ProviderResult
        target = core.models.Download.DownloadTarget(
            url=url,
            resolved_url=result.url,
            download_type=result.download_type,
            extra_headers=result.extra_headers,
            post_body=result.post_body
        )

        info = core.models.Download.MediaInfo(
            mime_type=result.mime_type,
            file_extension=result.file_ending,
            total_size=result.total_size
        )

        outputTarget = core.models.Download.OutputTarget(
            full_filename=f"{filename}.{result.file_ending}",
            download_path=data.download_path
        )

        context = core.models.Download.DownloadContext(
            context_id=f"{task_id}-{filename}",
            target=target,
            media_info=info,
            output=outputTarget,
            info=result.info,

        )

        contexts.append(context)

    return contexts


def _resolveProviderSearchFunction(provider: str) -> callable:
    providerResolved: settings.ProviderTypes = utils.validateProviders(provider)

    if providerResolved is None:
        raise core.models.errors.TaskFailedError(
            task="/download/video-audio/",
            reason="Invalid provider string was given that couldn't be resolved",
            caller="server/download/video-audio"
        )

    func = settings.PROVIDER_GETRESULTS_MAPPING.get(providerResolved)

    if func is None:
        raise core.models.errors.TaskFailedError(
            task="/download/video-audio/",
            reason=f"Couldn't map provider {providerResolved} to a function",
            caller="server/download/video-audio"
        )

    return func


async def _run_local_download(
        task_id: str,
        downloader: core.download.Dispatcher.DownloadDispatcher,
        convert: bool = False
):
    try:
        await downloader.downloadToFile()
        if convert is True:
            raise ValueError("Converting isn't supported yet")

    except Exception as e:
        server_state.log_queue.put_nowait(
            f"[ERROR] Download job {task_id} failed: {e}"
        )
        raise e


@app.post("/download/video-audio")
async def receive_download(data: requests.DownloadRequest, user=Security(require_user)):
    # Settings and creation
    global server_state
    taskId = str(uuid.uuid4())
    ses = Session()

    try:

        contexts: list[core.models.Download.DownloadContext] = await _resolveMediaAndCreateContexts(data, ses, taskId)

        downloadInformation = core.models.Download.DownloadInformation(
            job_id=taskId,
            session=ses,
            download_limiter=server_state.download_limiter,
            download_strategie=data.download_strategie,
            contexts=contexts,
        )
        job = ServerJob(
            job_id=taskId,
            download_information=downloadInformation,
            creation_timestamp=time.monotonic()
        )
        server_state.jobs[taskId] = job
        resources: list[responses.Resources] = []

        # Depending on the strategy something different will happen
        if data.download_strategie == core.models.Download.DownloadStrategie.LOCAL:
            downloader = core.download.Dispatcher.DownloadDispatcher(downloadInformation)
            asyncio.create_task(
                _run_local_download(
                    taskId,
                    downloader
                )
            )

            for context in downloadInformation.contexts:
                resource = responses.Resources(
                    context=context,
                    progress_url=f"/download/progress/{taskId}/{context.context_id}"
                )
                resources.append(resource)


        elif data.download_strategie == core.models.Download.DownloadStrategie.STREAM:
            for context in downloadInformation.contexts:

                streamJob = ServerStream(
                    stream_id=context.context_id,
                    context=context,
                )

                if context.target.download_type == core.models.Download.DownloadType.HLS:
                    segments, audioSegments = await asyncio.to_thread(
                        _getIndexSegmentsForStreaming,
                        job,
                        streamJob.stream_id,
                        context
                    )
                    watchUrlExtension = "/index.m3u8"
                    streamType = "hls"

                    streamJob.segments = segments
                    streamJob.audio_segments = audioSegments

                # Includes UMP and FILE
                else:
                    watchUrlExtension = f"/{context.output.full_filename}"
                    streamType = "file"

                server_state.jobs[taskId].stream_jobs[streamJob.stream_id] = streamJob

                resource = responses.Resources(
                    context=context,
                    progress_url=f"/download/progress/{taskId}/{context.context_id}",
                    download_url=f"/stream/download/{taskId}/{context.context_id}",
                    watch_url=f"/stream/watch/{taskId}/{context.context_id}{watchUrlExtension}",
                    stream_type=streamType
                )
                resources.append(resource)




        else:
            raise core.models.errors.TaskFailedError(
                task=f"/download/video-audio/",
                reason="Unknown download strategie was given",
                caller="server/download/video-audio"
            )

        return responses.DownloadResponse(
            task_id=taskId,
            resources=resources
        )



    except (ValueError, TypeError, core.models.errors.ArgumentError, core.models.errors.ArgumentErrorCompare) as e:
        server_state.log_queue.put_nowait(f"[ERROR] failed to create download task with given request: {data}")
        raise HTTPException(status_code=400, detail=f"Invalid type for {str(e)}")

    except core.models.errors.TaskFailedError as e:
        server_state.log_queue.put_nowait(f"[ERROR] Failed download. Request: {data}. Message from Resolver: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except core.models.errors.DRMProtectedMediaError as e:
        server_state.log_queue.put_nowait(
            f"[ERROR] DRM protected media. Request: {data}. Error: {str(e)}"
        )

        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Unknown error occured; {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _getIndexSegmentsForStreaming(job: ServerJob, stream_id: str, context: core.models.Download.DownloadContext):
    from PythonModule.core.download.HLS import models as hlsmodels
    segmentList = []

    file = html.getHtml(
        session=job.download_information.session,
        url=context.target.resolved_url,
        extra_headers=context.target.extra_headers
    )

    fileType: hlsmodels.FileType = core.download.HLSDispatcher(job.download_information).dertermineFileType(file)

    if fileType == hlsmodels.FileType.MASTER_FILE:
        masterResults = core.download.MasterHLSDownload(context, job.download_information.session).getUrls()
        indexUrl, audioUrl = masterResults

        context.target.resolved_url = indexUrl
        segmentList, audioSegmentList = core.download.IndexHLSDownload(context,
                                                                       job.download_information.session).getIndexSegmentList()


    elif fileType == hlsmodels.FileType.INDEX_FILE:
        segmentList, audioSegmentList = core.download.IndexHLSDownload(context,
                                                                       job.download_information.session).getIndexSegmentList()

    if not segmentList:
        raise core.models.errors.TaskFailedError(
            task="_getIndexSegmentsForStreaming",
            reason="Didn't get segmentList from index"
        )

    return (segmentList, audioSegmentList)


@app.get("/stream/watch/{task_id}/{stream_id}/index.m3u8",
         dependencies=[Security(require_user)])
async def stream_hls_index(task_id: str, stream_id: str):
    job = server_state.jobs.get(task_id)

    if job is None:
        raise HTTPException(status_code=404)

    stream = job.stream_jobs.get(stream_id)

    if stream is None or not stream.segments:
        raise HTTPException(status_code=404)

    max_duration = max(
        segment.duration
        for segment in stream.segments
    )

    lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3",
        f"#EXT-X-TARGETDURATION:{int(max_duration + 0.999)}",
        "#EXT-X-MEDIA-SEQUENCE:0",
    ]

    for index, segment in enumerate(stream.segments):
        lines.append(f"#EXTINF:{segment.duration:.3f},")
        lines.append(
            f"/stream/watch/{task_id}/{stream_id}/segment/{index}"
        )

    lines.append("#EXT-X-ENDLIST")

    playlist = "\n".join(lines)

    return Response(
        content=playlist,
        media_type="application/vnd.apple.mpegurl"
    )


@app.get("/stream/watch/{task_id}/{stream_id}/segment/{segment_id}",
         dependencies=[Security(require_user)])
async def stream_hls_segment(
        task_id: str,
        stream_id: str,
        segment_id: int
):
    job = server_state.jobs.get(task_id)

    if job is None:
        raise HTTPException(status_code=404)

    stream = job.stream_jobs.get(stream_id)

    if stream is None or not stream.segments:
        raise HTTPException(status_code=404)

    if segment_id < 0 or segment_id >= len(stream.segments):
        raise HTTPException(status_code=404)

    segment = stream.segments[segment_id]

    return StreamingResponse(
        file.asyncDownloadYieldSimple(
            session=job.download_information.session,
            url=segment.url,
            extra_headers=stream.context.target.extra_headers,
        ),
        media_type="video/mp2t"
    )


@app.get("/stream/watch/{task_id}/{stream_id}/{file_name}.{file_type}",
         dependencies=[Security(require_user)])
async def client_watch_stream(task_id: str, stream_id: str, file_name: str, file_type: str, request: Request):
    job = server_state.jobs.get(task_id)

    if job is None:
        raise HTTPException(status_code=404)

    stream_job = job.stream_jobs.get(stream_id)

    if stream_job is None:
        raise HTTPException(status_code=404)

    context: core.models.Download.DownloadContext = stream_job.context

    if context.output.full_filename != f"{file_name}.{file_type}":
        raise HTTPException(status_code=404)

    status_code = 200

    headers = {
        "Accept-Ranges": "bytes"
    }
    total_size = context.media_info.total_size

    range_headers = request.headers.get("range")
    start_byte = 0
    end_byte = None

    if range_headers:
        print("[WATCH] Browser Range: ", range_headers)
        value = range_headers.removeprefix("bytes=")
        start, end = value.split("-", 1)

        if start:
            start_byte = int(start)

        if end:
            end_byte = int(end)
        else:
            end_byte = total_size - 1

        status_code = 206

        headers["Content-Range"] = (
            f"bytes {start_byte}-{end_byte}/{total_size}"
        )

        headers["Content-Length"] = str(
            end_byte - start_byte + 1
        )
    else:
        headers["Content-Length"] = str(total_size)

    print(
        "Serving:",
        start_byte,
        end_byte,
        "/",
        total_size
    )

    if context.target.download_type == core.models.Download.DownloadType.FILE:
        return StreamingResponse(
            file.asyncDownloadYieldSimple(
                session=job.download_information.session,
                url=context.target.resolved_url,
                extra_headers=context.target.extra_headers,
                start_byte=start_byte,
                end_byte=end_byte,
            ),
            status_code=status_code,
            headers=headers,
            media_type=providermodels.EXTENSION_CONTENT_TYPES.get(
                context.media_info.file_extension
            ),
        )

    elif context.target.download_type == core.models.Download.DownloadType.UMP:
        from PythonModule.core.download.UMP import download

        return StreamingResponse(
            download.downloadAndYieldUMPRange(
                session=job.download_information.session,
                start_url=context.target.resolved_url,
                extra_headers=context.target.extra_headers,
                max_len=total_size,
                media_start=start_byte,
                media_end=end_byte,
                post_body=context.target.post_body
            ),
            status_code=status_code,
            headers=headers,
            media_type="audio/webm"
        )


@app.get("/stream/download/{task_id}/{stream_id}",
         dependencies=[Security(require_user)])
async def client_download_stream(task_id: str, stream_id: str):
    job = server_state.jobs.get(task_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ressource /stream/download/{task_id}/{stream_id} doesn't exist"
        )

    streamJob = job.stream_jobs.get(stream_id)
    if streamJob is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ressource /stream/download/{task_id}/{stream_id} doesn't exist"
        )

    context: core.models.Download.DownloadContext = streamJob.context

    downloadInformation = job.download_information
    downloader = core.download.Dispatcher.DownloadDispatcher(downloadInformation)

    async def download_and_cleanup():

        async for chunk in downloader.downloadContextAndYield(context):
            yield chunk

    return StreamingResponse(
        download_and_cleanup(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition":
                f'attachment; filename="{context.output.full_filename if context.output.full_filename is not None else (context.context_id + context.media_info.file_extension)}"'
        }
    )


def _findContext(download_information, context_id):
    for context in download_information.contexts:
        if context.context_id == context_id:
            return context

    return None


@app.get("/download/progress/{task_id}/{context_id}",
         dependencies=[Security(require_user)])
async def get_download_progress(task_id: str, context_id: str):
    job = server_state.jobs.get(task_id)

    if job is None:
        raise HTTPException(status_code=404)

    info: core.models.Download.DownloadInformation = job.download_information

    context = _findContext(info, context_id)
    if context is None:
        raise HTTPException(status_code=404)

    return context.download_progress


@app.post("/search")
async def receive_search(data: requests.SearchRequest, user=Security(require_user)):
    ses = Session()
    search_id = str(uuid.uuid4())
    try:
        response = await searchProcessor.SearchProcessor(
            searchRequest=data,
            session=ses,
        ).run()

        server_state.log_queue.put_nowait(
            f"[INFO] Search successful for job {search_id} with query {data.search} and provider {data.provider}")
        return response

    except Exception as e:
        server_state.log_queue.put_nowait(
            f"[ERROR] Failed search task with given arguments: id {search_id} provider {data.provider} and searching {data.search}.\n Error Message:{str(e)}")
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

        # active_downloads = [v for v in download_progress.values() if v["status"] not in ("complete", "error")]
        # downloads_with_errors = [v for v in download_progress.values() if v["status"] == "error"]
        # error_messages = [v["errorMessage"] for v in downloads_with_errors if v["errorMessage"]]

        return {
            "ok": True,
            "uptime_seconds": round(uptime_seconds, 2),
            "memory_mb": mem,
            "pid": os.getpid(),
            "processes": list_python_processes(),
            # "active_downloads": active_downloads,
            # "error_messages": error_messages
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


# ---------------- DB management ------------------------
# User account definitions (admin, mod, normal)
# API Key field for users
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
                        ApiKey TEXT NOT NULL,
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


def save_user_data(request: SaveUserDataRequest):
    user_identifier = request.user_identifier
    playlists = request.playlists
    medias = request.medias
    playlist_medias = request.playlist_medias
    setting = request.setting

    conn = connect_db()
    cursor = conn.cursor()

    try:
        # ---- 1. Medias upserten ----
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

        # ---- 2. Playlists upserten ----
        for playlist in playlists:
            cursor.execute(
                """INSERT INTO Playlists (Identifier, UserIdentifier, Name, Description)
                   VALUES (?, ?, ?, ?) ON CONFLICT(Identifier) DO
                UPDATE SET
                    Name = excluded.Name,
                    Description = excluded.Description""",
                (playlist.Identifier, user_identifier, playlist.Name, playlist.Description)
            )

        # ---- 3. Verwaiste Medias löschen (die in der DB sind, aber nicht mehr im Request) ----
        # CASCADE entfernt automatisch zugehörige PlaylistMedias-Einträge.
        media_ids = [m.Identifier for m in medias]
        if media_ids:
            placeholders = ",".join("?" for _ in media_ids)
            cursor.execute(
                f"""DELETE FROM DownloadedMedias
                    WHERE UserIdentifier = ?
                      AND Identifier NOT IN ({placeholders})""",
                (user_identifier, *media_ids)
            )
        else:
            # Request enthält gar keine Medias -> alle des Users löschen
            cursor.execute(
                "DELETE FROM DownloadedMedias WHERE UserIdentifier = ?",
                (user_identifier,)
            )

        # ---- 4. Verwaiste Playlists löschen ----
        playlist_ids = [p.Identifier for p in playlists]
        if playlist_ids:
            placeholders = ",".join("?" for _ in playlist_ids)
            cursor.execute(
                f"""DELETE FROM Playlists
                    WHERE UserIdentifier = ?
                      AND Identifier NOT IN ({placeholders})""",
                (user_identifier, *playlist_ids)
            )
        else:
            cursor.execute(
                "DELETE FROM Playlists WHERE UserIdentifier = ?",
                (user_identifier,)
            )

        # ---- 5. PlaylistMedias komplett neu setzen ----
        # Alle PlaylistMedias der (jetzt noch existierenden) Playlists dieses Users löschen...
        cursor.execute(
            """DELETE FROM PlaylistMedias
               WHERE PlaylistIdentifier IN (
                   SELECT Identifier FROM Playlists WHERE UserIdentifier = ?
               )""",
            (user_identifier,)
        )
        # ...und aus dem Request neu einfügen. Nur Einträge, deren Parents wirklich existieren.
        for pm in playlist_medias:
            cursor.execute("SELECT 1 FROM Playlists WHERE Identifier = ?", (pm.PlaylistIdentifier,))
            if cursor.fetchone() is None:
                server_state.log_queue.put_nowait(
                    f"[WARN] Skipping PlaylistMedia, missing Playlist parent: {pm.PlaylistIdentifier}")
                continue

            cursor.execute("SELECT 1 FROM DownloadedMedias WHERE Identifier = ?", (pm.MediaIdentifier,))
            if cursor.fetchone() is None:
                server_state.log_queue.put_nowait(
                    f"[WARN] Skipping PlaylistMedia, missing Media parent: {pm.MediaIdentifier}")
                continue

            cursor.execute(
                """INSERT INTO PlaylistMedias (PlaylistIdentifier, MediaIdentifier, Position)
                   VALUES (?, ?, ?)""",
                (pm.PlaylistIdentifier, pm.MediaIdentifier, pm.Position)
            )

        # ---- 6. Settings upserten ----
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
    except Exception as e:
        conn.rollback()
        raise fastapi.HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.post("/save")
async def handle_save_user_data(req: SaveUserDataRequest, user=Security(require_user)):
    if not check_owner(req.user_identifier, user["Identifier"]):
        server_state.log_queue.put_nowait(
            f"[WARN] Save rejected: user key does not match user_identifier '{req.user_identifier}'")
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

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
        server_state.log_queue.put_nowait(f"[INFO] User data for '{req.user_identifier}' saved successfully")
        return {"message": "User data saved successfully"}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error saving user data for '{req.user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ---------------- User Endpoints ---------------

# ============================================================
# User Endpoints
# ============================================================

# create_user() unverändert – reine DB-Funktion, kein Key.
def create_user(username: str, password: str, identifier: str, created_at: str, apikey_hash: str):
    conn = connect_db()
    cursor = conn.cursor()

    date = datetime.now()
    formatted = date.isoformat()

    cursor.execute("""INSERT INTO Users (Username, PasswordHash, Identifier, CreatedAt, LoggedIn, LastLoggedIn, ApiKey)
                      VALUES (?, ?, ?, ?, ?, ?, ?)""",
                   (username, password, identifier, created_at, False, formatted, apikey_hash))
    conn.commit()
    conn.close()


@app.post("/set/user/loggedIn")
async def handle_set_logged_in(identifier: str = Query(...), user=Security(require_user)):
    if not check_owner(identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""SELECT LoggedIn
                          FROM Users
                          WHERE Identifier = ?""", (identifier,))
        logged_in = cursor.fetchone()[0]

        if logged_in is None:
            server_state.log_queue.put_nowait(f"[ERROR] User with identifier '{identifier}' not found")
            raise fastapi.HTTPException(status_code=404, detail=f"User with identifier '{identifier}' not found")

        if logged_in:
            cursor.execute("""UPDATE Users
                              SET LoggedIn = 0
                              WHERE Identifier = ?""", (identifier,))
            conn.commit()
        else:
            cursor.execute("""UPDATE Users
                              SET LoggedIn = 1
                              WHERE Identifier = ?""", (identifier,))
            conn.commit()

    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error setting user logged-in status for '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.post("/set/user/lastLoggedIn")
async def handle_set_last_logged_in(identifier: str = Query(None), user=Security(require_user)):
    if not check_owner(identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()
        date = datetime.now()
        formatted = date.isoformat()

        cursor.execute("""SELECT Username
                          FROM Users
                          WHERE Identifier = ?""", (identifier,))
        username = cursor.fetchone()

        if username is None:
            server_state.log_queue.put_nowait(f"[ERROR] User with identifier '{identifier}' not found")
            raise fastapi.HTTPException(status_code=404, detail=f"User with identifier '{identifier}' not found")

        cursor.execute("""UPDATE Users
                          SET LastLoggedIn = ?
                          WHERE Identifier = ?""", (formatted, identifier))

        conn.commit()
        conn.close()
    except Exception as e:
        server_state.log_queue.put_nowait(
            f"[ERROR] Error setting user last logged-in status for '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get(

    "/get/user/{identifier}",

    response_model=UserResponse,

    dependencies=[Security(require_admin)]

)
async def get_user(

        identifier: str,

        auth_identifier: str = Security(require_auth)

):
    try:

        conn = connect_db()

        cursor = conn.cursor()

        cursor.execute(

            """

            SELECT Identifier, Username, CreatedAt, ApiKey

            FROM Users

            WHERE Identifier = ?

            """,

            (identifier,)

        )

        row = cursor.fetchone()

        if row is None:
            cursor.execute(

                """

                SELECT Identifier, Username, CreatedAt, ApiKey

                FROM Users

                WHERE Username = ?

                """,

                (identifier,)

            )

            row = cursor.fetchone()

        conn.close()

        if row is None:
            server_state.log_queue.put_nowait(

                f"[WARN] User '{identifier}' not found"

            )

            raise fastapi.HTTPException(

                status_code=404,

                detail="User not found"

            )

        # Auth-Header muss zum gefundenen User gehören

        if not secrets.compare_digest(

                row["Identifier"],

                auth_identifier

        ):
            server_state.log_queue.put_nowait(

                f"[WARN] Auth mismatch while reading user '{identifier}'"

            )

            raise fastapi.HTTPException(

                status_code=403,

                detail="Forbidden"

            )

        server_state.log_queue.put_nowait(

            f"[INFO] User '{row['Identifier']}' retrieved successfully"

        )

        return {

            "Identifier": row["Identifier"],

            "Username": row["Username"],

            "CreatedAt": row["CreatedAt"],

            "ApiKey": row["ApiKey"],

        }

    except fastapi.HTTPException:

        raise

    except Exception as e:

        server_state.log_queue.put_nowait(

            f"[ERROR] Error retrieving user '{identifier}': {str(e)}"

        )

        raise fastapi.HTTPException(

            status_code=500,

            detail=str(e)

        )


@app.get("/getall/users", response_model=List[UserResponse], dependencies=[Security(require_admin)])
async def get_all_users():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, Username, CreatedAt FROM Users")
        rows = cursor.fetchall()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} users")
        return [dict(row) for row in rows]
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error retrieving all users: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.post("/create-tables/", response_model=MessageResponse, dependencies=[Security(require_admin)])
async def create_table():
    try:
        create_app_tables()
        server_state.log_queue.put_nowait("[INFO] Tables created successfully")
        return {"message": "Tables created successfully"}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error creating tables: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.post("/create/user/", response_model=CreateResponse, dependencies=[Security(require_admin)])
async def handle_create_user_req(req: requests.CreateUserRequest):
    try:
        identifier = str(uuid.uuid4())
        username = req.username
        password = req.password
        created_at = datetime.now().isoformat()

        # Passwort: bcrypt. API-Key: deterministischer SHA-256-Hash, damit
        # eingehende Keys ebenfalls gehasht und die Hashes verglichen werden koennen.
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")

        password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")
        apikey_hash = hash_api_key(req.apikey.strip())

        create_user(username, password_hash, identifier, created_at, apikey_hash)

        server_state.log_queue.put_nowait(f"[INFO] User '{username}' created successfully with id {identifier}")
        return {"message": "User created successfully", "identifier": identifier}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error creating user '{req.username}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@app.post("/delete/user/{identifier}", response_model=MessageResponse)
async def handle_delete_user_req(identifier: str, user=Security(require_user)):
    if not check_owner(identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""DELETE
                          FROM Users
                          WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] User '{identifier}' deleted successfully")
        return {"message": "User deleted successfully"}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error deleting user '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ============================================================
# Playlist Endpoints
# ============================================================

# --- get_playlists: KEIN Admin-Key, unverändert ---
@app.get("/get/playlists/{identifier}", response_model=List[PlaylistResponse],
         dependencies=[Security(require_admin)])
async def get_playlists(identifier: str, auth_identifier: str = Security(require_auth)):
    if not owns_playlist(identifier, auth_identifier):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, Name, Description FROM Playlists WHERE Identifier = ?",
                       (identifier,))
        rows = cursor.fetchall()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Retrieved playlist(s) for identifier '{identifier}'")
        return [dict(row) for row in rows]
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error retrieving playlists for '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.post("/create/playlist/", response_model=CreateResponse)
async def handle_create_playlist_req(req: requests.CreatePlaylistRequest, user=Security(require_user)):
    if not check_owner(req.user_identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        identifier = str(uuid.uuid4())

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""INSERT INTO Playlists (Identifier, UserIdentifier, Name, Description)
                          VALUES (?, ?, ?, ?)""", (identifier, req.user_identifier, req.name, req.description))
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Playlist '{req.name}' created successfully with id {identifier}")
        return {"message": "Playlist created successfully", "identifier": identifier}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error creating playlist '{req.name}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


# HINWEIS: 'identifier' ist hier undefiniert (Bug im Original) – bewusst NICHT angefasst.
@app.post("/delete/playlist/{identifier}", response_model=MessageResponse)
async def handle_delete_playlist_req(identifier: str, user=Security(require_user)):
    if not owns_playlist(identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""DELETE
                          FROM Playlists
                          WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Playlist '{identifier}' deleted successfully")
        return {"message": "Playlist deleted successfully"}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error deleting playlist '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/getall/playlists", response_model=List[PlaylistResponse], dependencies=[Security(require_admin)])
async def get_all_playlists():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, Name, Description FROM Playlists")
        rows = cursor.fetchall()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} playlists")
        return [dict(row) for row in rows]
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error retrieving all playlists: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ============================================================
# DownloadedMedia Endpoints
# ============================================================

@app.post("/create/downloadedmedia", response_model=CreateResponse)
async def handle_create_downloaded_media_req(req: requests.CreateDownloadedMediaRequest,
                                             user=Security(require_user)):
    if not check_owner(req.user_identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""SELECT Identifier FROM DownloadedMedias WHERE DownloadPath = ?""", (req.download_path,))

        existing = cursor.fetchone()
        if existing is not None:
            identifier = existing["Identifier"]
            conn.close()
            server_state.log_queue.put_nowait(f"[INFO] Downloaded media with path '{req.download_path}' already exists")
            return {"message": f"Downloaded media with path '{req.download_path}' already exists",
                    "identifier": identifier}

        identifier = str(uuid.uuid4())
        cursor.execute(
            """INSERT INTO DownloadedMedias (Identifier, UserIdentifier, Url, MediaType, DownloadedAt, DownloadPath,
                                             IsPlayable, Title)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (identifier, req.user_identifier, req.url, req.media_type, req.downloaded_at, req.download_path,
             req.is_playable, req.title)
        )
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(
            f"[INFO] Downloaded media '{req.title}' created successfully with id {identifier}")
        return {"message": "Downloaded media created successfully", "identifier": identifier}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error creating downloaded media '{req.title}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


# HINWEIS: 'identifier' ist hier undefiniert (Bug im Original) – bewusst NICHT angefasst.
@app.post("/delete/downloadedmedia/{identifier}", response_model=MessageResponse)
async def handle_delete_downloaded_media_req(identifier: str, user=Security(require_user)):
    if not owns_record("DownloadedMedias", identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""DELETE
                          FROM DownloadedMedias
                          WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Downloaded media '{identifier}' deleted successfully")
        return {"message": "Downloaded media deleted successfully"}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error deleting downloaded media '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# --- get_downloaded_media: KEIN Admin-Key, unverändert ---
@app.get("/get/downloadedmedia/{identifier}", response_model=DownloadedMediaResponse,
         dependencies=[Security(require_admin)])
async def get_downloaded_media(identifier: str, auth_identifier: str = Security(require_auth)):
    if not owns_record("DownloadedMedias", identifier, auth_identifier):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT Identifier, UserIdentifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable, Title FROM DownloadedMedias WHERE Identifier = ?",
            (identifier,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            server_state.log_queue.put_nowait(f"[ERROR] Downloaded media '{identifier}' not found")
            raise fastapi.HTTPException(status_code=404, detail="Downloaded media not found")

        server_state.log_queue.put_nowait(f"[INFO] Downloaded media '{identifier}' retrieved successfully")
        return dict(row)
    except fastapi.HTTPException:
        raise
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error retrieving downloaded media '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/getall/downloadedmedias", response_model=List[DownloadedMediaResponse],
         dependencies=[Security(require_admin)])
async def get_all_downloaded_media():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT Identifier, UserIdentifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable, Title FROM DownloadedMedias")
        rows = cursor.fetchall()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} downloaded medias")
        return [dict(row) for row in rows]
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error retrieving all downloaded medias: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# --- get_user_downloaded_medias: KEIN Admin-Key, unverändert ---
@app.get("/getuser/downloadedmedias/{user_identifier}", response_model=List[DownloadedMediaResponse],
         dependencies=[Security(require_admin)])
async def get_user_downloaded_medias(user_identifier: str,
                                     auth_identifier: str = Security(require_auth)):
    if not check_owner(user_identifier, auth_identifier):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT Identifier, UserIdentifier, Title, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable FROM DownloadedMedias WHERE UserIdentifier = ?",
            (user_identifier,))
        rows = cursor.fetchall()
        conn.close()

        server_state.log_queue.put_nowait(
            f"[INFO] Retrieved {len(rows)} downloaded medias for user '{user_identifier}'")
        return [dict(row) for row in rows]
    except Exception as e:
        server_state.log_queue.put_nowait(
            f"[ERROR] Error retrieving downloaded medias for user '{user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ============================================================
# Settings Endpoints
# ============================================================

@app.post("/create/settings/", response_model=CreateResponse)
async def handle_create_setting_req(req: requests.CreateSettingsRequest, user=Security(require_user)):
    if not check_owner(req.user_identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        identifier = str(uuid.uuid4())

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO Settings (Identifier, UserIdentifier, DownloadPath, DarkModeEnabled, ScanFolderOnStartup)
               VALUES (?, ?, ?, ?, ?)""",
            (identifier, req.user_identifier, req.default_download_path, req.dark_mode_enabled,
             req.scan_folder_on_startup)
        )
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(
            f"[INFO] Settings created successfully for user '{req.user_identifier}' with id {identifier}")
        return {"message": "Setting created successfully", "identifier": identifier}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error creating settings for user '{req.user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


# HINWEIS: 'identifier' ist hier undefiniert (Bug im Original) – bewusst NICHT angefasst.
@app.post("/delete/settings/{identifier}", response_model=MessageResponse)
async def handle_delete_setting_req(identifier: str, user=Security(require_user)):
    if not owns_record("Settings", identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""DELETE
                          FROM Settings
                          WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Settings '{identifier}' deleted successfully")
        return {"message": "Setting deleted successfully"}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error deleting settings '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# --- get_setting: KEIN Admin-Key, unverändert ---
@app.get("/get/settings/{user_identifier}", response_model=SettingsResponse,
         dependencies=[Security(require_admin)])
async def get_setting(user_identifier: str, auth_identifier: str = Security(require_auth)):
    if not check_owner(user_identifier, auth_identifier):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT Identifier, UserIdentifier, DownloadPath, DarkModeEnabled, ScanFolderOnStartup FROM Settings WHERE UserIdentifier = ?",
            (user_identifier,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            server_state.log_queue.put_nowait(
                f"[INFO] No settings found for user '{user_identifier}' (expected for new users)")
            raise fastapi.HTTPException(status_code=404, detail="Setting not found")

        server_state.log_queue.put_nowait(f"[INFO] Settings retrieved for user '{user_identifier}'")
        return dict(row)
    except fastapi.HTTPException:
        raise
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error retrieving settings for user '{user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/getall/settings", response_model=List[SettingsResponse], dependencies=[Security(require_admin)])
async def get_all_settings():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT Identifier, UserIdentifier, DownloadPath, DarkModeEnabled, ScanFolderOnStartup FROM Settings")
        rows = cursor.fetchall()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} settings entries")
        return [dict(row) for row in rows]
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error retrieving all settings: {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ============================================================
# PlaylistMedia Endpoints
# ============================================================

@app.post("/create/playlistmedia", response_model=CreatePlaylistMediaResponse)
async def handle_create_playlist_media_req(req: requests.CreatePlaylistMediaRequest,
                                           user=Security(require_user)):
    if not owns_playlist(req.playlist_identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM PlaylistMedias WHERE PlaylistIdentifier = ? AND MediaIdentifier = ?",
                       (req.playlist_identifier, req.media_identifier))
        count = cursor.fetchone()[0]

        if count > 0:
            conn.close()
            server_state.log_queue.put_nowait(
                f"[ERROR] Media '{req.media_identifier}' already exists in playlist '{req.playlist_identifier}'")
            raise fastapi.HTTPException(status_code=400, detail="Media already exists in the playlist")

        cursor.execute("SELECT MAX(Position) FROM PlaylistMedias WHERE PlaylistIdentifier = ?",
                       (req.playlist_identifier,))
        max_position_row = cursor.fetchone()
        max_position = max_position_row[0] if max_position_row[0] is not None else 0
        new_position = max_position + 1

        cursor.execute("""INSERT INTO PlaylistMedias (PlaylistIdentifier, MediaIdentifier, Position)
                          VALUES (?, ?, ?)""", (req.playlist_identifier, req.media_identifier, new_position))
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(
            f"[INFO] Media '{req.media_identifier}' added to playlist '{req.playlist_identifier}' at position {new_position}")
        return {"message": "Media added to playlist successfully", "position": new_position}
    except fastapi.HTTPException:
        raise
    except Exception as e:
        server_state.log_queue.put_nowait(
            f"[ERROR] Error adding media '{req.media_identifier}' to playlist '{req.playlist_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@app.post("/delete/playlistmedia", response_model=MessageResponse)
async def handle_delete_playlist_media_req(req: requests.DeletePlaylistMediaRequest,
                                           user=Security(require_user)):
    if not owns_playlist(req.playlist_identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM PlaylistMedias WHERE PlaylistIdentifier = ? AND MediaIdentifier = ?",
                       (req.playlist_identifier, req.media_identifier))
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(
            f"[INFO] Media '{req.media_identifier}' removed from playlist '{req.playlist_identifier}'")
        return {"message": "Media removed from playlist successfully"}
    except Exception as e:
        server_state.log_queue.put_nowait(
            f"[ERROR] Error removing media '{req.media_identifier}' from playlist '{req.playlist_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# --- get_playlist_medias: KEIN Admin-Key, unverändert ---
@app.get("/get/playlistmedias/{playlist_identifier}", response_model=List[PlaylistMediaResponse],
         dependencies=[Security(require_admin)])
async def get_playlist_medias(playlist_identifier: str,
                              auth_identifier: str = Security(require_auth)):
    if not owns_playlist(playlist_identifier, auth_identifier):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT PlaylistIdentifier, MediaIdentifier, Position FROM PlaylistMedias WHERE PlaylistIdentifier = ? ORDER BY Position",
            (playlist_identifier,))
        rows = cursor.fetchall()
        conn.close()

        server_state.log_queue.put_nowait(
            f"[INFO] Retrieved {len(rows)} media entries for playlist '{playlist_identifier}'")
        return [dict(row) for row in rows]
    except Exception as e:
        server_state.log_queue.put_nowait(
            f"[ERROR] Error retrieving media for playlist '{playlist_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# --- get_user_playlists: KEIN Admin-Key, unverändert ---
@app.get("/getuser/playlists/{user_identifier}", response_model=List[PlaylistResponse],
         dependencies=[Security(require_admin)])
async def get_user_playlists(user_identifier: str,
                             auth_identifier: str = Security(require_auth)):
    if not check_owner(user_identifier, auth_identifier):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, UserIdentifier, Name, Description FROM Playlists WHERE UserIdentifier = ?",
                       (user_identifier,))
        rows = cursor.fetchall()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] Retrieved {len(rows)} playlists for user '{user_identifier}'")
        return [dict(row) for row in rows]
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error retrieving playlists for user '{user_identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# ============================================================
# Login / Register / Logout  (KEIN Admin-Key nach außen)
# ============================================================

# --- login: unverändert ---
@app.post("/login", response_model=LoginResponse)
async def handle_login_req(req: requests.LoginRequest):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT Identifier, PasswordHash FROM Users WHERE Username = ?", (req.username,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            server_state.log_queue.put_nowait(f"[ERROR] Login failed: user '{req.username}' not found")
            raise fastapi.HTTPException(status_code=404, detail="User not found")

        identifier, password_hash = row["Identifier"], row["PasswordHash"]

        if not bcrypt.checkpw(req.password.encode("utf-8"), password_hash.encode("utf-8")):
            server_state.log_queue.put_nowait(f"[ERROR] Login failed: invalid password for user '{req.username}'")
            raise fastapi.HTTPException(status_code=401, detail="Invalid password")

        server_state.log_queue.put_nowait(f"[INFO] User '{req.username}' logged in successfully")
        return {"message": "Login successful", "identifier": identifier}
    except fastapi.HTTPException:
        raise
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error during login for user '{req.username}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# GEÄNDERT: interner Aufruf ohne Key.
# handle_create_user_req hat jetzt nur noch (req) als Parameter; der direkte
# Funktionsaufruf umgeht die require_admin-Dependency (die läuft nur über HTTP),
# also bleibt /register wie gehabt offen/public.
@app.post("/register")
async def handle_register_req(req: requests.RegisterRequest):
    try:

        create_user_req = requests.CreateUserRequest(username=req.username, password=req.password, apikey=req.apikey)
        response = await handle_create_user_req(create_user_req)

        if response:
            server_state.log_queue.put_nowait(f"[INFO] User '{req.username}' registered successfully")
            return {"message": "User registered successfully", "identifier": response["identifier"]}
    except fastapi.HTTPException:
        raise
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error during registration for user '{req.username}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


# --- logout: unverändert ---
@app.post("/logout/{identifier}")
async def handle_logout_req(identifier: str, user=Security(require_user)):
    if not check_owner(identifier, user["Identifier"]):
        raise fastapi.HTTPException(status_code=403, detail="Forbidden")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""UPDATE Users
                          SET LoggedIn = 0
                          WHERE Identifier = ?""", (identifier,))
        conn.commit()
        conn.close()

        server_state.log_queue.put_nowait(f"[INFO] User '{identifier}' logged out successfully")
        return {"message": "Logout successful"}
    except Exception as e:
        server_state.log_queue.put_nowait(f"[ERROR] Error during logout for user '{identifier}': {str(e)}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))
