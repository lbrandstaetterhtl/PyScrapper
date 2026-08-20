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
import re




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


def searchMusic(
    search_term:str,
    filters: SearchFilters,
    session: Session,
    top:int = 5
    
    ) -> list[dict]:

    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Youtube.searchMusic")
    core.general.Validate.special.validateSession(session=session, caller="[providers] Youtube.searchMusic")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters, caller="[providers] Youtube.searchMusic")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Youtube.searchMusic") 

    searchUrl: str = "https://music.youtube.com/search?q=" + urllib.parse.quote(search_term)

    searchHtml = html.getHtml(session=session, url=searchUrl)

    if "consent" in searchHtml:
        EmergencyBrowser.BrowserButtonPress(
            url=searchUrl,
            button_name="",
            headless=False,
            wait_before_click_ms=2000,
            wait_after_click_ms=2000
        )
        session.reloadCookies()
        searchHtml = html.getHtml(session=session, url=searchUrl)

    pattern = (
    r"initialData\.push\(\{"
    r"path: '\\/search',"
    r".*?"
    r"data: '((?:\\.|[^'])*)'"
    r"\}\);"
)
    encodedJson = core.general.DataSearch.searchBlocks(pattern, searchHtml, True)
    decodedJson = re.sub(
        r"\\x([0-9a-fA-F]{2})",
        lambda m: chr(int(m.group(1), 16)),
        encodedJson
    )

    decodedJson = decodedJson.replace(r'\\"', r'\"')

    results: list[dict] = []

    
    jsondata = json.loads(decodedJson)

    

    for musicRenderer in core.general.DataSearch.iterValueFromJson(jsondata, "musicResponsiveListItemRenderer"):
        if len(results) >= top:
            break
        try:
            idk = (
                musicRenderer["flexColumns"][0]
                ["musicResponsiveListItemFlexColumnRenderer"]
                ["text"]
                ["runs"][0]
            )
            title = idk["text"]

            thumbnail = (
            musicRenderer["thumbnail"]
            ["musicThumbnailRenderer"]
            ["thumbnail"]
            ["thumbnails"][-1]
            ["url"]
        )

            videoId = (
            idk["navigationEndpoint"]
            ["watchEndpoint"]
            ["videoId"]
        )

            

        except (KeyError, IndexError, TypeError):
            continue

        result = {
            "identifier" : videoId,
            "url" : f"https://music.youtube.com/watch?v={videoId}",
            "title" : title,
            "thumbnail" : thumbnail
        }

        results.append(result)

    return results
    
    
    

        



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

def getMediaInformation2(
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
    EmergencyBrowser.POTokenBrowser(
        url=request.url,
        headless=False,
    )


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





def getMediaInformationMusic(
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
            "music.youtube.com",
        ],
        caller="[providers] Youtube.getMediaInformation"
    )
    medialist = EmergencyBrowser.BrowserDiscoverStreamURLs(url=request.url, headless=False, ad_block=True)
    candidate = medialist.candidates[0]


    parsedUrl = urllib.parse.urlparse(candidate.mediaUrl)
    query = urllib.parse.parse_qs(parsedUrl.query)
    max_size = query.get('clen')[0]
    

    return models.ProviderResult(
        url=candidate.mediaUrl,
        download_type=core.models.Download.DownloadType.UMP,
        extra_headers=candidate.headers.to_dict(),
        file_type="webm",
        total_size=int(max_size)
    )

    



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