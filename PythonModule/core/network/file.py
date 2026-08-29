

#Core imports
from .Session import Session


from ..models import Download

from ..general import Validate

#Own imports
from . import progress

#Python default imports

import asyncio
import urllib.request




def _validateDownloadToFileArguments(
    url: str,
    session: Session,
    out_file: str,
    extra_headers: dict,
    chunk_size: int,
    open_file_method: str,
    start_byte : int,
    end_byte : int | None 
):
    Validate.special.validateHostDefault(
                url, caller="[CORE] network.file.downloadToFile")
        
    Validate.special.validateSession(
        session, argument_name="session", caller="[CORE] network.file.downloadToFile")

    Validate.download.validateOutFile(
        out_file, caller="[CORE] network.file.downloadToFile", open_method=open_file_method)

    Validate.general.validateInt(
        argument_name="chunk_size", integer=chunk_size, caller="[CORE] network.file.downloadToFile")

    if extra_headers:
        Validate.general.validateDict(
            argument_name="extra_headers", dictionary=extra_headers, caller="[CORE] network.file.downloadToFile")
        
    if (
      
        not isinstance(start_byte, int)
        or not start_byte >= 0  
    ):
        raise ValueError("Startbyte wasn't an integer with value 0 and above")

    if end_byte is not None:
        if (
            not isinstance(end_byte, int)
            or not end_byte > start_byte
            or not end_byte > 0
        ):
            raise ValueError("Endbyte was given but it wasn't bigger than startbyte or wasn't greater 0")

    

#Just downloads bytes, no more, no less
def downloadToFileSimple(
        url: str,
        session: Session,
        out_file: str,
        extra_headers: dict = None,
        chunk_size: int = 8192,
        open_file_method: str = "wb",
        start_byte : int = 0,
        end_byte : int | None = None

) -> int:
    """
    Downloads a file from url.
    Doesn't update progress automatically
    Gives back how many bytes were written
    """

    _validateDownloadToFileArguments(
        url,
        session,
        out_file,
        extra_headers,
        chunk_size,
        open_file_method,
        start_byte,
        end_byte
    )

    byteRange = f"bytes={start_byte}-"
    if end_byte is not None:
        byteRange += str(end_byte)

    req = urllib.request.Request(
        url,
        headers={
            "Range" : byteRange
        }
    )
    

    downloadedBytes = 0
#Actuall download part
    with session.open(url=url, headers=extra_headers) as response, open(out_file, open_file_method) as file:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            file.write(chunk)
            downloadedBytes += len(chunk)


    return downloadedBytes

    



def downloadToFile(
        out_file: str,
        session: Session,
        url: str,
        download_progress: Download.DownloadProgress,
        extra_headers: dict = None,
        chunk_size: int = 8192,
        open_file_method: str = "wb",
        start_byte: int = 0,
        end_byte : int | None = None

):
    _validateDownloadToFileArguments(
            url,
            session,
            out_file,
            extra_headers,
            chunk_size,
            open_file_method,
            start_byte,
            end_byte
        )

    byteRange = f"bytes={start_byte}-"
    if end_byte is not None:
        byteRange += str(end_byte)

    req = urllib.request.Request(
        url,
        headers={
            "Range" : byteRange
        }
    )
    


    with session.open(request=req, headers=extra_headers) as response, open(out_file, open_file_method) as file:
        content_length = response.headers.get("Content-Length")
        content_range = response.headers.get("Content-Range")

        if content_range:
            total_size = content_range.split("/")[-1]

            if total_size != "*":
                download_progress.total_bytes = int(total_size)

        elif content_length:
            download_progress.total_bytes = int(content_length)


        while True:
            chunk = response.read(chunk_size)

            if not chunk:
                break

            file.write(chunk)

            progress.updateDownloadProgress(
                download_progress=download_progress,  downloaded_bytes=len(chunk), caller=f"[CORE] downloadToFile: {download_progress.job_id}")

     





def _validateDownloadYieldArguments(
    url: str,
    session: Session,
    extra_headers: dict,
    chunk_size: int,
    start_byte: int,
    end_byte: int | None = None
):
    Validate.special.validateHostDefault(
                url, caller="[CORE] network.file.downloadYield")
        
    Validate.special.validateSession(
        session, argument_name="session", caller="[CORE] network.file.downloadYield")

    Validate.general.validateInt(
        argument_name="chunk_size", integer=chunk_size, caller="[CORE] network.file.downloadYield")

    if extra_headers:
        Validate.general.validateDict(
            argument_name="extra_headers", dictionary=extra_headers, caller="[CORE] network.file.downloadYield")

    if (
      not isinstance(start_byte, int)
      or not start_byte >= 0  
    ):
        raise ValueError("Startbyte wasn't an integer with value 0 and above")

    if end_byte is not None:
        if (
            not isinstance(end_byte, int)
            or not end_byte > start_byte
            or not end_byte > 0
        ):
            raise ValueError("Endbyte was given but it wasn't bigger than startbyte or wasn't greater 0")




def downloadYieldSimple(
        session: Session,
        url: str,
        extra_headers: dict = None,
        chunk_size: int = 8192,
        start_byte: int = 0,
        end_byte : int | None = None
):
    _validateDownloadYieldArguments(
        url,
        session,
        extra_headers,
        chunk_size,
        start_byte,
        end_byte
    )

    byteRange = f"bytes={start_byte}-"
    if end_byte is not None:
        byteRange += str(end_byte)

    

    req = urllib.request.Request(
        url,
        headers={
            "Range" : byteRange
        }
    )

    with session.open(request=req, headers=extra_headers) as response:
        while True:
            chunk = response.read(chunk_size)

            if not chunk:
                break

            yield chunk

def downloadYield(
        session: Session,
        url: str,
        download_progress: Download.DownloadProgress,
        extra_headers: dict = None,
        chunk_size: int = 8192,
        start_byte: int = 0,
        end_byte : int | None = None
):
    _validateDownloadYieldArguments(
        url,
        session,
        extra_headers,
        chunk_size,
        start_byte,
        end_byte

    )

    byteRange = f"bytes={start_byte}-"
    if end_byte is not None:
        byteRange += str(end_byte)

    req = urllib.request.Request(
        url,
        headers={
            "Range" : byteRange
        }
    )



    with session.open(request=req, headers=extra_headers) as response:
        content_length = response.headers.get("Content-Length")
        content_range = response.headers.get("Content-Range")

        if content_range:
            total_size = content_range.split("/")[-1]

            if total_size != "*":
                download_progress.total_bytes = int(total_size)

        elif content_length:
            download_progress.total_bytes = int(content_length)

        if content_length:
            download_progress.total_bytes = int(content_length)
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break

            progress.updateDownloadProgress(
                download_progress,
                len(chunk),
                caller="[CORE] downloadYield"
            )
            yield chunk





async def asyncDownloadYieldSimple(
        session: Session,
        url: str,
        extra_headers: dict = None,
        chunk_size: int = 8192,
        start_byte: int = 0,
        end_byte: int | None = None
        ):
    _validateDownloadYieldArguments(
        url,
        session,
        extra_headers,
        chunk_size,
        start_byte,
        end_byte

    )


    byteRange = f"bytes={start_byte}-"
    if end_byte is not None:
        byteRange += str(end_byte)

    print(byteRange)
    req = urllib.request.Request(
        url,
        headers={
            "Range" : byteRange
        }
    )

    with session.open(request=req, headers=extra_headers) as response:
            
            while True:
                chunk = await asyncio.to_thread(
                        response.read,
                        chunk_size
                    )
                if not chunk:
                    break
    
                yield chunk
    
        

async def asyncDownloadYield(
    session: Session,
    url: str,
    download_progress: Download.DownloadProgress,
    extra_headers: dict = None,
    chunk_size: int = 8192,
    start_byte: int = 0,
    end_byte: int | None = None
    ):
    _validateDownloadYieldArguments(
        url,
        session,
        extra_headers,
        chunk_size,
        start_byte,
        end_byte
        

    )

    byteRange = f"bytes={start_byte}-"
    if end_byte is not None:
        byteRange += str(end_byte)

    req = urllib.request.Request(
        url,
        headers={
            "Range" : byteRange
        }
    )


    with session.open(request=req, headers=extra_headers) as response:
            content_length = response.headers.get("Content-Length")
            content_range = response.headers.get("Content-Range")

            if content_range:
                total_size = content_range.split("/")[-1]

                if total_size != "*":
                    download_progress.total_bytes = int(total_size)

            elif content_length:
                download_progress.total_bytes = int(content_length)
#actual download
            
            while True:
                chunk = await asyncio.to_thread(
                    response.read,
                    chunk_size
                )
                if not chunk:
                    break
    
                progress.updateDownloadProgress(
                    download_progress,
                    len(chunk),
                    caller="[CORE] downloadYield"
                )
                yield chunk
    
        
