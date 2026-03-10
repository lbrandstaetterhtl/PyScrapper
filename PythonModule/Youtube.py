import urllib.parse, urllib.request, urllib.error
import http.cookiejar
import json
import re
from yt_dlp import YoutubeDL
import re
import os
import shutil
import pathlib


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
        session: http.cookiejar.CookieJar = None,
        top:int = 5
        
        ) -> list[dict]:
    
    if not search:
        raise NoSearchError("YOUTUBE_SEARCH: No search was given")
    if not session:
        raise SessionError("YOUTUBE_SEARCH: No session was given")


    try:
        top = int(top)
    except (TypeError, ValueError) as e:
         raise ValueError(f"YOUTBE_SEARCH: Top variable must be an integer {e}") from e
    
    if top <= 0:
        raise ValueError("YOUTUBE_SEARCH: 'Top' variable must be greater than 0")
    


    search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(search)

    request = urllib.request.Request(
            search_url,
            method='GET',
            headers={"User-Agent": "Mozilla/5.0"}
        )


    html:str = get_html(request, session=session)
    jsondata: dict = search_json(html=html, keyword="var ytInitialData = ")


    Data = []
    for videorenderer in iter_value_from_json(jsondata, "videoRenderer"):
        if not isinstance(videorenderer, dict):
            continue

        video = videorenderer.get("videoId")
        if not video:
            continue
        dictionary = {"videoId": video}
        


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





def get_html(
        request:urllib.request.Request,
        session: http.cookiejar.CookieJar = None,
        decode:str = "utf-8"
        
        ) -> str:
    if not session:
        raise SessionError("GET_HTML: No session was given")

    try:
        with session.open(request) as response:
            final_url = response.geturl()
            html = response.read().decode(decode)
            low = html.lower()


            #if "consent.youtube.com" in final_url or "consent.youtube.com" in low or "before you continue to youtube" in low:
            #   raise SessionError("Consent page detected, cannot proceed with request. Please ensure that the session has the necessary cookies to bypass the consent")
            
    
    except urllib.error.HTTPError as e:
        raise urllib.error.HTTPError(e.url, e.code, f"Failed to get request - {e.reason}", e.headers, e.fp) from e

    except urllib.error.URLError as e:
        raise urllib.error.URLError(f"GET_HTML: Failed to get request - {e}") from e

    except UnicodeDecodeError as e:
        raise UnicodeError(f"GET_HTML: Failed to decode the HTML - {e}") from e
   

    if not html:
        raise urllib.error.URLError("GET_HTML: Failed to get request - HTML")


    return html





def search_json(
        html: str,
        keyword: str
        ) -> dict:
    

    found = re.search(keyword + r"({.*?});", html, re.DOTALL)

    if not found:
        raise NoSearchError("SEARCH_JSON: Failed to find the json data")
    
    try:    
        jsondata = json.loads(found.group(1))

    except json.JSONDecodeError:
        raise NoSearchError("SEARCH_JSON: Failed to decode the JSON data")


    return jsondata





def iter_value_from_json(
        data: dict,
        value: str
):
    if isinstance(data, dict):
        if value in data:
            yield data[value]

        for key in data:
            yield from iter_value_from_json(data[key], value)


    elif isinstance(data, list):
        for item in data:
            yield from iter_value_from_json(item, value)


def download_audio_only(
        url: str,
        out_path: str,
        progress_dict: dict

        ):
    if not url:
        raise YoutubeArgumentError("YOUTUBE_DOWNLOAD_AUDIO: No URL was given for download")
    if not out_path:
        raise YoutubeArgumentError("YOUTUBE_DOWNLOAD_AUDIO: No download path was given")

    identifier = url.replace("https://www.youtube.com/watch?v=", "")
    out_file = os.path.join(out_path, f"{identifier}")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_file,
        "progress_hooks": [build_progress_hook(progress_dict)],
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
    progress_dict['filename'] = out_file


def download(
        url: str,
        out_path: str,
        progress_dict: dict
):
    if not url:
        raise YoutubeArgumentError("YOUTUBE_DOWNLOAD: No URL was given for download")
    if not out_path:
        raise YoutubeArgumentError("YOUTUBE_DOWNLOAD: No path to download to was given")
    if not progress_dict:
        raise YoutubeArgumentError("YOUTUBE_DOWNLOAD: No progress dict was given")

 
    identifier = url.replace("https://www.youtube.com/watch?v=", "")
    out_file = os.path.join(out_path, f"{identifier}.mp4")
    if os.path.exists(out_file):
        raise YoutubeDownloadError(f"Destination out file {out_file} already exists. No Download has started")


    ydl_opts = {
#bv = best video, ba = best audio
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": out_file,
        "restrictfilenames": True,
        "merge_output_format": "mp4",
        "progress_hooks": [build_progress_hook(progress_dict)],
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }],


    }

    ffmpeg = find_ffmpeg()
    if ffmpeg:
        ydl_opts["ffmpeg_location"] = ffmpeg

    progress_dict['status'] = "downloading..."
    progress_dict['filename'] = out_file
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    progress_dict['status'] = "complete"    
    




def build_progress_hook(progress_dict: dict):
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
            progress_dict["status"] = "processing"
            progress_dict["downloadProgress"] = 100

        elif status == "error":
            raise YoutubeDownloadError("YOUTUBE_DOWNLOAD: an error occured while downloading")
    

    return progress_hook