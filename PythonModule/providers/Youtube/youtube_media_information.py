
import PythonModule.core as core

from .. import models

def getMediaInformation(
        request: models.ProviderResultRequest,
        retrys: int = 3,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="[providers] Soundcloud.getMediaInformation"
    )

    core.general.Validate.general.validateInt(
        argument_name="retrys", integer=retrys, caller="[providers] Soundcloud.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_protocols_list=["https"],
        allowed_hostnames_list=["soundcloud.com", "www.soundcloud.com"],
        caller="[providers] Soundcloud.download"
        )

    pass