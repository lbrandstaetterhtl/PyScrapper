#Core Imports
import PythonModule.core as core
from PythonModule.core.network import EmergencyBrowser
from PythonModule.core.network.Session import Session
from PythonModule.core.network import html
from PythonModule.models.requests import SearchFilters

#Own imports
from . import models

#Python Default Imports
import urllib.parse
import asyncio
import subprocess





TYPE_MAPPING = {
    "music.song": "track",
    "music.musician": "creator",
    "music.playlist": "playlist",
    "music.album": "album",
}



async def run_shell_command_async(command: str):
        await asyncio.to_thread(
            subprocess.run,
            command,
            shell=True,
            check=True,
            executable="/bin/bash"
        )



def search(
        search_term: str,
        filters: SearchFilters,
        session: Session,
        top: int = 5
) -> list[dict]:
     

    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Soundcloud.search")
    core.general.Validate.general.validateGeneralType(argument_name="filters", objType= SearchFilters, obj=filters, caller="[providers] Soundcloud.search")
    core.general.Validate.special.validateSession(session=session, argument_name="session", caller="[providers] Soundcloud.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Soundcloud.search")


    searchUrl: str = _buildSearchUrl(search_term)
    
    searchHtml: str = html.getHtml(
         session=session,
         url=searchUrl
    )
    core.general.Validate.general.validateStr(argument_name="searchHtml", string=searchHtml, caller="[providers] Soundcloud.search")

    results:list[dict] = []
    

    resultPattern: str = r'</ul>.*?<ul>.*?(<li><h2><a href=".*?)</ul>'
    resultsBlock: str = core.general.DataSearch.searchBlocks(resultPattern, searchHtml, return_regex_exception=True)
   

    


    hrefPattern: str = r'<a href="(.*?)".*?</a>'
    hrefList: list[str] = core.general.DataSearch.searchBlocksAll(hrefPattern, resultsBlock, return_regex_exception=True)

    for href in hrefList:
        if len(results) >= top:
            continue


        url = urllib.parse.urljoin("https://soundcloud.com", href)
        result:dict = _buildSearchResult(
            url,
            session,

        )
        if not result:
            continue

        result["identifier"] = href

        
        if _inFilter(
            filters=filters,
            result=result
        ):
            results.append(result)

    return results
    



def _inFilter(
    filters: SearchFilters,
    result: dict
) -> bool:

#If there are no filters, always append the result
    if not filters:
        return True

#If there are no tags than i can't check it and also append the result
    if not filters.tags or filters.tags == [""]:
        return True

#Getting result type, if it somehow is None, it will be marked as unknown and for safety and inspection it will still be marked as saveable
    resultType:str = result.get("type", None)
    if resultType == None:
        result["type"] = "unknown"
        return True

#Now checking if the result type is in tags
    resultType = resultType.strip()
    if resultType in filters.tags:
        return True

    return False


def _buildSearchResult(
        url: str,
        session: Session,

) -> dict:
    
#Search functions which calls this functions already uses the right url
    result: dict = {"url": url}
#Open the url and search for title, thumbnail and type
    with session.open(url=url) as response:
        data = response.read().decode("utf-8")

#Getting Type what this soundcloud resource is
    typePattern: str = r'<meta property="og:type" content="([^"]*)">'
    ressourceType: str = core.general.DataSearch.searchBlocks(typePattern, data, return_regex_exception=False)
    result["type"] = TYPE_MAPPING.get(ressourceType, None)

#Getting Title of this soundcloud resource
    titlePattern: str = r'<meta property="og:title" content="([^"]*)">'
    title: str = core.general.DataSearch.searchBlocks(titlePattern, data, return_regex_exception=False)
    result["title"] = title

#Getting Thumbnail of this soundcloud resource
    thumbnailPattern: str = r'<meta property="og:image" content="([^"]*)">'
    thumbnail: str = core.general.DataSearch.searchBlocks(thumbnailPattern, data, return_regex_exception=False)
    result["thumbnail"] = thumbnail

    
    if any(value == None or not value.strip() for value in result.values()):
        return {}  


    return result




def _buildSearchUrl(
          search_term: str
) -> str:
    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Soundcloud._buildSearchUrl")
    url = "https://soundcloud.com/search?" + urllib.parse.urlencode(
         {
              "q" : search_term
         }
    )
    return url


def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="Soundcloud.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_protocols_list=["https"],
        allowed_hostnames_list=["soundcloud.com", "www.soundcloud.com"],
        caller="[providers] Soundcloud.download"
        )

    buttonList=[
    "#onetrust-reject-all-handler",
    "button.modal__closeButton[title='Close']"
    ]

    medialist: core.models.media.MediaList = EmergencyBrowser.BrowserDiscoverStreamURLs_ButtonList(
        request.url,
        headless=True,
        adBlock=True,
        buttonList=buttonList
     )
    
    if not medialist:
        raise core.models.errors.TaskFailedError(
            task="[CORE] BrowserDiscoverStreamUrls_ButtonList",
            reason="Browser couldn't detect find valid media",
            extraMessages=["Browser can't find media when the website is DRM protected/encrypted", "Try again with Headful Browser and see if Browser is now able to find Media"]
        )

    bestCandidate = medialist.candidates[0]
    result = models.makeProviderResultFromCandidate(bestCandidate)
    result.total_size = models.getFileInformations(session=request.ses, url=result.url, extra_headers=result.extra_headers)
    return result
    
    




# def download(
#         download_information: core.models.General.DownloadInformations,
#         retry_with_FFmpeg:bool = False
        
# ):
    
    

#     core.general.Validate.validateDownloadInformation(argument_name="download_information", download_information=download_information, caller="[providers] Soundcloud.download")
#     core.general.Validate.validateBool(boolean=retry_with_FFmpeg, argument_name="retry_with_FFmpeg", caller="[providers] Soundcloud.download")

#     core.general.Validate.validateHostPro(
#         url=download_information.url,
#         allowed_protocols_list=["https"],
#         allowed_hostnames_list=["soundcloud.com", "www.soundcloud.com", "52.84.150.57", "52.84.150.39", "52.84.150.35", "52.84.150.52"],
#         caller="[providers] Soundcloud.download"
#         )


#     buttonList=[
#     "#onetrust-reject-all-handler",
#     "button.modal__closeButton[title='Close']"
#     ]

#     medialist: core.models.media.MediaList = core.request.EmergencyBrowser.BrowserDiscoverStreamURLs_ButtonList(
#         download_information.url,
#         headless=True,
#         adBlock=True,
#         buttonList=buttonList
#     )
    
#     if not medialist:
#         raise core.models.errors.TaskFailedError(
#             task="[CORE] BrowserDiscoverStreamUrls_ButtonList",
#             reason="Browser couldn't detect find valid media",
#             extraMessages=["Browser can't find media when the website is DRM protected/encrypted", "Try again with Headful Browser and see if Browser is now able to find Media"]
#         )
    
#     try:
#         for candidate in medialist.candidates:
            
#             candidate: core.models.media.Media
        
#             downloadFunction = MEDIATYPE_MAPPING.get(candidate.mediaType, None)
         
#             if downloadFunction == None:
#                 raise core.models.errors.TaskFailedError(
#                     task="[providers] Soundcloud.download",
#                     reason="Mediatype Mapping didn't give back a function",
#                     extraMessages=["Mediatype Mapping only has functions for HLS download", f"Mediatype of the highest prio media: '{candidate.mediaType}'"],
#                     caller="[providers] Soundcloud.download",
#                 )

                
#             downloader = downloadFunction(
#                 url = candidate.mediaUrl,
#                 out_file = download_information.outFile,
#                 session = download_information.session,
#                 progress_dict = download_information.downloadProgress
#             )
    
#             downloader.run()
     
#             return
                
 
#     except urllib.error.HTTPError as e:
#         if e.code == 403 and retry_with_FFmpeg:
#             print(f"Error 403, trying with CURL and FFMPEG")

#             ffmpegCommand = core.general.CurlToFFMPEG.get_curlToFFmpeg(
#                 candidate.curlCommand,
#                 output=download_information.outFile
#             )

#             run_shell_command_async(ffmpegCommand)

#             return

#         raise
#     except Exception:
#          raise


   