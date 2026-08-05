import urllib.error, urllib.request
import time
from ..request.Session import Session




def _downloadToFile(
        out_file: str,
        session: Session = None,
        request: urllib.request.Request = None,
        url: str = None,
        progress_dict: dict = None,
        extra_headers: dict = {},
        chunk_size: int = 8192,
):
    if request is None and url is None:
        raise ValueError(
            "_downloadToFile: Neither URL nor urllib Request was given"
        )

    if request is not None and url is not None:
        raise ValueError(
            "_downloadToFile: Give either URL or Request, not both"
        )

    if request is not None and not isinstance(
        request,
        urllib.request.Request
    ):
        raise TypeError(
            f"_downloadToFile: request must be urllib.request.Request, "
            f"got {type(request).__name__}: {request!r}"
        )

    if url is not None and not isinstance(url, str):
        raise TypeError(
            f"_downloadToFile: url must be str, "
            f"got {type(url).__name__}: {url!r}"
        )

    if session is None:
        session = Session()

    if progress_dict is None:
        progress_dict = {}

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

    progress_dict["status"] = "complete"