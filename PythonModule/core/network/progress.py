#Core imports
from ..models import Download

from ..general import Validate

from ..general.render import renderProgress



#Python default imports
import time

def updateDownloadProgress(
    download_progress: Download.DownloadProgress,
    downloaded_bytes: int | None = None,
    downloaded_segments: int | None = None,
    caller: str = "[CORE] updateDownloadProgress"
):

    if download_progress.start_time is None:
        download_progress.start_time = time.monotonic()
    
    
    Validate.download.validateDownloadProgress(
        argument_name="download_progress",
        download_progress=download_progress,
        caller=caller
    )

   

    download_progress.status = Download.TaskStatus.RUNNING

    # Update downloaded values
    if downloaded_bytes is not None:
        download_progress.downloaded_bytes += downloaded_bytes

    if downloaded_segments is not None:
        download_progress.downloaded_segments += downloaded_segments


    elapsed_time = (
        time.monotonic()
        - download_progress.start_time
    )


    # Calculate download speed
    if elapsed_time > 0:
        bytes_per_second = (
            download_progress.downloaded_bytes
            / elapsed_time
        )

        download_progress.speed = round(
            bytes_per_second / 1024 / 1024,
            2
        )


    # Segment based progress
    if download_progress.total_segments > 0:

        download_progress.progress = round(
            (
                download_progress.downloaded_segments
                / download_progress.total_segments
            ) * 100,
            2
        )

        if (
            download_progress.downloaded_segments > 0
            and elapsed_time > 0
        ):
            average_segment_time = (
                elapsed_time
                / download_progress.downloaded_segments
            )

            remaining_segments = (
                download_progress.total_segments
                - download_progress.downloaded_segments
            )

            download_progress.eta = round(
                remaining_segments * average_segment_time,
                1
            )


    # Byte based progress
    elif download_progress.total_bytes > 0:

        download_progress.progress = round(
            (
                download_progress.downloaded_bytes
                / download_progress.total_bytes
            ) * 100,
            2
        )

        if download_progress.speed > 0:
            bytes_per_second = (
                download_progress.downloaded_bytes
                / elapsed_time
            )

            remaining_bytes = (
                download_progress.total_bytes
                - download_progress.downloaded_bytes
            )

            download_progress.eta = round(
                remaining_bytes / bytes_per_second,
                1
            )


    # Unknown total size / segment count
    else:
        download_progress.progress = 0.0
        download_progress.eta = None


    # Pretty output
    if download_progress.total_segments > 0:
        downloaded_text = (
            f"{download_progress.downloaded_segments}"
            f"/{download_progress.total_segments} segments"
            f" - {download_progress.downloaded_bytes} bytes"
        )

    elif download_progress.total_bytes > 0:
        downloaded_text = (
            f"{download_progress.downloaded_bytes}"
            f"/{download_progress.total_bytes} bytes"
        )

    else:
        downloaded_text = (
            f"{download_progress.downloaded_bytes} bytes"
        )


    renderProgress(
        download_progress.job_id,
        (
            f"[DownloadJob] {download_progress.job_id} | "
            f"Downloaded {downloaded_text} | "
            f"({download_progress.progress:.2f}%, "
            f"{download_progress.speed:.2f} MiB/s, "
            f"ETA {download_progress.eta} s)"
        )
    )