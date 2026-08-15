#Core Imports
import PythonModule.core as core

from PythonModule.core.network.Session import Session
from PythonModule.core.network import html
from PythonModule.core.network import EmergencyBrowser

from PythonModule.models.requests import SearchFilters

# Own imports

from . import models


#Python Default Imports
import urllib.parse, urllib.error
from html import unescape
from pathlib import Path


SEARCH_TYPE_MAPPING = {
    "track": "audio",
    "audio": "audio",
    "song": "audio",
    "art": "art",
    "image": "art",
    "game": "games",
    "games" : "games",
    "movie": "movies",
    "movies" : "movies",
}

SEARCH_CLASS_MAPPING = {
    "item-audiosubmission" : "track",
    "item-portalitem-art" : "art",
    "item-user" : "creator",
    "item-portalsubmission" : "portal"
}

def search(
        search_term: str,
        filters: SearchFilters,
        session: Session,
        top: int = 5,
        retry: bool = True
) -> list[dict[str, str]]:

    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Newgrounds.search")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters, caller="[providers] Newgrounds.search")
    core.general.Validate.special.validateSession(session=session, argument_name="session", caller="[providers] Newgrounds.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Newgrounds.search")
    core.general.Validate.general.validateBool(boolean=retry, argument_name="retry", caller="[providers] Newgrounds.search")

    results: list[dict] = []
   
    searchUrlList: list[str] = _buildSearchUrl(
        search_term,
        filters
        )
    


    searchBlockList: list[list] = []
    try:
        for searchUrl in searchUrlList:

            searchHtml = html.getHtml(
            session,
            searchUrl
        )
            core.general.Validate.general.validateStr(argument_name="searchHtml", string=searchHtml, caller="[providers] Newgrounds.search")
    #Pattern with every that find every relevant block and their ressources which this finder uses. There are a lot more "<a href" in newgroudns search html, but with this pattern we find everything we need
            resourceBlockPattern =  r'(<a\s+href="[^"]+"\s+class="[^"]+"\s+title="[^"]+".*?<img\s+src="[^"]+").*?</a>'
            blocks = core.general.DataSearch.searchBlocksAll(resourceBlockPattern, searchHtml, return_regex_exception=True)
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

    except urllib.error.HTTPError as e:
            if e.code == 403 and retry:
                EmergencyBrowser.BrowserButtonPress(
                    url=searchUrl,
                    button_name="",
                    headless=False,
                )

                return search(
                    search_term=search_term,
                    filters=filters,
                    session=session,
                    top=top,
                    retry=False
                )

            raise

        
        


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
    url = core.general.DataSearch.searchBlocks(urlPattern, block, return_regex_exception=False)
    result["url"] = url


    titlePattern = r'title="(.*?)"'
    title = core.general.DataSearch.searchBlocks(titlePattern, block, return_regex_exception=False)
    result["title"] = title


    thumbnailPattern = r'<img\s+src="(.*?)"'
    thumbnail = core.general.DataSearch.searchBlocks(thumbnailPattern, block, return_regex_exception=False)

#Sometimes newgrounds thumbnails start with just // so we need to check for that and add newground.com
    if thumbnail:
        if thumbnail.startswith("//"):
            thumbnail = urllib.parse.urljoin(
                "https://www.newgrounds.com", thumbnail
            )
        result["thumbnail"] = thumbnail

    typePattern = r'class="(.*?)"'
    blockType = core.general.DataSearch.searchBlocks(typePattern, block, return_regex_exception=False)
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
            fullUrl = f"{url}?{query}"

            if fullUrl in searchUrlList:
                continue

            searchUrlList.append(fullUrl)


    return searchUrlList
   
    

        
def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="Newgrounds.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=["newgrounds.com", "www.newgrounds.com"],
        caller="[providers] Newgrounds.getMediaInformation"
    )

    siteHtml = html.getHtml(
        session=request.ses,
        url=request.url,
        extra_headers=request.extra_headers
    )
    if not siteHtml:
        raise core.models.errors.TaskFailedError(
            task="Newgrounds.getMediaInformation",
            reason="Couldn't get html",
            extraMessages=[
                f"Used url: {request.url}"
            ],
            caller="[providers] Newgrounds.getMediaInformation"
        )
        
    siteHtml = siteHtml.replace("\\/", "/")

    patterns = [
    # OpenGraph Audio
    r'<meta[^>]+property=["\']og:audio(?::url)?["\'][^>]+content=["\']([^"\']+)["\']',

    # OpenGraph Video
    r'<meta[^>]+property=["\']og:video(?::url)?["\'][^>]+content=["\']([^"\']+)["\']',

    # Direkte Media-URLs im HTML / Script-State
    r'https?://[^"\'\\ ]+\.(?:mp4|webm|mkv|mov|flac|wav|m4a|aac|opus|ogg|mp3)(?:\?[^"\'\\ ]*)?',
]    
    foundUrls = set()
    
    for pattern in patterns:
        matches = core.general.DataSearch.searchBlocksAll(pattern, siteHtml, return_regex_exception=False)

        for url in matches:
            foundUrls.add(unescape(url))

    if not foundUrls:
        raise core.models.errors.TaskFailedError(
            task="Newgrounds.getMediaInformation",
            reason="No video or audio url was found at all",
            extraMessages=[
                f"Used url: {request.url}"
            ],
            caller="[providers] Newgrounds.getMediaInformation"
        )


    bestUrl: str | None = None
    bestPriority = -1

    for url in foundUrls:
        extension = (
            Path(urllib.parse.urlparse(url).path)
            .suffix
            .lower()
            .removeprefix(".")
        )

        prio = models.NEWGROUNDS_MEDIA_PRIORITY.get(extension)

        if prio is None:
            continue

        if prio > bestPriority:
            bestUrl = url
            bestPriority = prio
    if bestUrl is None:
        raise core.models.errors.TaskFailedError(
            task="Newgrounds.getMediaInformation",
            reason="No valid url was found",
            extraMessages=[
                f"Now listening all urls that got found:",
                f", ".join(foundUrls) 
            ],
            caller="[providers] Newgrounds.getMediaInformation"
        )

    fileEnding = models.getContentType(bestUrl, request.ses, request.extra_headers)
    
    return models.makeProviderResult(
            url=bestUrl,
            fileending=fileEnding,
            type = core.models.Download.DownloadType.FILE,
            extra_headers=request.extra_headers
    
        )
        


    
    

#def download(
#        download_information: core.models.General.DownloadInformations
#) -> None:
   
#    core.general.Validate.validateDownloadInformation(argument_name="download_information", download_information=download_information, caller="[providers] Newgrounds.download")
#    core.general.Validate.validateHostPro(
#        url=download_information.url,
#        allowed_hostnames_list=["newgrounds.com", "www.newgrounds.com", "51.79.77.157", "51.79.77.158", "15.235.14.84", "51.79.82.168"],
#        caller="[providers] Newgrounds.download"
#    )
#    html: str = core.general.Html.getHtml(
#        session=download_information.session, 
#        url= download_information.url
#    )
#    core.general.Validate.validateStr(argument_name="html", string=html, caller="[providers] Newgrounds.download")

#    musicPattern = r'<meta property="og:audio"\s+content="(.*?)">'
#    musicUrl = core.general.DataSearch.searchBlocks(musicPattern, html, return_regex_exception=True)


#    core.download.File.downloadToFile(
#        out_file=download_information.outFile,
#        session=download_information.session,
#        url=musicUrl,
#        progress_dict=download_information.downloadProgress
#    )
    

    