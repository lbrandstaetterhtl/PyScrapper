# Core Imports
import PythonModule.core as core
from PythonModule.core.network import EmergencyBrowser
from PythonModule.core.network.Session import Session
from PythonModule.models.requests import SearchFilters

from PythonModule.core.network import html

from .. import models


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