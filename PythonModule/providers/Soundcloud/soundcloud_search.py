#Core imports
import PythonModule.core as core
from PythonModule.core.network.Session import Session
from PythonModule.core.network import html
from PythonModule.models.requests import SearchFilters

#Python default imports
import urllib.parse

TYPE_MAPPING = {
    "music.song": "track",
    "music.musician": "creator",
    "music.playlist": "playlist",
    "music.album": "album",
}


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
          search_term: str,
        
) -> str:
    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Soundcloud._buildSearchUrl")
    url = "https://soundcloud.com/search?" + urllib.parse.urlencode(
         {
              "q" : search_term
         }
    )
    return url