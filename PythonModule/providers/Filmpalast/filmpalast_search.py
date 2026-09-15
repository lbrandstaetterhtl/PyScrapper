
from PythonModule.core.network import Session
from PythonModule.models.requests import SearchFilters
import PythonModule.core as core
from PythonModule.core.network import html

#Python default imports
import urllib.parse

def search(
        search_term:str,
        filters: SearchFilters,
        session: Session,
        top:int = 5
        
        ) -> list[dict]:

    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Filmpalast.search")
    core.general.Validate.special.validateSession(session=session, caller="[providers] Filmpalast.search")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters, caller="[providers] Filmpalast.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Filmpalast.search") 


    searchUrl = "https://filmpalast.one/?story=" + urllib.parse.quote(search_term) + "&do=search&subaction=search"

    searchHtml: str = html.getHtml(
        session=session,
        url=searchUrl
    )

    if not searchHtml:
        raise core.models.errors.TaskFailedError(
            task="[providers] Filmpalast.search.getHtml",
            reason=f"Didn't get any valid html from provider with search url '{searchUrl}'",
            caller="[providers] Filmpalast.search"
        )

    filmBlockPattern = r'<li class="TPostMv">(.*?)</li>'

    allMovieBlocks = core.general.DataSearch.searchBlocksAll(
        pattern=filmBlockPattern,
        search_block=searchHtml,
        return_regex_exception=False
    )

    if not allMovieBlocks:
        raise core.models.errors.TaskFailedError(
            task="[providers] Filmpalast.search.searchBlocksAll - allMovieBlocks",
            reason=f"Didn't find any valid block with pattern '{filmBlockPattern}'",
            caller="[providers] Filmpalast.search"
        )


    results: list[dict] = []
    for movieBlock in allMovieBlocks:

        if len(results) >= top:
            break

        result = _buildSearcResult(movieBlock)
        if not result:
            continue

        

        results.append(result)

    return results





def _buildSearcResult(
        block: str
):

    thumbnailUrlPattern = r'<img class=.*? data-src="(.*?)"'
    thumbnailUrl = core.general.DataSearch.searchBlocks(pattern=thumbnailUrlPattern, search_block=block, return_regex_exception=False)
    if not thumbnailUrl:
        return

    titlePattern = r'<h3 class="Title">(.*?)</h3>'
    title = core.general.DataSearch.searchBlocks(pattern=titlePattern, search_block=block, return_regex_exception=False)
    if not title:
        return

    urlPattern= r'<a href="(.*?)">'
    url = core.general.DataSearch.searchBlocks(pattern=urlPattern, search_block=block, return_regex_exception=False)
    if not url:
        return

    thumbnailUrl = thumbnailUrl if thumbnailUrl.startswith("https://") else "https://filmpalast.one" + thumbnailUrl

    result = {
        "url" : url,
        "title": title,
        "thumbnail" : thumbnailUrl,
        "type": "movie"
    }

    return result
    
