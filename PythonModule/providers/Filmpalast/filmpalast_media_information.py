
#Core imports
import PythonModule.core as core
from PythonModule.core.network import html

#Own imports
from .. import models
from .filmpalast_browser import FilmpalastMediaBrowser

#Python default imports
import base64
import urllib.error

EXTRA_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Referer": "https://meinecloud.click/movie/tt4901304",
    "Origin": "https://meinecloud.click",
}



def getMediaInformation(
        request: models.ProviderResultRequest,
        retrys: int = 3,
) -> models.ProviderResult:

    

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="[providers] Filmpalast.getMediaInformation"
    )

    core.general.Validate.general.validateInt(
        argument_name="retrys", integer=retrys, caller="[providers] Filmpalast.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_protocols_list=["https"],
        allowed_hostnames_list=["filmpalast.one", "www.filmpalast.one"],
        caller="[providers] Filmpalast.getMediaInformation"
        )



    streamHtml = html.getHtml(
        session=request.ses,
        url=request.url
    )

    if not streamHtml:
        raise core.models.errors.TaskFailedError(
            task="[providers] Filmpalast.getMediaInformation.getHtml",
            reason=f"Didn't get any valid html from provider with stream url '{request.url}'",
            caller="[providers] Filmpalast.getMediaInformation"
        )

    iframeSrcPattern = r'<iframe[^>]+src="([^"]+)"'
    iframeSrc = core.general.DataSearch.searchBlocks(pattern=iframeSrcPattern, search_block=streamHtml, return_regex_exception=False)

    if not iframeSrc:
        raise core.models.errors.TaskFailedError(
            task="[providers] Filmpalast.getMediaInformation.searchBlocks",
            reason=f"Couldn't find iframe with source",
            caller="[providers] Filmpalast.getMediaInformation"
        )

    iframeHtml = html.getHtml(
        session=request.ses,
        url=iframeSrc,
        extra_headers=EXTRA_HEADERS
    )

    serverPattern = r'<li[^>]+data-link="([^"]+)"[^>]*>'

    serversDecoded: list[str] = []

    servers:list[str] = core.general.DataSearch.searchBlocksAll(
        pattern=serverPattern,
        search_block=iframeHtml,
        return_regex_exception=False
    )


    if not servers:
        raise core.models.errors.TaskFailedError(
            task="[providers] Filmpalast.getMediaInformation.searchBlocksAll",
            reason=f"Couldn't find any host",
            caller="[providers] Filmpalast.getMediaInformation"
        )

    for server in servers:
        decoded = base64.b64decode(server).decode("utf-8")

        if decoded.startswith("//"):
            decoded = "https:" + decoded

        serversDecoded.append(decoded)


    for decodedServer in serversDecoded:
        print(decodedServer)
        browser = FilmpalastMediaBrowser(
            url=decodedServer,

        )
        browser.run(headless=False, extra_headers=EXTRA_HEADERS)

        browser.stop()
        



    
