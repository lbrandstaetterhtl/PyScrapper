#CORE Imports
from ..network.Session import Session
from ..general.render import makeBorder


#Python Default Imports
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import asyncio



class TaskStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"

class DownloadStrategie(Enum):
    STREAM = "stream"
    LOCAL = "local"
    CACHED_STREAM = "cached_stream"

class DownloadType(Enum):
    HLS = auto()
    FILE = auto()
    DASH = auto()




@dataclass
class DownloadTarget:
    url: str

    download_type : DownloadType

    resolved_url: str = ""

    file_name: str = ""

    out_file: str = ""

    file_ending: str = "mp4"

    extra_headers: dict[str, str] = field(default_factory=dict)

    job_id: str = "unknown"

    total_size : int = 0

    def __post_init__(self):
        self.resolved_url = self.url

    def __str__(self) -> str:
        strings = [
            f"[JOB] {self.job_id}",
            f"URL: {self.url}",
            f"Output file: {self.out_file}",
            f"Extra headers: {len(self.extra_headers)}",
            f"Type: {str(self.download_type)}"
        ]

        return makeBorder(
            "DOWNLOAD TARGET",
            strings
        )



@dataclass
class DownloadProgress:
    job_id : str = "unknown"

    status: TaskStatus = TaskStatus.QUEUED

    start_time: float | None = None

    progress: float = 0.0

    downloaded_bytes: int = 0
    total_bytes: int = -1

    downloaded_segments: int = 0
    total_segments: int = -1

    speed: float = 0.
    eta: float | None = None

    error_message: str | None = None


    def __str__(self) -> str:
        strings = [
            f"[JOB] {self.job_id}",
            f"[STATUS] {self.status.name}",
            f"Progress: {self.progress:.2f}%", 
            f"Bytes: {self.downloaded_bytes}/{self.total_bytes}",
            f"Segments: {self.downloaded_segments}/{self.total_segments}",
            f"Speed: {self.speed:.2f} MiB/s",
            f"ETA: {self.eta} s"
        ]

        if self.error_message:
            strings.append(
                f"Error: {str(self.error_message)}"
            )

        return makeBorder(
            "DOWNLOAD PROGRESS",
            strings
        )




@dataclass
class ConvertProgress:
    job_id : str = "unknown"

    status : TaskStatus = TaskStatus.QUEUED
    total_converts: int = 0

    convert_progress: float = 0.0
    finished_converts: int = 0

    error_message: str = ""

    def __str__(self) -> str:
        strings = [
            f"[JOB] {self.job_id}",
            f"[STATUS] {self.status.name}",
            f"Total converts: {self.total_converts}",
            f"Finished converts: {self.finished_converts}",
            (
                "Converts left: "
                f"{self.total_converts - self.finished_converts}"
            ),
            f"Progress: {self.convert_progress:.2f}%"
        ]
        if self.error_message:
            strings.append(self.error_message)

        return makeBorder(
            "CONVERT PROGRESS",
            strings
        )
        

    
@dataclass
class DownloadContext:

    target: DownloadTarget

    download_progress : DownloadProgress = field(
        default_factory=DownloadProgress
    )

    convert_progress : ConvertProgress = field(
        default_factory=ConvertProgress
    )

    download_limiter: asyncio.Semaphore = field(
        default_factory=lambda: asyncio.Semaphore(1)
    )



    def __str__(self) -> str:
        strings = [
            f"[JOB] {self.target.job_id}",
            f"URL: {self.target.url}",
            (
                "Download: "
                f"{self.download_progress.progress:.2f}%"
            ),
            (
                "Convert: "
                f"{self.convert_progress.convert_progress:.2f}%"
            )
        ]

        return makeBorder(
            "DOWNLOAD CONTEXT",
            strings
        )




@dataclass 
class DownloadInformation:
    job_id: str

    session: Session

    contexts: list[DownloadContext] = field(
        default_factory=list
    )

    download_limiter: asyncio.Semaphore = field(
        default_factory=lambda: asyncio.Semaphore(1)
    )

    download_strategie: DownloadStrategie = DownloadStrategie.LOCAL


    def __post_init__(self):
        if isinstance(self.contexts, DownloadContext):
            self.contexts = [self.contexts]

    

        for index, context in enumerate(self.contexts):
            if context.target.job_id == "unknown":
                context_id = f"{self.job_id}-Context{index}"

                context.target.job_id = context_id
                context.download_progress.job_id = context_id
                context.convert_progress.job_id = context_id



    def __str__(self) -> str:
        strings = [
            f"[JOB] {self.job_id}",
            f"Contexts: {len(self.contexts)}",
            f"Strategie: {self.download_strategie}"
        ]

        for index, context in enumerate(
            self.contexts,
            start=1
        ):
            strings.append(
                f"Context {index}: "
                f"{context.download_progress.progress:.2f}% "
                f"[{context.download_progress.status.name}]"

            )
        
        return makeBorder(
            "DOWNLOAD INFORMATION",
            strings
        )

 

#Converts the whole struct to a dict and returns it
    def toDict(self) -> dict:
        return {
            "job_id": self.job_id,
            "contexts": [
                {
                    "target": asdict(context.target),
                    "download_progress": asdict(
                        context.download_progress
                    ),
                    "convert_progress": asdict(
                        context.convert_progress
                    )
                }
                for context in self.contexts
            ]
        }
