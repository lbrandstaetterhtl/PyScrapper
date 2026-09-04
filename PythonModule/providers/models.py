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

GOOD_URL_KEYWORDS = {
    "master": 100,
    "playlist": 80,
    "index": 70,
    "stream": 50,
    "audio": 20,
    "video": 20,
}

BAD_URL_KEYWORDS = {
    "preview": -100,
    "sample": -100,
    "thumbnail": -500,
    "image": -500,
    "banner": -500,
    "ads": -1000,
}

URL_EXTENSION_KEYWORDS = {
    # ==================================================
    # HLS
    # ==================================================

    "master.m3u8": "m3u8",
    "playlist.m3u8": "m3u8",
    "index.m3u8": "m3u8",
    ".m3u8": "m3u8",

    "application/vnd.apple.mpegurl": "m3u8",
    "application%2fvnd.apple.mpegurl": "m3u8",
    "application/x-mpegurl": "m3u8",
    "application%2fx-mpegurl": "m3u8",


    # ==================================================
    # DASH
    # ==================================================

    "manifest.mpd": "mpd",
    ".mpd": "mpd",

    "application/dash+xml": "mpd",
    "application%2fdash%2bxml": "mpd",


    # ==================================================
    # MP3
    # ==================================================

    ".mp3": "mp3",

    "mp3-64": "mp3",
    "mp3-96": "mp3",
    "mp3-128": "mp3",
    "mp3-160": "mp3",
    "mp3-192": "mp3",
    "mp3-256": "mp3",
    "mp3-320": "mp3",

    "mp3_64": "mp3",
    "mp3_96": "mp3",
    "mp3_128": "mp3",
    "mp3_160": "mp3",
    "mp3_192": "mp3",
    "mp3_256": "mp3",
    "mp3_320": "mp3",

    "audio/mpeg": "mp3",
    "audio%2fmpeg": "mp3",
    "audio/mp3": "mp3",
    "audio%2fmp3": "mp3",

    "format=mp3": "mp3",
    "ext=mp3": "mp3",


    # ==================================================
    # M4A
    # ==================================================

    ".m4a": "m4a",

    "audio/mp4": "m4a",
    "audio%2fmp4": "m4a",

    "format=m4a": "m4a",
    "ext=m4a": "m4a",

    "mime=audio%2fmp4": "m4a",
    "mime_type=audio%2fmp4": "m4a",


    # ==================================================
    # AAC
    # ==================================================

    ".aac": "aac",

    "aac_64k": "aac",
    "aac_96k": "aac",
    "aac_128k": "aac",
    "aac_160k": "aac",
    "aac_192k": "aac",
    "aac_256k": "aac",
    "aac_320k": "aac",

    "aac-64": "aac",
    "aac-96": "aac",
    "aac-128": "aac",
    "aac-160": "aac",
    "aac-192": "aac",
    "aac-256": "aac",
    "aac-320": "aac",

    "audio/aac": "aac",
    "audio%2faac": "aac",

    "format=aac": "aac",
    "ext=aac": "aac",


    # ==================================================
    # FLAC
    # ==================================================

    ".flac": "flac",

    "audio/flac": "flac",
    "audio%2fflac": "flac",
    "audio/x-flac": "flac",
    "audio%2fx-flac": "flac",

    "format=flac": "flac",
    "ext=flac": "flac",


    # ==================================================
    # WAV
    # ==================================================

    ".wav": "wav",

    "audio/wav": "wav",
    "audio%2fwav": "wav",
    "audio/x-wav": "wav",
    "audio%2fx-wav": "wav",
    "audio/wave": "wav",
    "audio%2fwave": "wav",

    "format=wav": "wav",
    "ext=wav": "wav",


    # ==================================================
    # OGG
    # ==================================================

    ".ogg": "ogg",
    ".oga": "ogg",

    "audio/ogg": "ogg",
    "audio%2fogg": "ogg",
    "application/ogg": "ogg",
    "application%2fogg": "ogg",

    "format=ogg": "ogg",
    "ext=ogg": "ogg",


    # ==================================================
    # OPUS
    # ==================================================

    ".opus": "opus",

    "audio/opus": "opus",
    "audio%2fopus": "opus",

    "format=opus": "opus",
    "ext=opus": "opus",


    # ==================================================
    # WEBM
    # ==================================================

    ".webm": "webm",

    "audio/webm": "webm",
    "audio%2fwebm": "webm",
    "video/webm": "webm",
    "video%2fwebm": "webm",

    "format=webm": "webm",
    "ext=webm": "webm",

    "mime=audio%2fwebm": "webm",
    "mime=video%2fwebm": "webm",
    "mime_type=audio%2fwebm": "webm",
    "mime_type=video%2fwebm": "webm",


    # ==================================================
    # MP4
    # ==================================================

    ".mp4": "mp4",

    "video/mp4": "mp4",
    "video%2fmp4": "mp4",

    "format=mp4": "mp4",
    "ext=mp4": "mp4",

    "mime=video%2fmp4": "mp4",
    "mime_type=video%2fmp4": "mp4",


    # ==================================================
    # MKV / Matroska
    # ==================================================

    ".mkv": "mkv",

    "video/x-matroska": "mkv",
    "video%2fx-matroska": "mkv",
    "video/matroska": "mkv",
    "video%2fmatroska": "mkv",

    "format=mkv": "mkv",
    "ext=mkv": "mkv",

    "matroska": "mkv",


    # ==================================================
    # MOV / QuickTime
    # ==================================================

    ".mov": "mov",

    "video/quicktime": "mov",
    "video%2fquicktime": "mov",

    "format=mov": "mov",
    "ext=mov": "mov",


    # ==================================================
    # M4V
    # ==================================================

    ".m4v": "m4v",

    "video/x-m4v": "m4v",
    "video%2fx-m4v": "m4v",

    "format=m4v": "m4v",
    "ext=m4v": "m4v",


    # ==================================================
    # AVI
    # ==================================================

    ".avi": "avi",

    "video/x-msvideo": "avi",
    "video%2fx-msvideo": "avi",
    "video/avi": "avi",
    "video%2favi": "avi",

    "format=avi": "avi",
    "ext=avi": "avi",


    # ==================================================
    # WMV
    # ==================================================

    ".wmv": "wmv",

    "video/x-ms-wmv": "wmv",
    "video%2fx-ms-wmv": "wmv",

    "format=wmv": "wmv",
    "ext=wmv": "wmv",


    # ==================================================
    # MPEG / MPG
    # ==================================================

    ".mpeg": "mpeg",
    ".mpg": "mpg",

    "video/mpeg": "mpeg",
    "video%2fmpeg": "mpeg",

    "format=mpeg": "mpeg",
    "ext=mpeg": "mpeg",

    "format=mpg": "mpg",
    "ext=mpg": "mpg",


    # ==================================================
    # MPEG-TS
    # ==================================================

    ".ts": "ts",

    "video/mp2t": "ts",
    "video%2fmp2t": "ts",

    "format=ts": "ts",
    "ext=ts": "ts",
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

    post_body : str | None = None

    info : core.models.Download.Info = field(default_factory=core.models.Download.Info)

    audio_url :str = ""




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

    total_size = -1
    mime_type = ""

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

        return int(total_size) if total_size is not None else -1, mime_type



    

#This is old, stays here just in case old browser and media gets used
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
class FoundMedia:
    url: str
    prio : int = -1

    stream_type : core.models.Download.DownloadType = core.models.Download.DownloadType.UNKNOWN
    media_type : str = ""

    extension: str = ""
    mime_type: str = ""

    total_size: int = -1

    extra_headers : dict[str, str] = field(default_factory=dict)
    post_body : bytes | None = None

    audio_url: str = ""




def makeProviderResultFromBrowserMediaList(
    medialist: list[core.models.media.Media2],
    download_type: core.models.Download.DownloadType
) -> ProviderResult:

    pass

def _getUrlPriority(url: str) -> int:
    urlLower = url.lower()
    prio = 0

    for keyword, points in GOOD_URL_KEYWORDS.items():
        if keyword in urlLower:
            prio += points

    for keyword, points in BAD_URL_KEYWORDS.items():
        if keyword in urlLower:
            prio += points

    return prio


def _getExtensionFromUrl(url: str) -> str:
    decodedUrl = urllib.parse.unquote(url).lower()
    parsed = urllib.parse.urlsplit(decodedUrl)

    path = parsed.path.lower()


    fileName = path.rsplit("/", 1)[-1]

    if "." in fileName:
        extension = fileName.rsplit(".", 1)[-1]

        if extension in MEDIA_EXTENSION_PRIORITY:
            return extension


    for keyword, extension in sorted(
        URL_EXTENSION_KEYWORDS.items(),
        key=lambda item: len(item[0]),
        reverse=True
    ):
        if keyword in url:
            return extension


    return ""




def _makeFoundMediaFromUrl(
        media: FoundMedia
):
    url = urllib.parse.unquote(media.url).lower()


    if not media.extension:
        media.extension = _getExtensionFromUrl(url)



    if not media.media_type and media.extension:
        media.media_type = _getMediaKind(
            media.extension
        ) or ""


    if not media.mime_type and media.extension:

        if (
            media.extension == "webm"
            and media.media_type == "audio"
        ):
            media.mime_type = "audio/webm"

        else:
            media.mime_type = EXTENSION_CONTENT_TYPES.get(
                media.extension,
                ""
            )

    if (
        not media.stream_type
        or media.stream_type == core.models.Download.DownloadType.UNKNOWN
    ):

        if media.extension == "m3u8":
            media.stream_type = core.models.Download.DownloadType.HLS

        elif media.extension == "mpd":
            media.stream_type = core.models.Download.DownloadType.DASH

        elif media.extension in SUPPORTED_EXTENSIONS:
            media.stream_type = core.models.Download.DownloadType.FILE

    if media.prio < 0:
        media.prio = 0

        if media.extension:
            media.prio += MEDIA_EXTENSION_PRIORITY.get(
                media.extension,
                0
            )

        media.prio += _getUrlPriority(url)

    return media

    

    


def makeProviderResult(
        found_media_list: list[FoundMedia],
        request: ProviderResultRequest,
    ):


    preferredFile = request.preferred_file

    if preferredFile:
        preferredFile = preferredFile.strip().lower().removeprefix(".")
        if preferredFile not in SUPPORTED_EXTENSIONS:
            raise core.models.errors.ArgumentError(
                argument="preferred_file",
                wanted_type=f"string -> with value {', '.join(SUPPORTED_EXTENSIONS)}",
                caller="[providers] makeProviderResult"
            )

    if request.preferred_type:
        if request.preferred_type not in ["audio", "video"]:
            raise core.models.errors.ArgumentError(
                argument="preferred_type",
                wanted_type=f"string -> with value 'audio', 'video'",
                caller="[providers] makeProviderResult"
            )

    bestMedia = FoundMedia(
        url=""
    )

    for i, media in enumerate(found_media_list):

        if (
            not media.extension
            
        ):
            media = _makeFoundMediaFromUrl(media)
            

        #Add check that checks if stuff like media type is unknown just in case and then update media object to continue normally
        print(f"Checking entry: {i}/{len(found_media_list)}")
        print(media)

        if request.preferred_file:
            if media.extension == request.preferred_file.lower():
                media.prio += 1000

        if request.preferred_type:
            if media.media_type == request.preferred_type.lower():
                media.prio += 200

        if media.prio > bestMedia.prio:
            bestMedia = media

        

    if not bestMedia.url:
        raise core.models.errors.TaskFailedError(
            task="[providers] makeProviderResult",
            reason="Didn't find any media with supported extensions",
            extraMessages=[
                "Now listing the supported files:",
                f"{', '.join(SUPPORTED_EXTENSIONS)}",
            ],
            caller="[providers] makeProviderResult"
        )
    

    return _buildProviderResultFromFoundMedia(
        bestMedia,
        request
    )







def _buildProviderResultFromFoundMedia(
        media : FoundMedia,
        request: ProviderResultRequest,
) -> ProviderResult:


    size = media.total_size
    if size< 0:
        size, mime = getUrlInformation(
            session=request.ses,
            url=media.url,
            extra_headers=media.extra_headers
        )
#Server works with total size or total segments depending on file or hls
    if media.stream_type == core.models.Download.DownloadType.HLS:
        size = -1
    
    result = ProviderResult(
        url=media.url,
        download_type=media.stream_type,
        extra_headers=media.extra_headers,
        file_ending=media.extension,
        media_type=media.media_type,
        mime_type=media.mime_type,
        total_size=size,
        post_body=media.post_body,
        audio_url=media.audio_url,
        info = core.models.Download.Info(
            url=media.url,
            found_file=media.extension,
            preferred_file=request.preferred_file if request.preferred_file else media.extension,
            found_type=media.media_type,
            preferred_type=request.preferred_type if request.preferred_type else media.media_type
        )
        
    )

    print(result)


    return result
    

    
def _getMediaKind(extension: str) -> str | None:
    extension = extension.lower()

    if extension in AUDIO_EXTENSIONS:
        return "audio"

    if extension in VIDEO_EXTENSIONS:
        return "video"

    return None