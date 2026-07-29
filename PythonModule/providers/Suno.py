import urllib.request, urllib.error, urllib.parse
import re, os
import time
import PythonModule.core as core


class SunoError(Exception): ...

class SunoNotEnoughArguments(SunoError): ...

class SunoInvalidType(SunoError): ...

class SunoNotFound(SunoError): ...











def search_media(
        html: str,
        mediatype: str = ".mp4",
        identifier: str = None
) -> str:
    wav = None
    if not html:
        raise SunoNotEnoughArguments("No html to search was given")
    
    
    if not identifier:
        raise SunoNotEnoughArguments("No identifier was given")
    
    if mediatype == ".wav":
        wav = ".wav"
        mediatype = ".mp3"

    media = f"https://cdn1.suno.ai/{identifier}{mediatype}"
    
    match = re.search(fr"{media}", html, re.DOTALL)
    
    if not match:
        raise SunoNotFound(f"Didn't find media {media}")
    song_url = match.group(0)
    if wav is not None:
        song_url.replace(".mp3", ".wav")
    return song_url




def search_creator(
        creator_name: str,
        session = None
        ):
    if not creator_name:
        raise SunoNotEnoughArguments("No creator name was given")
    if not creator_name.startswith("@"):
        creator_name = "@" + creator_name
    if not session:
        raise SunoNotEnoughArguments("No session was given")


    url = f"https://suno.com/{creator_name}"

    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        )
    
    try:
        with session.open(request=request) as response:
            html = response.read(1024 * 512).decode("utf-8")
            return html
        

    except urllib.error.HTTPError as e:
        raise urllib.error.HTTPError(f"HTTP Error {e}")
    
    except urllib.error.URLError as e:
        raise urllib.error.URLError(f"URL ERROR {e}")
    






def download (
        url: str,
        session,
        out_file: str,
        mediatype = ".mp3",
        progress_dict: dict = None,
        
        
        
):

    if not url: 
        raise SunoNotEnoughArguments("No url was given!")
    if not session:
        raise SunoNotEnoughArguments("No session was given")
    if not progress_dict:
        raise SunoNotEnoughArguments("No progress dict was given")
    

    html = core.general.Html.getHtml(url=url, session=session)

    strip = url.replace("https://suno.com/song/", "")
    identifier = strip

    file = search_media(html=html, identifier=identifier, mediatype=mediatype)
    if os.path.exists(out_file):
        raise SunoError(f"Destination out file {out_file} already exists. No Download has started")

    
    core.download.File._downloadToFile(url=file, out_file=out_file, session=session, progress_dict=progress_dict)

