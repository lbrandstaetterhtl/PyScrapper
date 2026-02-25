import urllib.request, urllib.error, urllib.parse
import re, os



class SunoError(Exception): ...

class SunoNotEnoughArguments(SunoError): ...

class SunoInvalidType(SunoError): ...

class SunoNotFound(SunoError): ...





def get_html(
        session = None,
        url: str = None,
        decode: str = "utf-8"
)-> str:
    
    if not url:
        raise SunoNotEnoughArguments("No URL was given")
    if not session:
        raise SunoNotEnoughArguments("No Session was given")
    
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        )


    try:
        with session.open(request) as response:
            Bytes = response.read(1024 * 512)
            html = Bytes.decode(decode)
            return html

    except urllib.error.HTTPError as e:
        raise urllib.error.HTTPError(f"HTTP Error {e}")
    
    except urllib.error.URLError as e:
        raise urllib.error.URLError(f"URL ERROR {e}")
    
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Failed to decode with given decode standard {decode}")





def search_media(
        html: str,
        mediatype: str = ".mp4",
        identifier: str = None
) -> str:
    wav = None
    if not html:
        raise SunoNotEnoughArguments("No html to search was given")
    
    if mediatype not in (".mp3", ".mp4", ".wav"):
        raise SunoInvalidType("Invalid type for media")
    
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
        with session.open(request) as response:
            html = response.read(1024 * 512).decode("utf-8")
            return html
        

    except urllib.error.HTTPError as e:
        raise urllib.error.HTTPError(f"HTTP Error {e}")
    
    except urllib.error.URLError as e:
        raise urllib.error.URLError(f"URL ERROR {e}")
    

def download_to_file(
        url: str,
        out_file: str,
        session = None,
        chunk_size: int = 1024 * 512,

        
):
    if not url:
        raise SunoNotEnoughArguments("No url was given")
    if not out_file:
        raise SunoNotEnoughArguments("Not enough arguments were given")
    if not session:
        raise SunoNotEnoughArguments("No session was given")

    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        )

    try:
        with session.open(request) as response, open(out_file, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)

    except urllib.error.HTTPError as e:
        raise urllib.error.HTTPError(f"HTTP Error {e}")
    
    except urllib.error.URLError as e:
        raise urllib.error.URLError(f"URL ERROR {e}")
    




def download (
        url: str,
        session,
        out_path: str = os.path.join("downloads"),
        mediatype = ".mp3",
        
):
    if mediatype not in (".mp3", ".mp4", ".wav"):
        raise SunoInvalidType(f"invalid type {mediatype}, use .mp3, .mp4 or .wav")
    if not url: 
        raise SunoNotEnoughArguments("No url was given!")
    if not session:
        raise SunoNotEnoughArguments("No session was given")
    
    os.makedirs(out_path, exist_ok=True)

    html = get_html(url=url, session=session)

    strip = url.replace("https://suno.com/song/", "")
    identifier = strip

    file = search_media(html=html, identifier=identifier, mediatype=mediatype)
    out_file = os.path.join(out_path, f"{identifier}{mediatype}")

    download_to_file(url=file, out_file=out_file, session=session)

    dictionary = {
        "Status": "Download complete",
        "File": out_file
    }
    return dictionary