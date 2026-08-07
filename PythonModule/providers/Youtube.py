#Core Imports
import PythonModule.core as core

#PythonModule imports
from PythonModule.models.requests import SearchFilters

#Python Default Imports
import os
import shutil
import pathlib
import urllib.parse

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
        session: core.request.Session.Session,
        top:int = 5
        
        ) -> list[dict]:

    core.general.Validate.validateStr(argument_name="search_term", string=search_term, caller="[providers] Youtube.search")
    core.general.Validate.validateSession(session=session, caller="[providers] Youtube.search")
    core.general.Validate.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters, caller="[providers] Youtube.search")
    core.general.Validate.validateInt(argument_name="top", integer=top, caller="[providers] Youtube.search") 


    search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(search_term)


    html:str = core.general.Html.getHtml(
        url=search_url,
        session=session
        )
    core.general.Validate.validateStr(argument_name="html", string=html, caller="[providers] Youtbe.search.getHtml")
    
    
    keyword = "var ytInitialData = "

    jsondata: dict = core.general.DataSearch.searchJson(searchBlock=html, keyword=keyword)

   
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





def download(
        download_information: core.models.General.DownloadInformations,
        
):
    core.general.Validate.validateDownloadInformation(
        argument_name="download_information",
        download_information=download_information,
        caller="[providers] Youtube.download"
    )
    core.general.Validate.validateHostPro(
        url=download_information.url,
        allowed_hostnames_list=["youtube.com", "www.youtube.com", "142.251.141.14"],
        caller="[providers]: Youtube.download"
        )
   

    ydl_opts = {
        # best video + best audio, fallback auf fertige mp4
        "format": "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[ext=mp4]/b",
        "outtmpl": download_information.outFile,
        "merge_output_format": "mp4",
        "progress_hooks": [_buildProgressHook(download_information.downloadProgress)],

        # Sehr hilfreich bei YouTube-Problemen
        "cookiesfrombrowser": ("firefox",),

        # Nur das einzelne Video, nicht versehentlich Playlist
        "noplaylist": True,

        # Robuster
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,

        # Gut zum Debuggen bei Problemen
        "verbose": True,

        # ffmpeg Postprocessing
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }],
    }

    ffmpeg = find_ffmpeg()
    if ffmpeg:
        ydl_opts["ffmpeg_location"] = ffmpeg

    download_information.downloadProgress['status'] = "downloading..."
    download_information.downloadProgress['filename'] = download_information.outFile
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([download_information.url])

    download_information.downloadProgress['status'] = "complete"    
    



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