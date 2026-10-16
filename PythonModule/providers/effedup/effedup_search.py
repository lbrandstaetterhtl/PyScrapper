
# Core Imports
import PythonModule.core as core
from PythonModule.core.network import EmergencyBrowser
from PythonModule.core.network.Session import Session
from PythonModule.models.requests import SearchFilters

from PythonModule.core.network import html

# Own imports

from .. import models

# Python Default Imports
import urllib.parse, urllib.request, urllib.error

def search(
        search_term: str,
        filters: SearchFilters,
        session: Session,
        top: int = 5
) -> list[dict]:
    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term,
                                              caller="[providers] effedup.search")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters,
                                                      caller="[providers] effedup.search")
    core.general.Validate.special.validateSession(session=session, argument_name="session",
                                                  caller="[providers] effedup.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] effedup.search")

    searchUrl: str = "https://www.effedupmovies.com/?" + urllib.parse.urlencode({"s": search_term})


    searchHtml: str = html.getHtml(
        session=session,
        url=searchUrl,
    )


    if not searchHtml:
        raise core.models.errors.TaskFailedError(
            task="[providers] effedup.search",
            reason=f"Failed to get HTML from {searchUrl}"
        )

    allMediaPattern = r'<article id=.*?>(.*?)</article>'
    allMedia = core.general.DataSearch.searchBlocksAll(
        pattern=allMediaPattern,
        search_block=searchHtml,
        return_regex_exception=True
    )
    results: list[dict] = []

    for media in allMedia:
        if (len(results) >= top):
            break
        result: dict = _makeResultFromMediaBlock(media)
        if result:
            results.append(result)

    return results



def _makeResultFromMediaBlock(mediaBlock: str) -> dict:
    result :dict = {}

    titlePattern = r'title="(.*?)"'
    title = core.general.DataSearch.searchBlocks(
        pattern=titlePattern,
        search_block=mediaBlock,
        return_regex_exception=False
    )
    if not title:
        return None
    result["title"] = title

    urlPattern = r'<a href="(.*?)"'
    url = core.general.DataSearch.searchBlocks(
        pattern=urlPattern,
        search_block=mediaBlock,
        return_regex_exception=False
    )
    if not url:
        return None
    result["url"] = url

    thumbnailPattern = r'<img.*? src="(.*?)"'
    thumbnail = core.general.DataSearch.searchBlocks(
        pattern=thumbnailPattern,
        search_block=mediaBlock,
        return_regex_exception=False
    )
    if not thumbnail:
        return None
    
    result["thumbnail"] = thumbnail

    return result