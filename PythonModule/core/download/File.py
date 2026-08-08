import urllib.error, urllib.request
import time
import os
from ..request.Session import Session
from ..models.errors import ArgumentError
from ..general import Validate

def _validateArguments_downloadToFile(
        out_file: str,
        session: Session,
        request: urllib.request.Request,
        url: str,
        progress_dict: dict,
        extra_headers: dict,
        chunk_size: int,
):
    if (
        (url and request)
        or (not url and not request)
    ):
        raise ArgumentError(
            argument="url, request",
            wanted_type="str, urllib.request.Request: Please provide only one and not None",
            caller="[CORE] downloadToFile"
        )
    Validate.validateOutFile(out_file=out_file, caller="[CORE] downloadToFile")
    Validate.validateInt(argument_name="chunk_size", integer=chunk_size, caller="[CORE] downloadToFile")
    Validate.validateSession(session=session, argument_name="session", caller="[CORE] downloadToFile")
    Validate.validateDict(argument_name="progress_dict", dictionary=progress_dict, caller="[CORE] downloadToFile")
    
    
    if url:
        Validate.validateHostDefault(url)
    else:
        Validate.validateUrllibRequest(request)

    if extra_headers:
        Validate.validateDict(argument_name="extra_headers", dictionary=extra_headers, caller="[CORE] downloadToFile")

    

def downloadToFile(
        out_file: str,
        session: Session = None,
        request: urllib.request.Request = None,
        url: str = None,
        progress_dict: dict = None,
        extra_headers: dict = {},
        chunk_size: int = 8192,
        convert_file: bool = False,

):
    _validateArguments_downloadToFile(out_file, session, request, url, progress_dict, extra_headers, chunk_size)

    if request is not None:
        response_context = session.open(request=request, headers=extra_headers)
    else:
        response_context = session.open(url=url, headers=extra_headers)


    
    with response_context as response, open(out_file, "wb") as file:
        progress_dict["status"] = "downloading..."
        progress_dict["totalSegments"] = -1

        total_size = int(response.headers.get("Content-Length", 0))
        progress_dict["totalBytes"] = total_size

        downloaded = 0
        start_time = time.time()

        while True:
            chunk = response.read(chunk_size)

            if not chunk:
                break

            file.write(chunk)
            downloaded += len(chunk)

            elapsed_time = time.time() - start_time
            speed = downloaded / elapsed_time if elapsed_time > 0 else 0

            progress_dict["downloadedBytes"] = downloaded

            if total_size > 0:
                progress_dict["downloadProgress"] = (
                    downloaded / total_size * 100
                )
            else:
                progress_dict["downloadProgress"] = 0

            if speed > 0:
                progress_dict["speed"] = round(
                    speed / 1024 / 1024,
                    2
                )

                if total_size > 0:
                    remaining = total_size - downloaded
                    progress_dict["eta"] = round(
                        remaining / speed,
                        1
                    )
            print(
                f"\rDownloadJob: {progress_dict.get('id', 'unknown')} "
                f"Downloaded "
                f"{downloaded}/{total_size} bytes "
                f"({progress_dict.get('downloadProgress', 0):.2f}%, "
                f"{progress_dict.get('speed', 0)} MiB/s, "
                f"ETA {progress_dict.get('eta', 'unknown')} s)",
                end="",
                flush=True
            )

        if convert_file is True:
        #Converter finally puts the file into the correct codec instead of loading bytes in wrong file extension
            from ..models.Convert import ConvertRequest
            from ..general import Converter
            convertRequest = ConvertRequest(
                input_file_list=[out_file],
                output_file_list=[out_file],
                inputs_per_output=1,
                convert_progress_dict=progress_dict.get("convertProgress", {})
            )
            fileConverter = Converter.FileConverter(
                convert_request=convertRequest,
                caller=f"DownloadJob: {progress_dict.get("id", "unknown")}"
            )

            fileConverter.run()
            
        


    progress_dict["status"] = "complete"