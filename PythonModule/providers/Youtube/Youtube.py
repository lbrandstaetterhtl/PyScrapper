#Core Imports
import PythonModule.core as core
from PythonModule.core.network import html
from PythonModule.core.network.Session import Session
from PythonModule.core.network import EmergencyBrowser
from PythonModule.core.network import browser

# Own imports
from . import models

#PythonModule imports
from PythonModule.models.requests import SearchFilters

#Python Default Imports
import os
import shutil
import pathlib
import urllib.parse
import json
import re
import time




#PIP Imports
from yt_dlp import YoutubeDL





    



def find_ffmpeg() -> str | None:
    """Locate ffmpeg.exe – checks PATH first, then the WinGet package folder (yt-dlp.FFmpeg)."""
    # 1) Already on PATH?
    path = shutil.which("ffmpeg")
    if path:
        return str(pathlib.Path(path).resolve())

    # 2) WinGet packages (yt-dlp.FFmpeg)
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        pkg_root = pathlib.Path(local_app) / "Microsoft" / "WinGet" / "Packages"
        if pkg_root.is_dir():
            for hit in pkg_root.rglob("ffmpeg.exe"):
                if "yt-dlp.FFmpeg" in str(hit):
                    return str(hit.resolve())

    return None






    
    
    

        






def getYoutubeFormats(
    url: str,
    cookie_file: str | None = None,
):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "default",
                    "web_safari",
                ]
            }
        },
    }

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            url,
            download=False
        )

    return info

def getMediaInformation(
    request: models.ProviderResultRequest,
    retrys: int = 3
) -> models.ProviderResult:

    core.general.Validate.general.validateInt(
            argument_name="retrys",
            integer=retrys,
            caller="Youtube.getMediaInformationMusic"
        )

    core.general.Validate.general.validateGeneralType(
            argument_name="request",
            obj=request,
            objType=models.ProviderResultRequest,
            caller="Youtube.getMediaInformation"
        )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=[
            "www.youtube.com",
            "youtube.com"
        ],
        caller="[providers] Youtube.getMediaInformation"
    )


    googleVideoMediaList: list[core.models.media.Media2] = []
    
    def _getMedia(Browser: browser.MediaBrowser):

        Browser.run(headless=False, wait_ms=4000)
        mediaList, unknownList = Browser.stop()
        

        YOUTUBE_INTERESTING_URLS = (
            "/youtubei/v1/player",
            "/api/stats/playback",
            "/api/stats/qoe",
            "/videoplayback",
        )

        for _media in mediaList:
            _media: core.models.media.Media2

            if any(keyword in _media.response_url.lower() for keyword in YOUTUBE_INTERESTING_URLS):
                googleVideoMediaList.append(_media)

        for _media in unknownList:

            if any(keyword in _media.response_url.lower() for keyword in YOUTUBE_INTERESTING_URLS):
                googleVideoMediaList.append(_media)
            
            

        
    retry: int = 0
    Browser = browser.MediaBrowser(request.url)

    while retry <= retrys:
        if googleVideoMediaList:
            break
        print(f"[providers] Youtube.getMEdiaInformationMusic: Trying to get media. Try: {retry}/{retrys}")
        retry += 1
        _getMedia(Browser)
    
    

    if not googleVideoMediaList:
        raise core.models.errors.TaskFailedError(
            task="[providers] Youtube.getMediaInformationMusic",
            reason="Couldn't find valid url",
            caller="[providers] Youtube.getMediaInformationMusic"
        )
    _media = None

    for media in googleVideoMediaList:
        
        if "sabr=1" in media.response_url:
            _media = media
            break


    return models.ProviderResult(
        url=_media.request_url,
        download_type=core.models.Download.DownloadType.UMP,
        extra_headers=_media.request_headers,
        file_ending="webm",
        media_type="video",
        mime_type="video/webm",
        total_size=0,
        post_body=_media.request_body,
        info=core.models.Download.Info(
            url=_media.request_url,
            found_file="webm",
            found_type="video",
            preferred_type=request.preferred_type,
            preferred_file=request.preferred_file
        )
    )

    



if __name__ == "__main__":
    data= bytearray()
    with request.ses.open(request=req) as response:
        while True:
            chunk = response.read(8192)

            if not chunk:
                break
            data.extend(chunk)

    parts = core.download.UMP.download._parseUMP(data)
    chunks = core.download.UMP.download.extractUMPChunks(parts)

    
    with open("test_audio.webm", "wb") as f:
        f.write(chunks[0])
        f.write(chunks[2])
        f.write(chunks[5])

    with open("test_video.mp4", "wb") as f:
        f.write(chunks[1])
        f.write(chunks[3])
        f.write(chunks[4])
        f.write(chunks[6])
        f.write(chunks[7])




def getMediaInformationMusic(
    request: models.ProviderResultRequest,
    retrys: int = 3
) -> models.ProviderResult:


    core.general.Validate.general.validateGeneralType(
        argument_name="request",
        obj=request,
        objType=models.ProviderResultRequest,
        caller="Youtube.getMediaInformationMusic"
    )
    core.general.Validate.general.validateInt(
        argument_name="retrys",
        integer=retrys,
        caller="Youtube.getMediaInformationMusic"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=[
            "music.youtube.com",
        ],
        caller="[providers] Youtube.getMediaInformationMusic"
    )

    googleVideoMediaList: list[core.models.media.Media2] = []


    def _getMedia(Browser):

        Browser.run(headless=False)
        mediaList, unknownList = Browser.stop()
        

        bad_keywords = (
        "ctier=l",
        "pcm2cms=yes",
        "ms=aub",
        "rms=aub",
    )   

        for _media in mediaList:
            _media: core.models.media.Media2
            if any(
                keyword in _media.response_url.lower() for keyword in bad_keywords
            ):
                continue

            if "googlevideo.com/videoplayback" in _media.response_url:
                googleVideoMediaList.append(_media)

    
        for _media in unknownList:
            if any(
                keyword in _media.response_url.lower() for keyword in bad_keywords
            ):
                continue
            if "googlevideo.com/videoplayback" in _media.response_url:
               googleVideoMediaList.append(_media)

        
    retry: int = 0
    Browser = browser.MediaBrowser(request.url)

    while retry <= retrys:
        if googleVideoMediaList:
            break
        print(f"[providers] Youtube.getMEdiaInformationMusic: Trying to get media. Try: {retry}/{retrys}")
        retry += 1
        _getMedia(Browser)
    

    if not googleVideoMediaList:
        raise core.models.errors.TaskFailedError(
            task="[providers] Youtube.getMediaInformationMusic",
            reason="Couldn't find valid url",
            caller="[providers] Youtube.getMediaInformationMusic"
        )

    bestMedia: core.models.media.Media2 = None
    bestPrio : int = -1
    bestItagType: str = ""

    for media in googleVideoMediaList:

        parsedUrl = urllib.parse.urlparse(media.response_url)

        query = urllib.parse.parse_qs(
            parsedUrl.query,
            keep_blank_values=True
        )
        itag = query.get("itag")[0]

        prio:int = ITAG_PRIORITY.get(itag, 0)
        itagType: str = ITAG_RESOLVE_TYPE.get(itag, "video-only")
        

        if request.preferred_type == itagType:
            prio += 100
        if prio > bestPrio:
            bestMedia = media
            bestPrio = prio
            bestItagType = itagType
        

    if bestMedia is None:
        raise core.models.errors.TaskFailedError(
            task="[providers] Youtube.getMediaInformationMusic",
            reason="Couldn't select a valid media",
            caller="[providers] Youtube.getMediaInformationMusic"
        )

    resolvedUrl = bestMedia.response_url

    parsedUrl = urllib.parse.urlparse(resolvedUrl)

    query = urllib.parse.parse_qs(
        parsedUrl.query,
        keep_blank_values=True
    )


    # ---------------------------------------------------------
    # Bandaid:
    # UMP needs a valid byte range.
    # If browser discovery caught playback in the middle,
    # force an initial range so we get the WebM header.
    # ---------------------------------------------------------

    current_range = query.get("range", [None])[0]

    if current_range:
        try:
            range_start = int(
                current_range.split("-", 1)[0]
            )
        except (ValueError, IndexError):
            range_start = None

        if range_start is not None and range_start != 0:
            print(
                f"[Youtube] UMP candidate starts at "
                f"{range_start}, forcing initial range"
            )

            query["range"] = ["0-64000"]

            resolvedUrl = urllib.parse.urlunparse(
            parsedUrl._replace(
                query=urllib.parse.urlencode(
                    query,
                    doseq=True
                )
            )
        )

    # URL nach eventuellem Bandaid erneut parsen
    parsedUrl = urllib.parse.urlparse(resolvedUrl)
    query = urllib.parse.parse_qs(parsedUrl.query)

    maxSize = int(query["clen"][0])


    parsedUrl = urllib.parse.urlparse(bestMedia.response_url)

    query = urllib.parse.parse_qs(
        parsedUrl.query,
        keep_blank_values=True
    )
    maxSize = query.get('clen')[0]

    mimeType = query.get("mime", [None])[0]

    if mimeType is None:
        mimeType = (
            media.response_headers
            .get("content-type", "")
            .split(";", 1)[0]
            .strip()
            .lower()
        )

    file_ending = models.CONTENT_TYPE_EXTENSIONS.get(
        mimeType
    )

    mediaType = None

    if mimeType:
        if mimeType.startswith("audio/"):
            mediaType = "audio"
        elif mimeType.startswith("video/"):
            mediaType = "video"


    if not file_ending:
        file_ending = "webm"
    

    result = models.ProviderResult(
        url=resolvedUrl,

        download_type=(
            core.models.Download.DownloadType.UMP
        ),

        extra_headers=media.request_headers,

        file_ending=file_ending,
        media_type=mediaType,
        mime_type=mimeType,

        total_size=int(maxSize)
            if maxSize is not None
            else 0,

        info=core.models.Download.Info(
            url=resolvedUrl,
            preferred_type=request.preferred_type,
            found_type=bestItagType,
            preferred_file=request.preferred_file,
            found_file=file_ending
        )

    )

    return result

    



#def download(
#        download_information: core.models.General.DownloadInformations,
#        
#):
#    core.general.Validate.validateDownloadInformation(
#        argument_name="download_information",
#        download_information=download_information,
#        caller="[providers] Youtube.download"
#    )
#    core.general.Validate.validateHostPro(
#        url=download_information.url,
#        allowed_hostnames_list=["youtube.com", "www.youtube.com", "142.251.141.14"],
#        caller="[providers]: Youtube.download"
#        )
#   

#    ydl_opts = {
#        # best video + best audio, fallback auf fertige mp4
#        "format": "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[ext=mp4]/b",
#        "outtmpl": download_information.outFile,
#        "merge_output_format": "mp4",
#        "progress_hooks": [_buildProgressHook(download_information.downloadProgress)],

        # Sehr hilfreich bei YouTube-Problemen
#        "cookiesfrombrowser": ("firefox",),

        # Nur das einzelne Video, nicht versehentlich Playlist
#        "noplaylist": True,

        # Robuster
#        "retries": 10,
#        "fragment_retries": 10,
#        "socket_timeout": 30,

        # Gut zum Debuggen bei Problemen
#        "verbose": True,

        # ffmpeg Postprocessing
#        "postprocessors": [{
#            "key": "FFmpegVideoConvertor",
#            "preferedformat": "mp4",
#        }],
#    }

#    ffmpeg = find_ffmpeg()
#    if ffmpeg:
#        ydl_opts["ffmpeg_location"] = ffmpeg

#    download_information.downloadProgress['status'] = "downloading..."
#    download_information.downloadProgress['filename'] = download_information.outFile
#    with YoutubeDL(ydl_opts) as ydl:
#        ydl.download([download_information.url])

#    download_information.downloadProgress['status'] = "complete"    
    



def _buildProgressHook(progress_dict: dict):
    def progress_hook(d: dict):
        status = d.get("status")

        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            speed = d.get("speed")

            progress_dict["status"] = "downloading"
            progress_dict["downloadedBytes"] = downloaded
            progress_dict["totalBytes"] = total

            if total:
                progress_dict["downloadProgress"] = int(downloaded / total * 100)
            else:
                progress_dict["downloadProgress"] = 0

            if speed:
                progress_dict["speed"] = round(speed / 1024 / 1024, 2)
            else:
                progress_dict["speed"] = None

        elif status == "finished":
            progress_dict["status"] = "complete"
            progress_dict["downloadProgress"] = 100

        elif status == "error":
            raise YoutubeDownloadError("YOUTUBE_DOWNLOAD: an error occurred while downloading")
    

    return progress_hook