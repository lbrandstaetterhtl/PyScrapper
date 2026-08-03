import enum
from dataclasses import dataclass, field
from PythonModule.core.request.Session import Session
import asyncio

class ProviderTypes(enum.Enum):
    Default = enum.auto()
    ERROR = enum.auto()
    Youtube = enum.auto()
    Bandcamp = enum.auto()
    Archive = enum.auto()
    Suno = enum.auto()
    Soundcloud = enum.auto()
    Wcoflix = enum.auto()
    Aniworld = enum.auto()

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



import PythonModule.providers as p

providerDownloadMapping: dict = {
    ProviderTypes.Archive : p.Archive.download,
    ProviderTypes.Suno : p.Suno.download,
    ProviderTypes.Youtube : p.Youtube.download,
    ProviderTypes.Bandcamp : p.Bandcamp.download,
    ProviderTypes.Default : p.Default.download,
    ProviderTypes.Soundcloud : p.Soundcloud.download
}

providerSearchMapping: dict = {
    ProviderTypes.Archive : p.Archive.search,
    ProviderTypes.Youtube : p.Youtube.search,
    ProviderTypes.Bandcamp : p.Bandcamp.search
}


