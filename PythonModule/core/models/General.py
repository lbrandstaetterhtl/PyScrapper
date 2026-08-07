#CORE Imports
from ..request.Session import Session

#Python Default Imports
from dataclasses import dataclass, field
import asyncio




@dataclass
class DownloadInformations:
    filename: str = ""
    fileending: str = ""

    downloadPath: str = ""
    outFile: str = ""

    url: str = ""
    session: Session = None

    downloadProgress: dict = field(default_factory=dict)
    providerStr: str = ""

    downloadLimiter: asyncio.Semaphore = asyncio.Semaphore(10)