# Core imports
import PythonModule.core as core

#own imports
from .soundcloud_browser import SoundcloudMediaBrowser

# Own provider imports

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

    browserConfig = {
        "click" : "#onetrust-reject-all-handler",
        "wait" : 500,
        "click" : "button.modal__closeButton[title='Close']",
        "wait" : 500
    }
    

    mediaBrowser = SoundcloudMediaBrowser(
        url=request.url,
    )

    medialist: list[models.FoundMedia] = []

    def _getMedia(browser: SoundcloudMediaBrowser):
        nonlocal medialist
        try:
            browser.run(
                headless=False,
                extra_headers=request.extra_headers,
                actions=browserConfig,
                wait_ms=10000
            )
        finally:
            try:
                medialist, unknownlist = browser.stop()
                
            except Exception as stopError:
                print(
                    "[Soundcloud] Failed to stop MediaBrowser:",
                    stopError
                )

    retry: int = 0
    while retry < retrys:
        if medialist:
            break

        _getMedia(mediaBrowser)

    
    if not medialist:
        raise core.models.errors.TaskFailedError(
            task="[CORE] SoundCloud._getMedia",
            reason="Browser couldn't detect valid media",
            extraMessages=
            [
                "Browser can't find media when the website is DRM protected/encrypted",
                "Try again with Headful Browser and see if Browser is now able to find Media"
                ],
            caller="[CORE] SoundCloud.getMediaInformation"
        )


    return models.makeProviderResult(
        medialist,
        request,
    )