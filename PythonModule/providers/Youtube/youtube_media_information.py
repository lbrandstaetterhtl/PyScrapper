
import PythonModule.core as core

from .. import models
import urllib.parse

def getMediaInformation(
        request: models.ProviderResultRequest,
        retrys: int = 3,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="[Youtube] getMediaInformation"
    )

    core.general.Validate.general.validateInt(
        argument_name="retrys", integer=retrys, caller="[Youtube] getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_protocols_list=["https"],
        allowed_hostnames_list=["youtube.com", "www.youtube.com"],
        caller="[Youtube] getMediaInformation"
        )

    parsedUrl = urllib.parse.urlparse(request.url)
    query = urllib.parse.parse_qs(parsedUrl.query)

    resolvedUrl = request.url
    
    if query.get("list", [None])[0]:
        query.pop("list")

        resolvedUrl = urllib.parse.urlunparse(
            parsedUrl._replace(
                query=urllib.parse.urlencode(query, doseq=True)
            )
        )


    mediaType = request.preferred_type if request.preferred_type else "video"

    return models.ProviderResult(
        url=resolvedUrl,
        download_type=core.models.Download.DownloadType.UMP,
        file_ending="webm",
        media_type=mediaType,
        mime_type=f"{mediaType}/webm",
        total_size=1,
        info=core.models.Download.Info(
            url=resolvedUrl,
            found_file="webm",
            preferred_file=request.preferred_file,
            preferred_type=request.preferred_type,
            found_type=mediaType
        )


    )