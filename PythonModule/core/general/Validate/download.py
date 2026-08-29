#Own Imports
from .general import validateStr
from .special import validateSession, validateHostDefault, validateFileOpen

#Core imports
from ...models.errors import ArgumentError, TaskFailedError

#Python default imports
import os
import asyncio



def validateOutFile(
    out_file: str,
    caller: str = "[CORE] validateOutFile",
    open_method: str = "wb"
):
    validateStr(argument_name="out_file", string=out_file, caller=caller)
    validateFileOpen(arugment_name="open_method", open_method=open_method, caller=caller)

    try:
        path = os.path.abspath(out_file)
        invalidReasonList: list[str] = []
        if "\0" in path:
            invalidReasonList.append("Null Byte was found, this makes the path invalid")

        if os.path.exists(out_file) and open_method not in ["a", "ab", "a+", "ab+"]:
            invalidReasonList.append("Given outFile already exists. Please choose another outFile")

        parent = os.path.dirname(os.path.abspath(out_file))
        os.makedirs(parent, exist_ok=True)

        os.stat(os.path.dirname(path) or ".")

        
        

        if invalidReasonList:
            raise TaskFailedError(
                task=f"validateOutFile '{out_file}'",
                reason=f"{', '.join(invalidReasonList)}",
                caller=caller
            )

    except Exception as e:
        raise TaskFailedError(
            task=f"validateOutFile {out_file}",
            reason=str(e),
            caller=caller
        )


def validateDownloadContext(
    argument_name: str,
    download_context,
    caller: str = "[CORE] validateDownloadContext"
):
    from ...models import Download

    if (
        not download_context
        or not isinstance(
            download_context,
            Download.DownloadContext
        )
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="core.models.Download.DownloadContext",
            obj=download_context,
            caller=caller
        )

    validateDownloadTarget(
        argument_name=f"{argument_name}.target",
        download_target=download_context.target,
        caller=caller
    )

    validateDownloadProgress(
        argument_name=f"{argument_name}.download_progress",
        download_progress=download_context.download_progress,
        caller=caller
    )




def validateDownloadTarget(
    argument_name: str,
    download_target,
    caller: str = "[CORE] validateDownloadTarget"
):
    from ...models import Download

    if (
        not download_target
        or not isinstance(
            download_target,
            Download.DownloadTarget
        )
    
    
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="core.models.Download.DownloadTarget",
            obj=download_target,
            caller=caller
        )
    if (
            not download_target.download_type
            or not isinstance(download_target.download_type, Download.DownloadType)
        ):
        raise ArgumentError(
            argument=argument_name + "download_type",
            wanted_type="core.models.Download.DownloadType",
            obj=download_target.download_type,
            caller=caller

        )


    validateHostDefault(
        url=download_target.url,
        caller=caller
    )

  

    if download_target.extra_headers:
        if not isinstance(
            download_target.extra_headers,
            dict
        ):
            raise ArgumentError(
                argument=f"{argument_name}.extra_headers",
                wanted_type="dict[str, str]",
                obj=download_target.extra_headers,
                caller=caller
            )
        
    if download_target.extra_headers:
        if not all(
            isinstance(key, str)
            and isinstance(value, str)
            for key, value
            in download_target.extra_headers.items()
        ):
            raise ArgumentError(
                argument=f"{argument_name}.extra_headers",
                wanted_type="dict[str, str]",
                obj=download_target.extra_headers,
                caller=caller
            )




def validateDownloadProgress(
    argument_name: str,
    download_progress,
    caller: str = "[CORE] validateDownloadProgress"
):
    from ...models import Download

    if (
        not download_progress
        or not isinstance(
            download_progress,
            Download.DownloadProgress
        )
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="core.models.Download.DownloadProgress",
            obj=download_progress,
            caller=caller
        )

    validateStr(
        argument_name=f"{argument_name}.job_id",
        string=download_progress.job_id,
        caller=caller
    )

    if not isinstance(
        download_progress.status,
        Download.TaskStatus
    ):
        raise ArgumentError(
            argument=f"{argument_name}.status",
            wanted_type="core.models.Download.TaskStatus",
            obj=download_progress.status,
            caller=caller
        )

    if (
        not isinstance(
            download_progress.progress,
            (int, float)
        )
        or isinstance(
            download_progress.progress,
            bool
        )
        or not 0 <= download_progress.progress <= 100
    ):
        raise ArgumentError(
            argument=f"{argument_name}.progress",
            wanted_type="float: 0 <= progress <= 100",
            obj=download_progress.progress,
            caller=caller
        )

    if (
        not isinstance(
            download_progress.downloaded_bytes,
            int
        )
        or isinstance(
            download_progress.downloaded_bytes,
            bool
        )
        or download_progress.downloaded_bytes < 0
    ):
        raise ArgumentError(
            argument=f"{argument_name}.downloaded_bytes",
            wanted_type="int >= 0",
            obj=download_progress.downloaded_bytes,
            caller=caller
        )

    if (
        not isinstance(
            download_progress.total_bytes,
            int
        )
        or isinstance(
            download_progress.total_bytes,
            bool
        )
        or download_progress.total_bytes < -1
    ):
        raise ArgumentError(
            argument=f"{argument_name}.total_bytes",
            wanted_type="int >= -1",
            obj=download_progress.total_bytes,
            caller=caller
        )

    if (
        not isinstance(
            download_progress.downloaded_segments,
            int
        )
        or isinstance(
            download_progress.downloaded_segments,
            bool
        )
        or download_progress.downloaded_segments < 0
    ):
        raise ArgumentError(
            argument=f"{argument_name}.downloaded_segments",
            wanted_type="int >= 0",
            obj=download_progress.downloaded_segments,
            caller=caller
        )

    if (
        not isinstance(
            download_progress.total_segments,
            int
        )
        or isinstance(
            download_progress.total_segments,
            bool
        )
        or download_progress.total_segments < -1
    ):
        raise ArgumentError(
            argument=f"{argument_name}.total_segments",
            wanted_type="int >= -1",
            obj=download_progress.total_segments,
            caller=caller
        )

    if (
        not isinstance(
            download_progress.speed,
            (int, float)
        )
        or isinstance(
            download_progress.speed,
            bool
        )
        or download_progress.speed < 0
    ):
        raise ArgumentError(
            argument=f"{argument_name}.speed",
            wanted_type="float >= 0",
            obj=download_progress.speed,
            caller=caller
        )

    if (
        download_progress.eta is not None
        and (
            not isinstance(
                download_progress.eta,
                (int, float)
            )
            or isinstance(
                download_progress.eta,
                bool
            )
            or download_progress.eta < 0
        )
    ):
        raise ArgumentError(
            argument=f"{argument_name}.eta",
            wanted_type="float >= 0 | None",
            obj=download_progress.eta,
            caller=caller
        )

    if (
        download_progress.error_message is not None
        and not isinstance(
            download_progress.error_message,
            str
        )
    ):
        raise ArgumentError(
            argument=f"{argument_name}.error_message",
            wanted_type="str | None",
            obj=download_progress.error_message,
            caller=caller
        )




def validateConvertProgress(
    argument_name: str,
    convert_progress,
    caller: str = "[CORE] validateConvertProgress"
):
    from ...models import Download

    if (
        not convert_progress
        or not isinstance(
            convert_progress,
            Download.ConvertProgress
        )
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="core.models.Download.ConvertProgress",
            obj=convert_progress,
            caller=caller
        )

    validateStr(
        argument_name=f"{argument_name}.job_id",
        string=convert_progress.job_id,
        caller=caller
    )

    if not isinstance(
        convert_progress.status,
        Download.TaskStatus
    ):
        raise ArgumentError(
            argument=f"{argument_name}.status",
            wanted_type="core.models.Download.TaskStatus",
            obj=convert_progress.status,
            caller=caller
        )

    if (
        not isinstance(
            convert_progress.total_converts,
            int
        )
        or isinstance(
            convert_progress.total_converts,
            bool
        )
        or convert_progress.total_converts < 0
    ):
        raise ArgumentError(
            argument=f"{argument_name}.total_converts",
            wanted_type="int >= 0",
            obj=convert_progress.total_converts,
            caller=caller
        )

    if (
        not isinstance(
            convert_progress.finished_converts,
            int
        )
        or isinstance(
            convert_progress.finished_converts,
            bool
        )
        or convert_progress.finished_converts < 0
    ):
        raise ArgumentError(
            argument=f"{argument_name}.finished_converts",
            wanted_type="int >= 0",
            obj=convert_progress.finished_converts,
            caller=caller
        )

    if (
        convert_progress.finished_converts
        > convert_progress.total_converts
    ):
        raise ArgumentError(
            argument=f"{argument_name}.finished_converts",
            wanted_type=(
                "int <= total_converts"
            ),
            obj=convert_progress.finished_converts,
            caller=caller
        )

    if (
        not isinstance(
            convert_progress.convert_progress,
            (int, float)
        )
        or isinstance(
            convert_progress.convert_progress,
            bool
        )
        or not (
            0
            <= convert_progress.convert_progress
            <= 100
        )
    ):
        raise ArgumentError(
            argument=f"{argument_name}.convert_progress",
            wanted_type=(
                "float: 0 <= convert_progress <= 100"
            ),
            obj=convert_progress.convert_progress,
            caller=caller
        )



def validateDownloadInformation(
    argument_name: str,
    download_information,
    caller: str  = "[CORE] validateDownloadInformation"
):
    from ...models import Download
    if (
        not download_information
        or not isinstance(download_information, Download.DownloadInformation)
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="core.models.Download.DownloadInformation",
            obj=download_information,
            caller=caller
        )

    if (
        not download_information.download_strategie
        or not isinstance(download_information.download_strategie, Download.DownloadStrategie)
    ):
        raise ArgumentError(
            argument=argument_name,
            wanted_type="core.models.Download.DownloadStrategie",
            obj=download_information.download_strategie,
        )

    
    if (
        not download_information.download_limiter
        or not isinstance(download_information.download_limiter, asyncio.Semaphore)
    ):
        raise ArgumentError(
            argument=f"{argument_name}.download_limiter",
            wanted_type="asyncio.Semaphore",
            obj=download_information.download_limiter,
            caller=caller
        )
    
    validateSession(session=download_information.session, argument_name=argument_name, caller=caller)
    
    validateStr(argument_name="job_id", string=download_information.job_id, caller=caller)

    
    for index, context in enumerate(
        download_information.contexts
    ):
        validateDownloadContext(
            argument_name=f"{argument_name}.contexts[{index}]",
            download_context=context,
            caller=caller
        )