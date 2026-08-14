# core imports

import PythonModule.core as core
from PythonModule.core.network.Session import Session

#Python default imports
from dataclasses import dataclass, field
from enum import Enum



CONTENT_TYPE_EXTENSIONS = {
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/x-matroska": "mkv",
    "video/mp2t": "ts",

    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/aac": "aac",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/flac": "flac",
    "audio/ogg": "ogg",

    "application/vnd.apple.mpegurl": "m3u8",
    "application/x-mpegurl": "m3u8",
    "application/dash+xml": "mpd",
}

EXTENSION_CONTENT_TYPES = {
    "mp4": "video/mp4",
    "webm": "video/webm",
    "mkv": "video/x-matroska",
    "ts": "video/mp2t",

    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "ogg": "audio/ogg",

    "m3u8": "application/vnd.apple.mpegurl",
    "mpd": "application/dash+xml",
}

@dataclass
class ProviderResult:
    url: str 

    download_type: core.models.Download.DownloadType

    extra_headers: dict | None = None

    file_type: str = "mp4"




@dataclass
class ProviderResultRequest:
    url: str

    ses: Session

    extra_headers: dict | None = None

    def __post_init__(self):
        core.general.Validate.download.validateHostDefault(
            self.url,caller="ProviderResultRequest.__post_init__"
        )

        core.general.Validate.special.validateSession(
            self.ses, caller="ProviderResultRequest.__post_init__"
        )

        if self.extra_headers:
            core.general.Validate.general.validateDict(
                argument_name="extra_headers", dictionary=self.extra_headers, caller="ProviderResultRequest.__post_init__"
            )


class ProviderNames(Enum):
    YOUTUBE = "youtube"
    BANDCAMP = "bandcamp"
    DEFAULT = "default"
    SOUNDCLOUD = "soundcloud"





def getContentType(
        url: str,
        session: Session
) -> str | None:

    with session.open(url=url) as response:
        content_type: str = response.headers.get("Content-Type")
        if content_type:
            content_type = content_type.split(";", 1)[0].strip()
            return CONTENT_TYPE_EXTENSIONS.get(content_type, None)

        return None
            


def makeProviderResultFromCandidate(candidate: core.models.media.Media):
    if  candidate.streamType == core.models.media.StreamType.HLS:
            downloadType = core.models.Download.DownloadType.HLS
            if candidate.mediaExtension == "m3u8": 
                candidate.mediaExtension = "ts"

    elif candidate.streamType == core.models.media.StreamType.DIRECT:
        downloadType = core.models.Download.DownloadType.FILE
    else:
        downloadType = None

    
    result =  ProviderResult(
        url = candidate.mediaUrl,
        download_type=downloadType,
        extra_headers=candidate.headers.to_dict(),
        file_type=candidate.mediaExtension
    )

    return result

def makeProviderResult(
        url: str,
        fileending: str,
        type : core.models.Download.DownloadType,
        extra_headers: dict | None = None
):

    if fileending == "m3u8":
        fileending = "ts"

    result = ProviderResult(
        url=url,
        download_type=type,
        extra_headers=extra_headers,
        file_type=fileending
    )

    return result
    
