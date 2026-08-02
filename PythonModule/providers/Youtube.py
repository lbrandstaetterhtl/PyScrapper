import urllib.parse
from yt_dlp import YoutubeDL
import os
import shutil
import pathlib
import PythonModule.core as core
from PythonModule.models import processorModels
from PythonModule.models.requests import SearchFilters


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
        search:str,
        filters: SearchFilters,
        session: core.request.Session.Session,
        top:int = 5
        
        ) -> list[dict]:
    
    if not search or not isinstance(search, str):
        raise NoSearchError("YOUTUBE_SEARCH: No search was given or invalid type was given")
    if not session or not isinstance(session, core.request.Session.Session):
        raise SessionError("YOUTUBE_SEARCH: No session was given or unsupported type of sessio")
    if not isinstance(filters, SearchFilters): raise ValueError("'filters' must be from type SearchFilters")
    if not isinstance(top, int) or top < 0: raise ValueError("'top' must be an integer above 0")

    try:
        top = int(top)
    except (TypeError, ValueError) as e:
         raise ValueError(f"YOUTBE_SEARCH: Top variable must be an integer {e}") from e
    
    if top <= 0:
        raise ValueError("YOUTUBE_SEARCH: 'Top' variable must be greater than 0")
    


    search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(search)

    


    html:str = core.general.Html.getHtml(
        url=search_url,
        session=session
        )
    jsondata: dict = core.general.DataSearch.searchJson(searchBlock=html, keyword="var ytInitialData = ")


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



def download_audio_only(
        url: str,
        out_file: str,
        progress_dict: dict,
        
    ):

    if not url:
        raise YoutubeArgumentError("YOUTUBE_DOWNLOAD_AUDIO: No URL was given for download")
    if not out_file:
        raise YoutubeArgumentError("YOUTUBE_DOWNLOAD_AUDIO: No out_file was given")

    identifier = url.replace("https://www.youtube.com/watch?v=", "")
    

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_file,
        "progress_hooks": [_buildProgressHook(progress_dict)],
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    ffmpeg = find_ffmpeg()
    if ffmpeg:
        ydl_opts["ffmpeg_location"] = ffmpeg

    progress_dict['status'] = "downloading..."
    
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    progress_dict['status'] = "complete"






def download(
        download_information: processorModels.DownloadInformations,
        
):
    if not download_information or not isinstance(download_information, processorModels.DownloadInformations): raise ValueError("YoutubeDownload: Given download informations is either None or has the wrong type")

    #identifier = url.replace("https://www.youtube.com/watch?v=", "")
   
    if os.path.exists(download_information.outFile):
        raise YoutubeDownloadError(f"Destination out file {download_information.outFile} already exists. No Download has started")


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