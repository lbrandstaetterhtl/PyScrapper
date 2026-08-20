# Core Imports
import PythonModule.core as core
from PythonModule.core.network import EmergencyBrowser

from . import models

#Python Default Imports




def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:
    """
    Attempts to discover downloadable or streamable media from a webpage
    using the default provider.

    This function is intended as a best-effort fallback for websites that do
    not have a dedicated provider implementation. It analyzes media requests
    made by the webpage and tries to identify a suitable media resource such
    as a direct file, HLS playlist, or other supported stream.

    If successful, it returns media information containing a URL that can be
    used by the download/streaming system to access the discovered media.

    This default discovery method has been successfully tested with:
    - Aniworld.to
    - Dailymotion.com
    - Rumble.com
    - PeerTube.tv
    - Twitch videos (individual stream parts)
    - Imgur.com videos
    - Reddit videos
    - Threads.com posts
    - Tumblr.com
    - 9GAG.com

Websites with partial support:
    - Facebook videos:
        Either the audio or video stream is discovered, but not both.

    - VK Video:
        An MPEG-DASH (.mpd) manifest is discovered. DASH playback/download
        is currently not handled by the core, but the manifest URL can still
        be returned to the user for external playback or processing.

    - Bilibili:
        Audio can be discovered, but video delivery uses MPEG-DASH, which is
        currently not supported by the core.

    
    - Instagram reels video only

    Support for these websites is not guaranteed, as their delivery methods
    and website implementations may change at any time.
    """

    
    medialist: core.models.media.MediaList = EmergencyBrowser.BrowserDiscoverStreamURLs(
            url = request.url,
            ad_block=True,
            headless=True,
            extra_headers=request.extra_headers
        )

    if not medialist:
        medialist: core.models.media.MediaList = EmergencyBrowser.BrowserDiscoverStreamURLs(
            url = request.url,
            ad_block=True,
            headless=False,
            extra_headers=request.extra_headers
        )

    

    if not medialist:
        raise core.models.errors.TaskFailedError(
            task="BrowserDiscoverStreamURLs",
            reason="Browser isn't currently capable of finding medias on given url",
            extraMessages=[f"Given url: {request.url}"]
        )

    bestCandidate = medialist.candidates[0]
    result = models.makeProviderResultFromCandidate(bestCandidate)
    result.total_size = models.getFileInformations(session=request.ses, url=result.url, extra_headers=result.extra_headers)
    return result
    
    


    



