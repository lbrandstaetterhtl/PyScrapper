#Core Imports
from PythonModule.core.network import html
from PythonModule.core.network import EmergencyBrowser
import PythonModule.core as core

from . import models





#def _searchMedia(
#        html: str,
#        mediatype: str = ".mp4",
#        identifier: str = None
#) -> str:

#    core.general.Validate.general.validateStr(argument_name="html", string=html, caller="[providers] Suno._searchMedia")
#    core.general.Validate.general.validateStr(argument_name="identifier", string=identifier, caller="[providers] Suno._searchMedia")
#    core.general.Validate.general.validateStr(argument_name="mediatype", string=mediatype, caller="[providers] Suno._searchMedia")


#    mediaPattern = rf"https://cdn1.suno.ai/{identifier}{mediatype}"
    
#    songUrl:str = core.general.DataSearch.searchBlocks(mediaPattern, html, return_regex_exception=True)

#    return songUrl




def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="Soundcloud.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=["suno.com", "www.suno.com"],
        caller="[providers] Suno.getMediaInformation"
    )

    def getUrls():

        siteHtml = html.getHtml(
            session=request.ses,
            url=request.url,
            extra_headers=request.extra_headers
        )

        cdnPattern = r'\\?"(?:audio|video)_url\\?":\\?"(https://cdn\d+\.suno\.ai/[^"\\]+)'

        return core.general.DataSearch.searchBlocksAll(
            pattern=cdnPattern,
            search_block=siteHtml,
            return_regex_exception=True
        )
    try:
        allUrls:list[str] = getUrls()

    except Exception:
#if there aren't urls found it will probably because of captcha
        EmergencyBrowser.BrowserButtonPress(
            url=request.url,
            button_name="",
            headless=False,
            wait_after_click_ms=20000,
            wait_before_click_ms=20000
        )
        request.ses.reloadCookies()

    identifier: str = request.url.rstrip(".")[0].split("/", 1)[-1]

    allUrls = getUrls()

    bestUrl: str | None
    bestPrio: int = -1

    for url in allUrls:
        extension = url.rstrip(".")[-1]
        

        if identifier not in url:
            continue
        prio = models.MEDIA_PRIORITY_FOR_QUALITY_AUDIO.get(extension, 0)

        if prio > bestPrio:
            bestUrl = url
            bestPrio = prio

    if bestUrl is None:
        raise core.models.errors.TaskFailedError(
            task="Suno.getMediaInformation",
            reason="No supported audio/video file found",
            extraMessages=[
                f"Used url: {request.url}"
            ],
            caller="[providers] Suno.getMediaInformation"
        )

    fileEnding = models.getContentType(bestUrl, request.ses, request.extra_headers)

    return models.makeProviderResult(
            url=bestUrl,
            fileending=fileEnding,
            type = core.models.Download.DownloadType.FILE,
            extra_headers=request.extra_headers
    
        )
    



    
    


#def download (
#        download_information: core.models.General.DownloadInformations,  
        
#):
#    core.general.Validate.validateDownloadInformation(argument_name="download_information", download_information=download_information, caller="[providers] Suno.download")
#    core.general.Validate.validateHostPro(
#        url=download_information.url,
#        allowed_hostnames_list=["suno.com/", "www.suno.com/", "104.20.16.212", "172.66.144.155"],
#        caller="[providers] Suno.download"
#        )
#
  #  html = core.general.Html.getHtml(url=download_information.url, session=download_information.session)
 #   core.general.Validate.validateStr(argument_name="html", string=html, caller="[providers] Suno.download")
#
#
 #   strip = download_information.url.replace("https://suno.com/song/", "")
#    identifier = strip

#    songUrl = _searchMedia(html=html, identifier=identifier, mediatype=download_information.fileending)

#    
#    core.download.File.downloadToFile(
#        url=songUrl, out_file=download_information.outFile,
#        session=download_information.session,
#        progress_dict=download_information.downloadProgress
#        )

