#Core Imports
#Own imports
#Python default imports

def getHtml(
        session = None,
        url: str = None,
        encoding: str = "utf-8",
        extra_headers: dict = None,
        chunk_size = 8096,

)-> str | None:
    from ..general import Validate

    Validate.special.validateSession(session=session, caller="[CORE] getHtml")
    Validate.special.validateEncoding(encoding=encoding, argument_name="encoding", caller="[CORE] getHtml")
    Validate.general.validateInt(argument_name="chunk_size", integer=chunk_size, caller="[CORE] getHtml")

    if extra_headers:
        Validate.general.validateDict(argument_name="extra_headers", dictionary=extra_headers, caller="[CORE] getHtml")

    Validate.special.validateHostDefault(url=url, caller="[CORE] getHtml")
    
    
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