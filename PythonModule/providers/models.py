# core imports

import PythonModule.core as core
from PythonModule.core.network.Session import Session

#Python default imports
from dataclasses import dataclass, field
from enum import Enum
import urllib.request, urllib.parse
import os

AUDIO_EXTENSIONS = [
    "mp3",
    "m4a",
    "aac",
    "flac",
    "wav",
    "ogg",
    "opus",
]

VIDEO_EXTENSIONS = [
    "mp4",
    "mkv",
    "webm",
    "mov",
    "m4v",
    "avi",
    "wmv",
    "mpg",
    "mpeg",
    "ts",
]

SUPPORTED_EXTENSIONS = [
    "mp4",
    "mkv",
    "webm",
    "mov",
    "m4v",
    "avi",
    "wmv",
    "mpg",
    "mpeg",
    "ts",
    "mp3",
    "m4a",
    "aac",
    "flac",
    "wav",
    "ogg",
    "opus",
]

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
    "webm-audio" : "audio/webm",
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

#Example mp3
    file_ending: str | None = None

#Example audio
    media_type: str | None = None

#Example audio/mp3
    mime_type : str | None = None

    total_size : int = 0

    info : core.models.Download.Info = field(default_factory=core.models.Download.Info)




@dataclass
class ProviderResultRequest:
    url: str

    ses: Session

    extra_headers: dict | None = None

    preferred_type: str | None = None

    preferred_file: str | None = None
    

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

        if self.preferred_type is not None:
            core.general.Validate.general.validateStr(argument_name="preferred_type", string=self.preferred_type, caller="ProviderResultRequest.__post_init__")

            if self.preferred_type not in ["audio", "video"]:
                raise core.models.errors.ArgumentError(argument="preferred_type", wanted_type="string with value 'audio' or 'video'", caller="ProviderResultRequest.__post_init__")

        if self.preferred_file is not None:
            core.general.Validate.general.validateStr(argument_name="preferred_file", string=self.preferred_file, caller="ProviderResultRequest.__post_init__")


            supported_files: list[str] = []
            for key in MEDIA_EXTENSION_PRIORITY.keys():
                supported_files.append(key)

            if not any(file == self.preferred_file for file in supported_files):
                raise core.models.errors.ArgumentError(
                    argument="preferred_type",
                    wanted_type=f"string with value: {', '.join(supported_files)}",
                    caller="ProviderResultRequest.__post_init__")
                




class ProviderNames(Enum):
    YOUTUBE = "youtube"
    BANDCAMP = "bandcamp"
    DEFAULT = "default"
    SOUNDCLOUD = "soundcloud"








def getUrlInformation(
        session,
        url: str,
        extra_headers: dict | None = None
)-> tuple[int | None, str | None]:
    req = urllib.request.Request(
        url,
        headers={
            "Range" : "bytes=0-0"
        }
    )

    total_size = None

    with session.open(request=req, headers=extra_headers) as response:
        content_range = response.headers.get("Content-Range")
        content_length = response.headers.get("Content-Length")
        content_type = response.headers.get("Content-Type")
        if content_type:
            mime_type = content_type.split(";", 1)[0].strip().lower()

        if content_range:

            total = content_range.split("/")[-1]

            if total != "*":
                total_size = int(total)

        elif content_length:
            total_size = int(content_length)

        return int(total_size) if total_size is not None else None, mime_type



    


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




@dataclass
class BestMedia:
    url: str | None = None
    prio : int = -1

    is_preferred_type: bool = False
    is_preferred_file : bool = False

    media_type : str | None = None
    file_ending : str | None = None


def makeProviderResult(
        urls: list[str],
        request: ProviderResultRequest,
        download_type : core.models.Download.DownloadType
    ):

    preferredFile = request.preferred_file

    if preferredFile:
        preferredFile = preferredFile.strip().lower().removeprefix(".")
        if preferredFile not in SUPPORTED_EXTENSIONS:
            raise core.models.errors.ArgumentError(
                argument="preferred_file",
                wanted_type=f"string -> with value {', '.join(SUPPORTED_EXTENSIONS)}",
                caller="[providers] get_best_Url"
            )

    if request.preferred_type:
        if request.preferred_type not in ["audio", "video"]:
            raise core.models.errors.ArgumentError(
                argument="preferred_type",
                wanted_type=f"string -> with value 'audio', 'video'",
                caller="[providers] get_best_Url"
            )

    bestMedia = BestMedia(
        url=None
    )

    for url in urls:
        foundPreferredType: bool = False
        foundPreferredFile: bool = False

        path = urllib.parse.urlparse(url).path

        filename = os.path.basename(path)
        name, extension = os.path.splitext(filename)
        extension = extension.lower().removeprefix(".")

        prio: int = MEDIA_EXTENSION_PRIORITY.get(extension, None)

        if prio is None:
            continue

        mediaKind = get_media_kind(extension)
        if request.preferred_type and mediaKind == request.preferred_type.lower():
            foundPreferredType = True
            prio += 200

        if preferredFile and extension == preferredFile.lower():
            foundPreferredFile = True
            prio += 1000

        if prio > bestMedia.prio:
            bestMedia.prio = prio
            bestMedia.url = url
            bestMedia.file_ending = extension
            bestMedia.media_type = mediaKind
            bestMedia.is_preferred_file = foundPreferredFile
            bestMedia.is_preferred_type = foundPreferredType

    if bestMedia.url is None:
        raise core.models.errors.TaskFailedError(
            task="[providers] get_best_Url",
            reason="Didn't find any media with supported extensions",
            extraMessages=[
                "Now listing the supported files:",
                f"{', '.join(SUPPORTED_EXTENSIONS)}",
            ],
            caller="[providers] get_best_Url"
        )
    

    result = _buildProviderResult(
        bestMedia,
        request
    )
    result.download_type = download_type
    return result





def _buildProviderResult(
        media : BestMedia,
        request: ProviderResultRequest,
) -> ProviderResult:

    fileEnding = media.file_ending

    if fileEnding.lower() == "m3u8":
        fileEnding = "ts"

    size, mime = getUrlInformation(
        session=request.ses,
        url=media.url,
        extra_headers=request.extra_headers
    )
    
    result = ProviderResult(
        url=media.url,
        download_type=None,
        extra_headers=request.extra_headers,
        file_ending=fileEnding,
        media_type=media.media_type,
        mime_type=mime,
        total_size=size,
        info = core.models.Download.Info(
            url=media.url,
            found_file=media.file_ending,
            preferred_file=request.preferred_file if request.preferred_file else media.file_ending,
            found_type=media.media_type,
            preferred_type=request.preferred_type if request.preferred_type else media.media_type
        )
    )


    return result
    

    
def get_media_kind(extension: str) -> str | None:
    extension = extension.lower()

    if extension in AUDIO_EXTENSIONS:
        return "audio"

    if extension in VIDEO_EXTENSIONS:
        return "video"

    return None