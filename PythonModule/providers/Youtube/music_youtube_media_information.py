# Corei mports
import PythonModule.core as core

# Provider imports
from .. import models 

from .youtube_browser import YoutubeMusicMediaBrowser, YoutubeMusicTokenBrowser

import time

def getMediaInformationMusic(
    request: models.ProviderResultRequest,
    retrys: int = 3
) -> models.ProviderResult:


    core.general.Validate.general.validateGeneralType(
        argument_name="request",
        obj=request,
        objType=models.ProviderResultRequest,
        caller="Youtube.getMediaInformationMusic"
    )
    core.general.Validate.general.validateInt(
        argument_name="retrys",
        integer=retrys,
        caller="Youtube.getMediaInformationMusic"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=[
            "music.youtube.com",
        ],
        caller="[providers] Youtube.getMediaInformationMusic"
    )

    youtubeBrowser = YoutubeMusicMediaBrowser(
        url=request.url,
    )
    
    medialist: list[models.FoundMedia] = []

    def _getMedia(youtubeBrowser: YoutubeMusicMediaBrowser):
        nonlocal medialist
        youtubeBrowser.run()
        
        medialist, _ = youtubeBrowser.stop()


    retry: int = 0

    while retry < retrys:
        if medialist:
            break
        print(f"[Youtube] _getMedia: Trying to get media. Try: {retry}/{retrys}")
        _getMedia(youtubeBrowser)

    if not medialist:
        raise core.models.errors.TaskFailedError(
            task="[Youtube] getMediaInformationMusic",
            reason="Browser couldn't detect valid media",
            caller="[Youtube] getMediaInformationMusic"
        )

    # tokenBrowser = YoutubeMusicTokenBrowser(
    #     url=request.url,
    # )

    # wait_time = 15000
    # tokenBrowser.run(
    #     headless=False,
    #     extra_headers=request.extra_headers,
    #     timeout_ms=wait_time
    # )
    # time.sleep(wait_time / 1000)
    # token = tokenBrowser.stop()

    # for media in medialist:
    #     media.url = core.download.UMP.download.replacePoToken(
    #         media.url,
    #         token
    #     )

    return models.makeProviderResult(
        medialist,
        request,
    )


    

    

    

