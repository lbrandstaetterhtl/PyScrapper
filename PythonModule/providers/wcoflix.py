import PythonModule.core as core
import urllib.request, urllib.parse
import gzip
import zlib

import subprocess

from PythonModule.models import processorModels





    


iFramePattern = r'<iframe[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>'

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:149.0) Gecko/20100101 Firefox/149.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Sec-Fetch-Storage-Access": "none",
    "Connection": "keep-alive",
    "Referer": "https://www.wcoflix.tv/",
    "Cookie": "PHPSESSID=fir8vjjgm4b0qcm41be8sp6ire",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "DNT": "1",
    "Sec-GPC": "1",
    "Priority": "u=4",
    "TE": "trailers",
}


def download(
        download_information: processorModels.DownloadInformations,
        retry_with_FFmpeg: bool = True
): 
    if not download_information or not isinstance(download_information, processorModels.DownloadInformations): raise ValueError("wcoflixDownload: Given download information is either None or has the wrong type")
    episodeHtml: str = core.general.Html.getHtml(
        download_information.session,
        download_information.url
    )

    indexUrl: str = core.general.DataSearch.searchBlocks(
        iFramePattern, 
        episodeHtml
    )
    indexRequest: str = urllib.request.Request(
        indexUrl,
        headers=headers
    )

    with download_information.session.open(
        request=indexRequest
    ) as response:
        indexHTMLRaw = response.read()
        encoding = response.headers.get("Content-Encoding", "").lower()

    if encoding == "gzip":
        indexHTMLRaw = gzip.decompress(indexHTMLRaw)
    elif encoding == "deflate":
        indexHTMLRaw = zlib.decompress(indexHTMLRaw)

    

    medialist: core.models.media.MediaList = core.request.EmergencyBrowser.WCOFLIXBrowserDiscoverStreamUrls(
        indexUrl,
        headless=True,
        ad_block=True,
        extra_headers={
            "Referer": "https://www.wcoflix.tv/"
        }
    )
    if not medialist:
        raise ValueError("wcoflixDownload: No media was found, since this is wcoflix I don't trust the provider. Please try again in a few minutes with the same task")
    candiate: core.models.media.Media = medialist.candidates[-1]

    extraHeaders = candiate.headers.to_dict()
    core.download.File._downloadToFile(
        download_information.outFile,
        session=download_information.session,
        url=candiate.mediaUrl,
        extra_headers=extraHeaders
    )
    
                

    





