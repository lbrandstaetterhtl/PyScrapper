#Core Imports
import PythonModule.core as core
from PythonModule.core.network import html
from PythonModule.core.network.Session import Session
from PythonModule.core.network import EmergencyBrowser

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


class NoSearchError(Exception): ...

class SignaturCipherError(Exception): ...

class SessionError(Exception): ...

class YoutubeArgumentError(Exception): ...

class YoutubeDownloadError(Exception): ...



def search(
        search_term:str,
        filters: SearchFilters,
        session: Session,
        top:int = 5
        
        ) -> list[dict]:

    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Youtube.search")
    core.general.Validate.special.validateSession(session=session, caller="[providers] Youtube.search")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters, caller="[providers] Youtube.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Youtube.search") 


    search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(search_term)


    searchHtml:str = html.getHtml(
        url=search_url,
        session=session
        )
    core.general.Validate.general.validateStr(argument_name="searchHtml", string=searchHtml, caller="[providers] Youtbe.search.getHtml")
    
    
    keyword = "var ytInitialData = "

    jsondata: dict = core.general.DataSearch.searchJson(searchBlock=searchHtml, keyword=keyword)

   
    if not jsondata:
        raise core.models.errors.TaskFailedError(
            task="[CORE] searchJson",
            reason=f"Didn't find data with keyword {keyword}"
        )


    Data = []

    for videorenderer in core.general.DataSearch.iterValueFromJson(jsondata, "videoRenderer"):
        if not isinstance(videorenderer, dict):
            continue

        video = videorenderer.get("videoId")
        if not video:
            continue
        dictionary = {"identifier": video}
        


        if video:
            dictionary["url"] = "https://www.youtube.com/watch?v=" + video


        thumbnail = videorenderer.get("thumbnail", {}).get("thumbnails", [])
        if thumbnail:
            for obj in thumbnail:
                thumb_url = obj.get("url", None)
                if thumb_url:
                    dictionary["thumbnail"] = thumb_url
                    break
                
        
        title = videorenderer.get("title", {}).get("runs", [])
        if title:
            for obj in title:
                text = obj.get("text", None)
                if text:
                    dictionary["title"] = text
                    break


        Data.append(dictionary)


        if len(Data) == top:
            break


    return Data


import json
import re
import urllib.parse
import urllib.request


import urllib.parse
from playwright.sync_api import sync_playwright


WEB_SAFARI_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/15.5 Safari/605.1.15"
)


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
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request",
        obj=request,
        objType=models.ProviderResultRequest,
        caller="Youtube.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=[
            "youtube.com",
            "www.youtube.com",
        ],
        caller="[providers] Youtube.getMediaInformation"
    )

    ydl_opts = {
        "quiet": True,
        "skip_download": True,

        "cookiefile": request.ses.cookieFile,

        "extractor_args": {
                    "youtube": {
                        "player_client": [
                            "default",
                            "android_vr",
                            "web_safari",
                        ]
                    }
                },
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            request.url,
            download=False
        )

    formats = info.get("formats", [])

    usable_formats = []

    for fmt in formats:

        media_url = fmt.get("url")
        extension = fmt.get("ext")

        if not media_url:
            continue

        if extension not in (
            "mp4",
            "webm",
            "m4a",
            "mp3",
            "ogg",
            "opus",
        ):
            continue

        # SABR URLs wollen wir nicht verwenden.
        if "sabr=1" in media_url.lower():
            continue

        usable_formats.append(fmt)

    if not usable_formats:
        raise core.models.errors.TaskFailedError(
            task="Youtube.getMediaInformation",
            reason="yt-dlp returned no usable direct media URL",
            caller="[providers] Youtube.getMediaInformation"
        )

    # ---------------------------------------------------------
    # Gute Formate zuerst ausprobieren
    # ---------------------------------------------------------

    def formatScore(fmt: dict) -> tuple:

        hasVideo = (
            fmt.get("vcodec") is not None
            and fmt.get("vcodec") != "none"
        )

        hasAudio = (
            fmt.get("acodec") is not None
            and fmt.get("acodec") != "none"
        )

        hasVideoAndAudio = hasVideo and hasAudio

        return (
            hasVideoAndAudio,
            fmt.get("height") or 0,
            fmt.get("tbr") or 0,
            fmt.get("abr") or 0,
        )

    usable_formats.sort(
        key=formatScore,
        reverse=True
    )

    # ---------------------------------------------------------
    # Formate der Reihe nach testen
    # ---------------------------------------------------------

    for fmt in usable_formats:

        media_url = fmt["url"]
        extra_headers = fmt.get("http_headers") or {}

        try:
            print(
                "[Youtube] Trying format:",
                fmt.get("format_id"),
                fmt.get("ext"),
                fmt.get("height"),
                fmt.get("vcodec"),
                fmt.get("acodec"),
            )

            print(f"[Youtube] now trying url: {media_url}")
            fileType = models.getContentType(
                url=media_url,
                session=request.ses,
                extra_headers=extra_headers
            )
            total_size = models.getFileInformations(
                url=media_url,
                session=request.ses,
                extra_headers=extra_headers
            )

            print(
                "[Youtube] Successfully selected format:",
                fmt.get("format_id"),
                fileType
            )

            return models.ProviderResult(
                url=media_url,

                download_type=(
                    core.models.Download.DownloadType.FILE
                ),

                extra_headers=extra_headers,

                file_type=fileType,
                total_size=total_size
            )

        except Exception as error:

            print(
                "[Youtube] Format failed:",
                fmt.get("format_id"),
                str(error)
            )


            continue



    raise core.models.errors.TaskFailedError(
        task="Youtube.getMediaInformation",
        reason=(
            "yt-dlp returned formats, but none of the "
            "direct media URLs could be used"
        ),
        caller="[providers] Youtube.getMediaInformation"
    )





def _getMusicClientVersion(session: Session) -> str:
    url = "https://music.youtube.com"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/151.0.0.0 Safari/537.36"
            )
        }
    )

    with session.open(request=req) as response:
        musicHtml: str = response.read().decode("utf-8", errors="replace")
        finalUrl = response.geturl()

    if "consent.youtube.com" in finalUrl or \
       'base href="https://consent.youtube.com/' in musicHtml:
        print("[Youtube] consent site was found, sending emergency browser")
        EmergencyBrowser.BrowserButtonPress(
            url=url,
            button_name="",
            headless=False
        )
        session.reloadCookies()

        test_req = urllib.request.Request(
            "https://music.youtube.com/"
        )

        session.cookieJar.add_cookie_header(test_req)

        print("COOKIE HEADER:")
        print(test_req.get_header("Cookie"))

        with session.open(request=req) as response:
                musicHtml: str = response.read().decode("utf-8", errors="replace")
                finalUrl = response.geturl()

    patterns = [
        r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"',
        r'"innertubeClientVersion":"([^"]+)"',
    ]

    for pattern in patterns:
        clientVersion = core.general.DataSearch.searchBlocks(pattern, musicHtml, return_regex_exception=False)

        if clientVersion:
            return clientVersion

    raise core.models.errors.TaskFailedError(
        task="[providers] Youtube._getMusicClientVersion",
        reason="Couldn't find music client version in html",
        extraMessages=[
            f"Patterns: {', '.join(patterns)}",
            f"Searched html: {musicHtml}"
        ]
    )
        







def getMediaInformationMusic(
    request: models.ProviderResultRequest,
) -> models.ProviderResult:

    print(request)


    core.general.Validate.general.validateGeneralType(
        argument_name="request",
        obj=request,
        objType=models.ProviderResultRequest,
        caller="Youtube.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=[
            "music.youtube.com",
        ],
        caller="[providers] Youtube.getMediaInformation"
    )
    medialist = EmergencyBrowser.BrowserDiscoverStreamURLs(url=request.url, headless=False, ad_block=True)
    candidate = medialist.candidates[0]
    parsedUrl = urllib.parse.urlparse(candidate.mediaUrl)
    query = urllib.parse.parse_qs(parsedUrl.query)

    poToken = query.get("pot", [None])[0]
    print(poToken)

    
    client_version = _getMusicClientVersion(request.ses)
    print(f"[Youtube] Music client version: {client_version}")
    video_id = request.url.split("?v=", 1)[1].split("&")[0]

    

    headers={
            "Content-Type": "application/json",
            "Origin": "https://music.youtube.com",
            "Referer": "https://music.youtube.com/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/151.0.0.0 Safari/537.36"
            )
        }

    body = {
        "context": {
            "client": {
                "clientName": "WEB_REMIX",
                "clientVersion": client_version,
                "hl": "en",
                "gl": "US"
            }
        },
        "videoId": video_id
    }

    data = json.dumps(body).encode("utf-8")

    ytRequest = urllib.request.Request(
        "https://music.youtube.com/youtubei/v1/player?prettyPrint=false",
        data=data,
        headers=headers,
        method="POST"
    )

    with request.ses.open(request=ytRequest) as response:
        raw = response.read()
        jsonData = json.loads(raw.decode("utf-8"))

    print(jsonData)


    

    


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
            raise YoutubeDownloadError("YOUTUBE_DOWNLOAD: an error occured while downloading")
    

    return progress_hook