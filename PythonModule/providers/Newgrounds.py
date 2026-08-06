import PythonModule.core as core

from PythonModule.models import processorModels
from PythonModule.models.requests import SearchFilters

import urllib.parse
import re

SEARCH_TYPE_MAPPING = {
    "track": "audio",
    "audio": "audio",
    "song": "audio",
    "art": "art",
    "image": "art",
    "game": "games",
    "movie": "movies",
}

SEARCH_CLASS_MAPPING = {
    "item-audiosubmission" : "track",
    "item-portalitem-art" : "art",
    "item-user" : "creator",
    "item-portalsubmission" : "portal"
}

def search(
        search: str,
        filters: SearchFilters,
        session: core.request.Session.Session,
        top: int = 5
) -> list[dict[str, str]]:

    if not isinstance(search, str): raise ValueError("NewgroundsSearch: 'search' must be an string")
    if not isinstance(filters, SearchFilters): raise ValueError("NewgroundsSearch: 'filters' must be from type SearchFilters")
    if not isinstance(top, int) or top < 0: raise ValueError("NewgroundsSearch: 'top' must be an integer above 0")
    if not isinstance(session, core.request.Session.Session): raise ValueError("NewgroundsSearch: Given Session isn't core Session")
    results: list[dict] = []
   
    searchUrlList: list[str] = _buildSearchUrl(
        search,
        filters
        )
    


    searchBlockList: list[list] = []

    for searchUrl in searchUrlList:

        html = core.general.Html.getHtml(
        session,
        searchUrl
    )
#Pattern with every that find every relevant block and their ressources which this finder uses. There are a lot more "<a href" in newgroudns search html, but with this pattern we find everything we need
        resourceBlockPattern =  r'(<a\s+href="[^"]+"\s+class="[^"]+"\s+title="[^"]+".*?<img\s+src="[^"]+").*?</a>'
        blocks = core.general.DataSearch.searchBlocksAll(resourceBlockPattern, html, returnException=False)
        searchBlockList.append(blocks)

    searchBlockListPos: int = 0
    
    searchBlockListLen = len(searchBlockList)

    noItemStreak = 0

#If there are more tags and therefor more lists -> I didn't want to fill results with firstly data of tag1 and if there is still space to fill go to list with tag2, so with everyround a new list gets used and rounds back after max len has been reached
    while True:
        if len(results) >= top:
            return results

        if noItemStreak >= searchBlockListLen:
            return results
        
        curBlockList:list[str] = searchBlockList[searchBlockListPos]
      
        
        if len(curBlockList) > 0:
         
            noItemStreak = 0
            curBlock = curBlockList.pop(0)
            result = _buildSearchResult(curBlock)
     
            if result:
                results.append(result)

        else:
            noItemStreak += 1
      
        searchBlockListPos = _updateListPos(searchBlockListPos, searchBlockListLen)
        
        


def _updateListPos(
        curPos: int,
        lenList: int
):
    newPos = curPos + 1
    if newPos > (lenList - 1):
        newPos = 0
    return newPos


def _buildSearchResult(
        block: str
):
    result: dict = {}

    urlPattern = r'<a\s+href="(.*?)"'
    url = core.general.DataSearch.searchBlocks(urlPattern, block, returnException=False)
    result["url"] = url


    titlePattern = r'title="(.*?)"'
    title = core.general.DataSearch.searchBlocks(titlePattern, block, returnException=False)
    result["title"] = title


    thumbnailPattern = r'<img\s+src="(.*?)"'
    thumbnail = core.general.DataSearch.searchBlocks(thumbnailPattern, block, returnException=False)

#Sometimes newgrounds thumbnails start with just // so we need to check for that and add newground.com
    if thumbnail.startswith("//"):
        thumbnail = urllib.parse.urljoin(
            "https://www.newgrounds.com", thumbnail
        )
    result["thumbnail"] = thumbnail

    typePattern = r'class="(.*?)"'
    blockType = core.general.DataSearch.searchBlocks(typePattern, block, returnException=False)
    result["type"] = SEARCH_CLASS_MAPPING.get(blockType, None)


    for value in result.values():
        if value == None:
            return {}


    return result




def _buildSearchUrl(
        search: str,
        filters: SearchFilters
        ) -> list[str]:
    if not isinstance(search, str) or not search.strip():
        raise ValueError(
            "Newgrounds_buildSearchUrl: search must be a non-empty string"
        )

    
    searchUrlList: list[str] = []

    base = "https://www.newgrounds.com/search/"
    query = urllib.parse.urlencode({
                    "suitabilities": "etm",
                    "terms": search.strip(),
                })

    if not filters or not filters.tags or filters.tags == [""]:
        url=base +  "summary"
        searchUrlList.append(f"{url}?{query}")
        

    
    elif filters.tags and filters.tags != [""]:
        for tag in filters.tags:
            
            filterType = SEARCH_TYPE_MAPPING.get(tag, None)

            if filterType == None:
                continue

            url = base + "conduct/" + filterType
            if url in searchUrlList:
                continue

            searchUrlList.append(f"{url}?{query}")


    return searchUrlList
   
    


def download(
        download_information: processorModels.DownloadInformations
) -> None:
    if not download_information or not isinstance(download_information, processorModels.DownloadInformations): raise ValueError("NewgroundsDownload: Given download information is either None or has the wrong type")
    if not download_information.url.lower().startswith("https://www.newgrounds.com"): raise ValueError("NewgroundsDownload: url MUST start with  'https://www.newgrounds.com'")

    html: str = core.general.Html.getHtml(
        session=download_information.session, 
        url= download_information.url
    )

    musicPattern = r'<meta property="og:audio"\s+content="(.*?)">'
    musicUrl = core.general.DataSearch.searchBlocks(musicPattern, html)
    if not musicUrl: raise ValueError("NewgroundsDownload: No music url was found, are you certain that the given url is a track url?")

    core.download.File._downloadToFile(
        out_file=download_information.outFile,
        session=download_information.session,
        url=musicUrl,
        progress_dict=download_information.downloadProgress
    )
    

    

    
# GEH AUSI!!!! LG Elias
    