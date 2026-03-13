import urllib.error, urllib.request

class ArgumentError(Exception): ...

def get_html(
        session = None,
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
        with session.open(request) as response:
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
    
