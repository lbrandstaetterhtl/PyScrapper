#Core Imports
import PythonModule.core as core
from PythonModule.core.network import html
from PythonModule.core.network.Session import Session
from PythonModule.core.network import EmergencyBrowser

#Own downloads

from . import models

#Python Default imports
import gzip
import zlib




    


iFramePattern = r'<iframe[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>'

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:149.0) Gecko/20100101 Firefox/149.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Sec-Fetch-Storage-Access": "none",
    "Connection": "keep-alive",
    "Referer": "https://www.wcoflix.tv/",
    "Cookie": "PHPSESSID=fir8vjjgm4b0qcm41be8sp6ire",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "DNT": "1",
    "Sec-GPC": "1",
    "Priority": "u=4",
    "TE": "trailers",
}


def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="Soundcloud.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=["wcoflix.tv", "www.wcoflix.tv"],
        caller="[providers] Wcoflix.getMediaInformation"
    )

    episodeHtml = html.getHtml(
        request.ses,
        request.url
    )

    indexUrl: str = core.general.DataSearch.searchBlocks(
        iFramePattern,
        episodeHtml,
        return_regex_exception=True
    )

    with request.ses.open(
        url=indexUrl, headers=headers
    ) as response:
        
        indexHTMLRaw = response.read()
        encoding = response.headers.get("Content-Encoding", "").lower()

    if encoding == "gzip":
        indexHTMLRaw = gzip.decompress(indexHTMLRaw)
    elif encoding == "deflate":
        indexHTMLRaw = zlib.decompress(indexHTMLRaw)

    

    medialist: core.models.media.MediaList = EmergencyBrowser.WCOFLIXBrowserDiscoverStreamUrls(
        indexUrl,
        headless=True,
        ad_block=True,
        extra_headers={
            "Referer": "https://www.wcoflix.tv/"
        }
    )   
    if not medialist:
        raise core.models.errors.TaskFailedError(
            task="[CORE] WCOFLIXBrowserDiscoverStreamUrls",
            reason="Browser didn't get valid Media. Please try again later",
            caller="[provider] Wcoflix.download"
        )

    print("TESTATASRFAR")
    print(medialist.candidates[-1].mediaUrl)
    request.extra_headers = medialist.candidates[-1].headers.to_dict()

    return models.makeProviderResult(
        urls=[medialist.candidates[-1].mediaUrl],
        request=request,
        download_type=core.models.Download.DownloadType.FILE
    )


#def download(
#        download_information: core.models.General.DownloadInformations,
#        retry_with_FFmpeg: bool = True
#): 
#    core.general.Validate.download.validateDownloadInformation(argument_name="download_information", download_information=download_information, caller="[providers] Wcoflix.download")
#    core.general.Validate.general.validateBool(boolean=retry_with_FFmpeg, argument_name="retry_with_ffmpeg", caller="[providers] Wcoflix.download")
#    core.general.Validate.special.validateHostPro(
#        url=download_information.url,
#        allowed_hostnames_list=["wcoflix.tv", "www.wcoflix.tv"],
#        caller="[providers] Wcoflix.download"
#        )
#
#
#    episodeHtml: str = core.general.Html.getHtml(
#        download_information.session,
#        download_information.url
#    )
#    core.general.Validate.validateStr(argument_name="expisodeHtml", string=episodeHtml, caller="[providers] Wcoflix.download")#
#
#    indexUrl: str = core.general.DataSearch.searchBlocks(
#        iFramePattern, 
#        episodeHtml,
#        return_regex_exception=True
#    )


#    with download_information.session.open(
#        url=indexUrl, headers=headers
#    ) as response:
#        
#        indexHTMLRaw = response.read()
#        encoding = response.headers.get("Content-Encoding", "").lower()

#    if encoding == "gzip":
#        indexHTMLRaw = gzip.decompress(indexHTMLRaw)
#    elif encoding == "deflate":
#        indexHTMLRaw = zlib.decompress(indexHTMLRaw)

    

#    medialist: core.models.media.MediaList = core.request.EmergencyBrowser.WCOFLIXBrowserDiscoverStreamUrls(
#        indexUrl,
#        headless=True,
#        ad_block=True,
#        extra_headers={
#            "Referer": "https://www.wcoflix.tv/"
#        }
#    )
#    if not medialist:
#        raise core.models.errors.TaskFailedError(
#            task="[CORE] WCOFLIXBrowserDiscoverStreamUrls",
#            reason="Browser didn't get valid Media. Please try again later",
#            caller="[provider] Wcoflix.download"
#        )
#    
#    candidate: core.models.media.Media = medialist.candidates[0]

#    downloadFunction = MEDIATYPE_MAPPING.get(candidate.mediaType, None)
#    if not downloadFunction:
#        raise core.models.errors.TaskFailedError(
#            task="MEDIATYPE_MAPPING.get()",
#            reason="Mediatype of the candidate wasn't in the dictionary",
#            extraMessages=["Wcoflix only supports functions for File and HLS", f"Mediatype of candidate {candidate.mediaType}"],
#            caller="[providers] Wcoflix.download"
#        )
  
#    extraHeaders = candidate.headers.to_dict()#
#    if isinstance(downloadFunction, type):         
#        downloader = downloadFunction(
#            url = candidate.mediaUrl,
#            out_file = download_information.outFile,
#            session = download_information.session,
#            progress_dict = download_information.downloadProgress,
#            extra_headers = extraHeaders,
#        )
        
#        downloader.run()
#        return  

#    else:
        
#        downloadFunction(
#            url= candidate.mediaUrl,
#            out_file = download_information.outFile,
#            session = download_information.session,
#            progress_dict = download_information.downloadProgress,
#            extra_headers=extraHeaders
        
#        )
#        return


    
                

    





