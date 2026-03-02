import urllib.parse, urllib.request, urllib.error
import http.cookiejar
import json
import re
from yt_dlp import YoutubeDL
import re
import os
#FFMPEG MUST BE INSTALLED FOR DOWNLOAD TO WORK


class NoSearchError(Exception): ...

class SignaturCipherError(Exception): ...

class SessionError(Exception): ...

class YoutubeArgumentError(Exception): ...


def search(
        search:str,
        session: http.cookiejar.CookieJar = None,
        top:int = 5
        
        ) -> list[dict]:
    
    if not search:
        raise NoSearchError("No search was given")
    if not session:
        raise SessionError("No session was given")


    try:
        top = int(top)
    except (TypeError, ValueError) as e:
         raise ValueError(f"Top variable must be an integer {e}") from e
    
    if top <= 0:
        raise ValueError("'Top' variable must be greater than 0")
    


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
        raise SessionError("No session was given")

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
        raise urllib.error.URLError(f"Failed to get request - {e}") from e

    except UnicodeDecodeError as e:
        raise UnicodeError(f"Failed to decode the HTML - {e}") from e
   

    if not html:
        raise urllib.error.URLError("Failed to get request - HTML")


    return html





def search_json(
        html: str,
        keyword: str
        ) -> dict:
    

    found = re.search(keyword + r"({.*?});", html, re.DOTALL)

    if not found:
        raise NoSearchError("Failed to find the json data")
    
    try:    
        jsondata = json.loads(found.group(1))

    except json.JSONDecodeError:
        raise NoSearchError("Failed to decode the JSON data")


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

        ):
    if not url:
        raise YoutubeArgumentError("No URL was given for download")
    if not out_path:
        raise YoutubeArgumentError("No download path was given")

    identifier = url.strip("https://www.youtube.com/watch?v=")
    out_file = os.path.join(out_path, f"{identifier}")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_file,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


    dictionary = {
        "status": "Download complete",
        "file": out_file
    }
    return dictionary, identifier


def download(
        url: str,
        out_path: str,
):
    if not url:
        raise YoutubeArgumentError("No URL was given for download")
    if not out_path:
        raise YoutubeArgumentError("No path to download to was given")

    
    identifier = url.strip("https://www.youtube.com/watch?v=")
    out_file = os.path.join(out_path, f"{identifier}.mp4")

    ydl_opts = {
#bv = best video, ba = best audio
        "format": "bv*+ba/b",
        "outtmpl": out_file,
        "merge_output_format": "mp4",

    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    dictionary = {
        "status": "Download complete",
        "file": out_file
    }    
    return dictionary, identifier
        