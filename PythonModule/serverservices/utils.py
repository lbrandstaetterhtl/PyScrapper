from PythonModule.models import settings
from PythonModule.models.exceptions import InvalidMediaType, NotSupportedProvider
import urllib.error, urllib.request
import os
import asyncio

def validateProviders(
          providerGiven: str
):
    for providerType, aliases in settings.SUPPORTEDPROVIDERS.items():
            if providerGiven.lower() in aliases:
                return providerType
    raise Exception("Invalid provider was given")





def validateMediatype(
          provider: str,
          mediatype: str

):
    mediatype = mediatype.strip()
    if mediatype not in settings.SUPPORTEDFILES[provider]:
        print("Invalid Mediatype")
        raise InvalidMediaType(mediatype, provider, supported=settings.SUPPORTEDFILES[provider])
    



    

def make_out_file(
        out_path: str,
        filename: str,
        mediatype: str
) -> str:
    if not isinstance(out_path, str): raise ValueError("Out path must be a string")
    if not isinstance(filename, str): raise ValueError("filename must be a string")
    if not isinstance(mediatype, str): raise ValueError("mediatype must be a string")

    os.makedirs(out_path, exist_ok=True)
    if not mediatype.startswith("."):
         mediatype = f".{mediatype}"
    out_file = os.path.join(out_path, f"{filename}{mediatype}")
    if os.path.exists(out_file):
         raise Exception(f"Destination path {out_file} already exists")

    return out_file

async def cleanup_progress(
        task_id: str,
        download_progess:dict,
        delay: int = 60
          
        ):
    await asyncio.sleep(delay)
    progress:dict = download_progess.get(task_id)
    if progress and progress.get("status") in ("complete", "error"):
         
        download_progess.pop(task_id)


def addpointtomediatype(
        mediatype: str
) -> str:
    if not isinstance(mediatype, str): raise ValueError("Please give mediatype from type string")

    mediatype = mediatype.strip()
    if not mediatype.startswith("."):
         mediatype = f".{mediatype}"
    return mediatype
    