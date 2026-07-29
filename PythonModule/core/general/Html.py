from ..models.errors import ArgumentError
from ..request.Session import Session
import urllib.request, urllib.error, urllib.parse
import json

def loadJSONUrl(
        request,
        session: Session,
        encoding="utf-8",

) -> str | None:

    
    if not isinstance(request, urllib.request.Request): raise ValueError("loadJSONUrl: Invalid request was given")
    if not isinstance(session, Session): raise ValueError("loadJSONUrl: Invalid session was given")

    with session.open(request=request) as response:
        raw = response.read()
        text = raw.decode(encoding)
        jsonData = json.loads(text)

    
    return jsonData if jsonData else None
    

def getHtml(
        session:Session = None,
        url: str = None,
        decode: str = "utf-8",
        chunk_size = 8096

)-> str:
    
    if not url:
        raise ArgumentError("No URL was given")
    if not session:
        raise ArgumentError("No Session was given")
    
    request = urllib.request.Request(
        url,
        method="GET",
    )


    try:
        with session.open(request=request) as response:
            chunks = []
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
            
#the b"" for the join is used so we can python it is Bytes we are dealing with            
            html = b"".join(chunks).decode(decode)
            return html

    except urllib.error.HTTPError as e:
        raise
    
    except urllib.error.URLError as e:
        raise
    
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Failed to decode with given decode standard {decode}")