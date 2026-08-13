

#Core imports
from .Session import Session


from ..models import Download

from ..general import Validate

#Own imports
from . import progress

#Python default imports
import time
import asyncio




def _validateDownloadToFileArguments(
    url: str,
    session: Session,
    out_file: str,
    extra_headers: dict,
    chunk_size: int,
    open_file_method: str,  
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

    

#Just downloads bytes, no more, no less
def downloadToFileSimple(
        url: str,
        session: Session,
        out_file: str,
        extra_headers: dict = None,
        chunk_size: int = 8192,
        open_file_method: str = "wb"

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
        open_file_method
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
        open_file_method: str = "wb"

):
    _validateDownloadToFileArguments(
            url,
            session,
            out_file,
            extra_headers,
            chunk_size,
            open_file_method
        )
    

    Validate.download.validateDownloadProgress(
            argument_name="download_progress", download_progress=download_progress, caller="[CORE] downloadToFile")


    with session.open(url=url, headers=extra_headers) as response, open(out_file, open_file_method) as file:
        download_progress.total_bytes = int(response.headers.get("Content-Length", 0))


        while True:
            chunk = response.read(chunk_size)

            if not chunk:
                break

            file.write(chunk)

            progress.updateDownloadProgress(
                download_progress,  len(chunk), f"[CORE] downloadToFile: {download_progress.job_id}")

     





def _validateDownloadYieldArguments(
    url: str,
    session: Session,
    extra_headers: dict,
    chunk_size: int, 
):
    Validate.special.validateHostDefault(
                url, caller="[CORE] network.file.downloadToFile")
        
    Validate.special.validateSession(
        session, argument_name="session", caller="[CORE] network.file.downloadToFile")

    Validate.general.validateInt(
        argument_name="chunk_size", integer=chunk_size, caller="[CORE] network.file.downloadToFile")

    if extra_headers:
        Validate.general.validateDict(
            argument_name="extra_headers", dictionary=extra_headers, caller="[CORE] network.file.downloadToFile")


def downloadYieldSimple(
        session: Session,
        url: str,
        extra_headers: dict = None,
        chunk_size: int = 8192
):
    _validateDownloadYieldArguments(
        url,
        session,
        extra_headers,
        chunk_size
    )

    with session.open(url=url, headers=extra_headers) as response:
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
        chunk_size: int = 8192
):
    _validateDownloadYieldArguments(
        url,
        session,
        extra_headers,
        chunk_size

    )

    Validate.download.validateDownloadProgress(
        argument_name="download_progress",
        download_progress=download_progress,
        caller="[CORE] network.file.yield.downloadYield"
    )



    with session.open(url=url, headers=extra_headers) as response:
        content_length = response.headers.get("Content-Length")

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
        chunk_size: int = 8192
        ):
    _validateDownloadYieldArguments(
        url,
        session,
        extra_headers,
        chunk_size

    )
    with session.open(url=url, headers=extra_headers) as response:
            
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
    chunk_size: int = 8192
    ):
    _validateDownloadYieldArguments(
        url,
        session,
        extra_headers,
        chunk_size

    )

   

    with session.open(url=url, headers=extra_headers) as response:
            content_length = response.headers.get("Content-Length")

            if content_length:
                download_progress.total_bytes = int(content_length)
            
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
    
        
