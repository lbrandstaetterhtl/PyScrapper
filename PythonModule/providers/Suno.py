import urllib.request, urllib.error, urllib.parse
import PythonModule.core as core
import os, re
from PythonModule.models import processorModels

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
        download_information: processorModels.DownloadInformations,
        
        
        
):
    if not download_information or not isinstance(download_information, processorModels.DownloadInformations): raise ValueError("BandcampDownload: Given download information is either None or has the wrong type")
    

    html = core.general.Html.getHtml(url=download_information.url, session=download_information.session)

    strip = download_information.url.replace("https://suno.com/song/", "")
    identifier = strip

    file = search_media(html=html, identifier=identifier, mediatype=download_information.fileending)
    if os.path.exists(download_information.outFile):
        raise SunoError(f"SunoDownload: Destination out file {download_information.outFile} already exists. No Download has started")

    
    core.download.File._downloadToFile(
        url=file, out_file=download_information.outFile,
        session=download_information.session,
        progress_dict=download_information.downloadProgress
        )

