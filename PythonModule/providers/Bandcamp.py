# Core Imports
import PythonModule.core as core
from PythonModule.core.network import EmergencyBrowser
from PythonModule.core.network.Session import Session
from PythonModule.models.requests import SearchFilters

from PythonModule.core.network import html

# Own imports

from . import models

# Python Default Imports
import urllib.parse, urllib.request, urllib.error


class BandCampSearchError(Exception): ...


def search(
        search_term: str,
        filters: SearchFilters,
        session: Session,
        top: int = 5
) -> list[dict]:
    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term,
                                              caller="[providers] Bandcamp.search")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters,
                                                      caller="[providers] Bandcamp.search")
    core.general.Validate.special.validateSession(session=session, argument_name="session",
                                                  caller="[providers] Bandcamp.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Bandcamp.search")
    searchURL = _buildSearchUrl(
        search_term=search_term,
    )

    def _getSearchHtml():
        searchHtml = html.getHtml(
            url=searchURL,
            session=session
        )
        core.general.Validate.general.validateStr(argument_name="searchHtml", string=searchHtml,
                                                  caller="[providers] Bandcamp._getSearchHtml")
        return searchHtml

    try:
        results = _get_searchResults(
            searchHtml=_getSearchHtml(),
            top=top,
            filters=filters
        )
    # Sometimes Bandcamp hates python and wants javascript to be executed
    except Exception:

        # Der Browser bekommt die Seite, die urllib nicht bekommt. Sein html wird direkt weiterverwendet,
        # ein zweiter Versuch mit urllib wuerde erneut an der Challenge haengen
        browserResult = EmergencyBrowser.BrowserButtonPress(
            url=searchURL,
            button_name="",
            cookie_file=session.cookieFile,
            headless=False,
            wait_after_click_ms=15000,
            wait_before_click_ms=10000
        )
        session.reloadCookies()

        searchHtml = browserResult["html"]

        if _isClientChallenge(searchHtml):
            raise core.models.errors.TaskFailedError(
                task="[providers] Bandcamp.search",
                reason="Bandcamp still answers with a client challenge after the browser run",
                extraMessages=[
                    "The challenge was not solved inside the given waiting time",
                    "Try a longer wait_before_click_ms or check if the browser window shows a captcha",
                    f"Used url: {searchURL}"
                ],
                caller="[providers] Bandcamp.search"
            )

        results = _get_searchResults(
            searchHtml=searchHtml,
            top=top,
            filters=filters
        )

    return results


def _buildSearchUrl(
        search_term: str,

) -> list[str]:
    base_url = "https://bandcamp.com/search?"

    params = {
        "q": search_term
    }
    searchURL = base_url + urllib.parse.urlencode(params)
    return searchURL


def _get_searchResults(
        searchHtml: str,
        top: int,
        filters: SearchFilters

) -> list[dict]:
    results = []

    result_items_pattern = r'<ul class="result-items">(.*?)</ul>'

    try:
        allTracks = core.general.DataSearch.searchBlocks(
            pattern=result_items_pattern,
            search_block=searchHtml,
            return_regex_exception=True
        )

    except core.general.DataSearch.RegexSearchError as error:
        raise core.models.errors.TaskFailedError(
            task="allTracks = [CORE] searchBlocks",
            reason=f"searchBlocks search error: {error}",
            extraMessages=["Maybe Bandcamp wants the user to solve captcha.",
                           "Try sending a headful browser and see if there is javascript or captchas that needs to be solved"],
            caller="[providers] Bandcamp._get_searchResults",
        )
    tracks = core.general.DataSearch.searchBlocksAll(pattern=r'<li class="searchresult.*?</li>', search_block=allTracks,
                                                     return_regex_exception=True)

    for track in tracks:

        if len(results) >= top:
            break
        type_pattern = r'data-search=.*?(?:&quot;|")type(?:&quot;|")\s*:\s*(?:&quot;|")(.*?)(?:&quot;|")'

        trackType = core.general.DataSearch.searchBlocks(
            pattern=type_pattern,
            search_block=track,
            return_regex_exception=True
        )
        MyType = _typeMapping(trackType)

        # Default "nothing" that gets sent for tags is [''] that's why filtering for that
        if filters.tags != ['']:

            if MyType not in filters.tags:
                continue

        result = _buildResult(
            track=track,
            typeGiven=MyType

        )

        results.append(result)

    return results


def _buildResult(
        track: str,
        typeGiven: str

) -> dict:
    dictionary = {}
    thumbnail_pattern = r'<img src="(.*?)">'

    dictionary['thumbnail'] = core.general.DataSearch.searchBlocks(
        pattern=thumbnail_pattern,
        search_block=track
    )
    titel_pattern = r'<div class="heading">.*?<a.*?>(.*?)</a>'
    dictionary['title'] = core.general.DataSearch.searchBlocks(
        pattern=titel_pattern,
        search_block=track
    )

    url_pattern = r'<div class="heading">.*?<a href="(.*?)"'
    dictionary['url'] = core.general.DataSearch.searchBlocks(
        pattern=url_pattern,
        search_block=track
    )
    dictionary["type"] = typeGiven
    return dictionary


def _typeMapping(givenType: str) -> str:
    mapping = {
        "t": "track",
        "a": "album",
        "b": "creator"
    }
    return mapping.get(givenType, None)


def _validateURL(
        url: str,
) -> str:
    if url.startswith("https://t4.bcbits.com/"):
        return "streamURL"

    elif url.startswith("https://") and "track" in url:
        return "trackURL"

    elif url.startswith("https://") and "album" in url:
        return "albumURL"

    else:

        raise core.models.errors.InvalidURLError(
            url=url,
            reasonList=["Given url is neither a direct streamUrl, trackUrl or albumUrl"],
            caller="[providers] Bandcamp._validateUrl"
        )


# Bandcamp is behind a bot check. The interstitial has no search results in it, only a loader script
CLIENT_CHALLENGE_MARKERS = (
    "<title>Client Challenge</title>",
    "/_fs-ch-"
)


def _isClientChallenge(
        page_html: str
) -> bool:
    if not isinstance(page_html, str):
        return False

    return any(marker in page_html for marker in CLIENT_CHALLENGE_MARKERS)


# Matches every stream url on the page. The url ends at the next quote, backslash or whitespace.
# No ";" as an end marker, that would cut the url at the first "&amp;"
STREAMING_URL_PATTERN = r'(https://t4\.bcbits\.com/stream/[^"\s\\]+?)(?:&quot;|"|\\|\s|$)'


def _extractStreamingURLs(
        urlType: str,
        url: str,
        session
) -> tuple[list[str], list[str | None]]:
    match urlType:
        case "streamURL":
            streamingURL = url
            return [streamingURL], [None]

        case "trackURL" | "albumURL":
            pageHtml = html.getHtml(
                url=url,
                session=session
            )
            core.general.Validate.general.validateStr(argument_name="pageHtml", string=pageHtml,
                                                      caller="[providers] Bandcamp._extractStreamingURLs")

            streamingUrls = _findStreamingUrls(pageHtml)

            return streamingUrls, [url] * len(streamingUrls)

        case _:
            raise core.models.errors.TaskFailedError(
                task="match urlType",
                reason=f"None supported urltype '{urlType}' was given",
                caller="[providers] Bandcamp._extractStreamingURLs"
            )


# Reads every stream url out of a page or out of html that came from the browser
def _findStreamingUrls(
        page_html: str
) -> list[str]:
    streamingUrls = core.general.DataSearch.searchBlocksAll(
        pattern=STREAMING_URL_PATTERN,
        search_block=page_html,
        return_regex_exception=False
    )

    # searchBlocksAll gives back an empty string instead of an empty list when nothing matched
    if not streamingUrls:
        return []

    return _cleanStreamingUrls(streamingUrls)


# Removes html escaping and duplicates while keeping the order of the page
def _cleanStreamingUrls(
        urls: list[str]
) -> list[str]:
    cleaned: list[str] = []

    for url in urls:
        url = url.replace("&amp;", "&").strip()

        if not url:
            continue

        if url in cleaned:
            continue

        cleaned.append(url)

    return cleaned


# Bandcamp only writes the stream urls into the html after the player was started once
def _getEmbeddedPlayerUrl(
        url: str,
        session
) -> str:
    trackHTML = html.getHtml(
        url=url,
        session=session
    )
    core.general.Validate.general.validateStr(argument_name="trackHTML", string=trackHTML,
                                              caller="[providers] Bandcamp._getEmbeddedPlayerUrl")

    embeddedplayer_pattern = r'<meta property="og:video".*?content="(https://bandcamp.com/EmbeddedPlayer.*?)">'
    embeddedPlayerUrl = core.general.DataSearch.searchBlocks(
        pattern=embeddedplayer_pattern,
        search_block=trackHTML
    )
    core.general.Validate.general.validateStr(argument_name="embeddedPlayerUrl", string=embeddedPlayerUrl,
                                              caller="[providers] Bandcamp._getEmbeddedPlayerUrl")

    return embeddedPlayerUrl


def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:
    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest,
        caller="[providers] Bandcamp.getMediaInformation"
    )

    urlType = _validateURL(
        url=request.url
    )

    streamingURLList, trackURLList = _extractStreamingURLs(
        url=request.url,
        urlType=urlType,
        session=request.ses
    )

    # Nothing in the html yet, so press play in the embedded player and read the page again
    if not streamingURLList:

        embeddedPlayerUrl = _getEmbeddedPlayerUrl(
            url=request.url,
            session=request.ses
        )

        browserResult = EmergencyBrowser.BrowserButtonPress(
            url=embeddedPlayerUrl,
            button_name="#big_play_button",
            cookie_file=request.ses.cookieFile
        )
        request.ses.reloadCookies()

        # Erst das html aus dem Player nehmen, das liegt schon da
        streamingURLList = _findStreamingUrls(browserResult["html"])
        trackURLList = [request.url] * len(streamingURLList)

        # Sonst die Seite mit den frischen Cookies noch einmal lesen
        if not streamingURLList:
            streamingURLList, trackURLList = _extractStreamingURLs(
                url=request.url,
                urlType=urlType,
                session=request.ses
            )

    if not streamingURLList:
        raise core.models.errors.TaskFailedError(
            task="[providers] Bandcamp.getMediaInformation",
            reason="Didn't find any streaming urls in the given page",
            extraMessages=[
                f"Given url: {request.url}",
                f"Resolved url type: {urlType}"
            ],
            caller="[providers] Bandcamp.getMediaInformation"
        )

    foundMediaList : list[models.FoundMedia] = []
    for url in streamingURLList:
        media = models.FoundMedia(
            url=url,
            stream_type=core.models.Download.DownloadType.FILE,
            extra_headers=request.extra_headers
        )
        foundMediaList.append(media)

    return models.makeProviderResult(
        foundMediaList,
        request,

    )

# def download(
#         download_information: core.models.Download.DownloadInformation,
#         retry = True
# ):
#     core.general.Validate.download.validateDownloadInformation(
#         argument_name="download_information",
#         download_information=download_information,
#         caller="[providers] Bandcamp.download"
#     )
#     core.general.Validate.general.validateBool(boolean=retry, argument_name="retry", caller="[providers] Bandcamp.download")

#     urlType = _validateURL(
#         url=download_information.url
#     )


#     streamingURLList, trackURLList = _extractStreamingURL(
#         url=download_information.url,
#         urlType=urlType,
#         session=download_information.session
#     )


#     for streamingURL, trackURL in zip(streamingURLList, trackURLList):

#         request = urllib.request.Request(
#             streamingURL,
#             method="GET",
#             headers={
#                 "Referer" : streamingURL,
#                 "Origin" : download_information.url,
#                 "Range": "bytes=0-",
#                 }
#             )


#         try:
#             core.download.File.downloadToFile(
#                 request=request,
#                 session=download_information.session,
#                 out_file=download_information.outFile,
#                 progress_dict=download_information.downloadProgress,

#             )
#         except urllib.error.HTTPError as e:
#             if e.code == 403 and retry and urlType !="streamURL":
#                 retry = False

#                 trackHTML = html.getHtml(
#                     url=trackURL,
#                     session=download_information.session
#                 )
#                 core.general.Validate.general.validateStr(argument_name="trackHTML", string=trackHTML, caller="[providers] Bandcamp.download.error")

#                 embeddedplayer_pattern = r'<meta property="og:video".*?content="(https://bandcamp.com/EmbeddedPlayer.*?)">'
#                 embeddedPlayerUrl = core.general.DataSearch.searchBlocks(
#                     pattern=embeddedplayer_pattern,
#                     search_block=trackHTML
#                 )
#                 core.general.Validate.general.validateStr(argument_name="embeddedPlayerUrl", string=embeddedPlayerUrl, caller="[providers] Bandcamp.download.error")

#                 EmergencyBrowser.BrowserButtonPress(url=embeddedPlayerUrl, button_name="#big_play_button")


#                 core.download.File.downloadToFile(
#                     request=request,
#                     session=download_information.session,
#                     out_file=download_information.outFile,
#                     progress_dict=download_information.downloadProgress

#                 )
#             else: raise