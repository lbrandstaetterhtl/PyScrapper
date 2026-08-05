import PythonModule.core as core
import urllib.error
import asyncio
import subprocess

import urllib.parse

from PythonModule.models import processorModels
from PythonModule.models.requests import SearchFilters

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

MEDIATYPE_MAPPING = {
    core.models.media.MediaType.MASTER_M3U8 : core.download.HLS.DownloadM3U8FromMaster,
    core.models.media.MediaType.INDEX_M3U8 : core.download.HLS.DownloadM3U8FromIndex,
}


def search(
        search: str,
        filters: SearchFilters,
        session: core.request.Session.Session,
        top: int = 5
) -> list[dict]:
     

    if not isinstance(search, str): raise ValueError("SoundcloudSearch: 'search' must be an string")
    if not isinstance(filters, SearchFilters): raise ValueError("SoundcloudSearch: 'filters' must be from type SearchFilters")
    if not isinstance(top, int) or top < 0: raise ValueError("SoundcloudSearch: 'top' must be an integer above 0")
    if not isinstance(session, core.request.Session.Session): raise ValueError("SoundcloudSearch: Given Session isn't core Session")

    searchUrl: str = _buildSearchUrl(search)
    html: str = core.general.Html.getHtml(
         session=session,
         url=searchUrl
    )
    results:list[dict] = []
    

    resultPattern: str = r'</ul>.*?<ul>.*?(<li><h2><a href=".*?)</ul>'
    resultsBlock: str = core.general.DataSearch.searchBlocks(resultPattern, html, returnException=False)
    if not resultsBlock: raise ValueError("SoundcloudSearch: No result on Soundcloud was found")

    


    hrefPattern: str = r'<a href="(.*?)".*?</a>'
    hrefList: list[str] = core.general.DataSearch.searchBlocksAll(hrefPattern, resultsBlock, returnException=False)
    if not hrefList: raise ValueError("SoundcloudSearch: Results were given but scrapper couldn't find href for results")
    for href in hrefList:
        if len(results) == top:
            continue


        url = urllib.parse.urljoin("https://soundcloud.com", href)
        result:dict = _buildSearchResult(
            url,
            session,

        )
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

#Gettign result type, if it somehow is None, it will be marked as unknown an for safety and inspection it will still be marked as saveable
    resultType:str = result.get("type", None)
    if resultType == None:
        result["type"] == "unknown"
        return True

#Now checking if the result type is in tags
    resultType = resultType.strip()
    if resultType in filters.tags:
        return True

    return False


def _buildSearchResult(
        url: str,
        session: core.request.Session.Session,

) -> dict:
    
#Search functions which calls this functions allready uses the right url
    result: dict = {"url": url}
#Open the url and search for title, thumbnail and type
    with session.open(url=url) as response:
        data = response.read().decode("utf-8")

#Getting Type what this soundcloud ressource is
    typePattern: str = r'<meta property="og:type" content="([^"]*)">'
    ressourceType: str = core.general.DataSearch.searchBlocks(typePattern, data, returnException=False)
    result["type"] = TYPE_MAPPING.get(ressourceType, None)

#Getting Title of this soudncloud ressource
    titlePattern: str = r'<meta property="og:title" content="([^"]*)">'
    title: str = core.general.DataSearch.searchBlocks(titlePattern, data, returnException=False)
    result["title"] = title

#Getting Thumbnail of this soundcloud ressource
    thumbnailPattern: str = r'<meta property="og:image" content="([^"]*)">'
    thumbnail: str = core.general.DataSearch.searchBlocks(thumbnailPattern, data, returnException=False)
    result["thumbnail"] = thumbnail


    return result






def _buildSearchUrl(
          search: str
) -> str:
    if not search or not isinstance(search, str): raise ValueError("Soundcloud_buildSearchUrl: Given search input wasn't a string")

    url = "https://soundcloud.com/search?" + urllib.parse.urlencode(
         {
              "q" : search
         }
    )
    return url





def download(
        download_information: processorModels.DownloadInformations,
        retry_with_FFmpeg:bool = False
        
):
    
    

    if not download_information or not isinstance(download_information, processorModels.DownloadInformations): raise ValueError("SoundcloudDownload: Given download information is either None or has the wrong type")

    if not "soundcloud.com" in download_information.url.lower(): raise core.models.errors.ArgumentError("Given URL wasn't a soundcloud.com URL")


    buttonList=[
    "#onetrust-reject-all-handler",
    "button.modal__closeButton[title='Close']"
    ]

    medialist: core.models.media.MediaList = core.request.EmergencyBrowser.BrowserDiscoverStreamURLs_ButtonList(
        download_information.url,
        headless=True,
        adBlock=True,
        buttonList=buttonList
    )
    
    if not medialist: raise ValueError("SoundcloudDownload: Didn't find media to download, maybe it is DRM protected? Try again headful Browser! DRM isn't supported tho")
    
    try:
        for candidate in medialist.candidates:
            
            candidate: core.models.media.Media
        
            downloadFunction = MEDIATYPE_MAPPING.get(candidate.mediaType, None)
         
            
            if not downloadFunction:
                raise ValueError("SoundcloudDownload: Best found ressource doesn't have a function to download it with")

            
  
                
            downloader = downloadFunction(
                url = candidate.mediaUrl,
                out_file = download_information.outFile,
                session = download_information.session,
                progress_dict = download_information.downloadProgress
            )
    
            downloader.run()
     
            return
                
 
    except urllib.error.HTTPError as e:
        if e.code == 403 and retry_with_FFmpeg:
            print(f"Error 403, trying with CURL and FFMPEG")

            ffmpegCommand = core.general.CurlToFFMPEG.get_curlToFFmpeg(
                candidate.curlCommand,
                output=download_information.outFile
            )

            run_shell_command_async(ffmpegCommand)

            return

        raise
    except Exception:
         raise


   