# core imports

import PythonModule.core as core
from PythonModule.core.network.Session import Session

#Python default imports
from dataclasses import dataclass, field
from enum import Enum
import urllib.request



NEWGROUNDS_MEDIA_PRIORITY = {
    # Lossless Audio
    "flac": 100,
    "wav": 95,

    # Sehr brauchbares Video
    "mp4": 90,
    "webm": 85,

    # Andere Audioformate
    "m4a": 80,
    "aac": 78,
    "opus": 76,
    "ogg": 74,
    "mp3": 70,

    # Sonstige Video-Container
    "mkv": 65,
    "mov": 60,
}

MEDIA_EXTENSION_PRIORITY = {
    # Video + Audio Container
    "mp4": 100,
    "mkv": 95,
    "webm": 90,
    "mov": 80,
    "m4v": 80,
    "avi": 70,
    "wmv": 60,
    "mpg": 55,
    "mpeg": 55,
    "ts": 50,

    # Audio
    "flac": 45,
    "wav": 40,
    "m4a": 38,
    "aac": 35,
    "ogg": 32,
    "opus": 30,
    "mp3": 25,

    # Playlists / Streams
    "m3u8": 20,
    "mpd": 20,
}

#Priority list when audio quality is more important
MEDIA_PRIORITY_FOR_QUALITY_AUDIO = {
    # Lossless Audio
    "flac": 100,
    "wav": 95,

    # modern audio formats
    "m4a": 85,
    "aac": 80,
    "opus": 78,
    "ogg": 75,

    # video less important
        "mp4": 70,
        "mkv": 65,
        "webm": 50,

    # poor old mp3
    "mp3": 40,

    
}

CONTENT_TYPE_EXTENSIONS = {
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/x-matroska": "mkv",
    "video/mp2t": "ts",

    "audio/mpeg": "mp3",
    "audio/mp3" : "mp3",
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

    total_size : int | None = None




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
        session: Session,
        extra_headers: dict | None = None
) -> str | None:

    with session.open(url=url, headers=extra_headers) as response:
        content_type: str = response.headers.get("Content-Type")
        print(content_type)
        if content_type:
            content_type = content_type.split(";", 1)[0].strip()
            return CONTENT_TYPE_EXTENSIONS.get(content_type, None)

        return None


def getFileInformations(
        session,
        url: str,
        extra_headers: dict | None = None
):
    req = urllib.request.Request(
        url,
        headers={
            "Range" : "bytes=0-0"
        }
    )

    with session.open(request=req, headers=extra_headers) as response:
        content_range = response.headers.get("Content-Range")
        content_length = response.headers.get("Content-Length")

        if content_range:

            total = content_range.split("/")[-1]

            if total != "*":
                total_size = int(total)

        elif content_length:
            total_size = int(content_length)

        return total_size



    


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
        file_type=candidate.mediaExtension,
        
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
    
