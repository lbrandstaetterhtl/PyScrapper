#Core Imports
from ..request.Session import Session


#Python Default Imports
import json


def loadJSONUrl(
        url: str,
        session: Session,
        encoding="utf-8",
        extra_headers:dict = None,
   

) -> str | None:
    from . import Validate
    
 
    Validate.validateEncoding(encoding=encoding, caller="[CORE] loadJSONUrl")
    Validate.validateSession(session=session, caller="[CORE] loadJSONUrl")
    if extra_headers:
        Validate.validateDict(argument_name="extra_headers", dictionary=extra_headers, caller="[CORE] loadJSONUrl")
    Validate.validateHostDefault(url, caller="[CORE] loadJSONUrl")

    with session.open(url=url, headers=extra_headers) as response:
        raw = response.read()
        text = raw.decode(encoding)
        jsonData = json.loads(text)

    
    return jsonData if jsonData else None




    

def getHtml(
        session:Session = None,
        url: str = None,
        encoding: str = "utf-8",
        extra_headers: dict = None,
        chunk_size = 8096,

)-> str | None:
    from . import Validate

    Validate.validateSession(session=session, caller="[CORE] getHtml")
    Validate.validateEncoding(encoding=encoding, argument_name="encoding", caller="[CORE] getHtml")
    Validate.validateInt(argument_name="chunk_size", integer=chunk_size, caller="[CORE] getHtml")
    if extra_headers:
        Validate.validateDict(argument_name="extra_headers", dictionary=extra_headers, caller="[CORE] getHtml")

    Validate.validateHostDefault(url=url, caller="[CORE] getHtml")
    
    
    with session.open(url=url, headers=extra_headers) as response:
        chunks = []
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
        
#the b"" for the join is used so we can python it is Bytes we are dealing with            
        html = b"".join(chunks).decode(encoding)
        return html
    
