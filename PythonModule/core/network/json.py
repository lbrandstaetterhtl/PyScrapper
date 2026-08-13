# core imports
from ..general import Validate

#own imports

#python default imports
import json


def loadJSONUrl(
        url: str,
        session,
        encoding="utf-8",
        extra_headers:dict = None,
   

) -> str | None:
    
    
    Validate.special.validateEncoding(encoding=encoding, caller="[CORE] loadJSONUrl")
    Validate.special.validateSession(session=session, caller="[CORE] loadJSONUrl")

    if extra_headers:
        Validate.general.validateDict(argument_name="extra_headers", dictionary=extra_headers, caller="[CORE] loadJSONUrl")
    Validate.special.validateHostDefault(url, caller="[CORE] loadJSONUrl")

    with session.open(url=url, headers=extra_headers) as response:
        raw = response.read()
        text = raw.decode(encoding)
        jsonData = json.loads(text)

    
    return jsonData if jsonData else None