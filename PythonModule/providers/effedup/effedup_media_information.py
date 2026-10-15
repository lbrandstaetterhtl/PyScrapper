import PythonModule.core as core
from PythonModule.core.network import html

from PythonModule.core.network import Session

from .. import models 

def getMediaInformation(
        request: models.ProviderResultRequest,
        retrys: int = 3,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="[Effedup] getMediaInformation"
    )

    core.general.Validate.general.validateInt(
        argument_name="retrys", integer=retrys, caller="[Effedup] getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_protocols_list=["https"],
        allowed_hostnames_list=["effedupmovies.com", "www.effedupmovies.com"],
        caller="[Effedup] getMediaInformation"
        )

    effedupHtml: str = html.getHtml(
        session=request.ses,
        url=request.url,
        extra_headers=request.extra_headers
    )

    with open("effedup_debug.html", "w", encoding="utf-8") as f:
        f.write(effedupHtml)
    if not effedupHtml:
        raise core.models.errors.TaskFailedError(
            task="[Effedup] getMediaInformation",
            reason=f"Failed to get HTML from {request.url}"
        )

    hlsUrlPattern = r'<source src="(https://.*?.m3u8)"'
    hlsUrl = core.general.DataSearch.searchBlocks(
        pattern=hlsUrlPattern,
        search_block=effedupHtml,
        return_regex_exception=True
    )
    foundMedia = models.FoundMedia(
        url=hlsUrl,
        prio=100,
        stream_type=core.models.Download.DownloadType.HLS,
        extra_headers=request.extra_headers,
        extension="ts",
        mime_type="video/MP2T",
        media_type="video"
    )

    return models.makeProviderResult(
        [foundMedia],
        request
    )
    