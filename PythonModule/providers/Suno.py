#Core Imports
from PythonModule.core.network import html
from PythonModule.core.network import EmergencyBrowser
import PythonModule.core as core
from PythonModule.models.requests import SearchFilters

from . import models
import urllib.parse
import json





#def _searchMedia(
#        html: str,
#        mediatype: str = ".mp4",
#        identifier: str = None
#) -> str:

#    core.general.Validate.general.validateStr(argument_name="html", string=html, caller="[providers] Suno._searchMedia")
#    core.general.Validate.general.validateStr(argument_name="identifier", string=identifier, caller="[providers] Suno._searchMedia")
#    core.general.Validate.general.validateStr(argument_name="mediatype", string=mediatype, caller="[providers] Suno._searchMedia")


#    mediaPattern = rf"https://cdn1.suno.ai/{identifier}{mediatype}"
    
#    songUrl:str = core.general.DataSearch.searchBlocks(mediaPattern, html, return_regex_exception=True)

#    return songUrl

def _buildSearchUrl(term: str):
    
        baseUrl: str = "https://suno.com/explore"
        params = {
            "q" : term,
            "type" : "public_song"
        }
        url = f"{baseUrl}?{urllib.parse.urlencode(params)}"
        return url
    

def search(
        search_term: str,
        session=None,
        filters: SearchFilters = None,
        top=5,

)-> list[dict]:
    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Suno.search")
    core.general.Validate.special.validateSession(session=session, argument_name="session", caller="[providers] Suno.search")


    url = "https://studio-api-prod.suno.com/api/unified/feed"

    payload = {
        "feed_id": "omnisearch_songs",
        "cursor": None,
        "page_size": top,
        "request_metadata": {
            "term": search_term
        }
    }

    body = json.dumps(payload).encode("utf-8")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),

        "Accept": "application/json",
        "Accept-Language": "en",


        "Accept-Encoding": "identity",

        "Content-Type": "application/json",

        "Origin": "https://suno.com",
        "Referer": "https://suno.com/",

        "browser-token": json.dumps({
            "token": "eyJ0aW1lc3RhbXAiOjE3ODY5NjQ4NDAzOTV9"
        }),

        "device-id": "ae436bfd-8fdd-4647-a571-5ccc7a9c0dc1",

        "DNT": "1",
        "Sec-GPC": "1",
    }

    request = urllib.request.Request(
        url=url,
        data=body,
        headers=headers,
        method="POST"
    )

    with session.open(request=request) as response:
        raw = response.read()
        text = raw.decode("utf-8")
        jsonData = json.loads(text)

 
    results: list[dict] = []
    for item in jsonData["feed"]["items"]:

        if len(results) == top:
            break

        content = item.get("content_item")
        thumbnail = content.get("image_url")
        title = content.get("title")
        id = content.get("id")
        result = {
            "thumbnail" : thumbnail,
            "title" : title,
            "url" : f"https://suno.com/song/{id}",
            "type" : "track"
        }
        
        results.append(result)

    return results








def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="Soundcloud.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=["suno.com", "www.suno.com"],
        caller="[providers] Suno.getMediaInformation"
    )

    def _getUrls():

        siteHtml = html.getHtml(
            session=request.ses,
            url=request.url,
            extra_headers=request.extra_headers
        )

        cdnPattern = r'\\?"(?:audio|video)_url\\?":\\?"(https://cdn\d+\.suno\.ai/[^"\\]+)'

        return core.general.DataSearch.searchBlocksAll(
            pattern=cdnPattern,
            search_block=siteHtml,
            return_regex_exception=True
        )
    try:
        allUrls:list[str] = _getUrls()

    except Exception:
#if there aren't urls found it will probably because of captcha
        EmergencyBrowser.BrowserButtonPress(
            url=request.url,
            button_name="",
            headless=False,
            wait_after_click_ms=20000,
            wait_before_click_ms=20000
        )
        request.ses.reloadCookies()

    identifier: str = request.url.rstrip(".")[0].split("/", 1)[-1]

    allUrls = _getUrls()


    foundMediaList: list[models.FoundMedia] = []

    for url in allUrls:
        
        if identifier not in url:
            continue

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
        
    



    
    


#def download (
#        download_information: core.models.General.DownloadInformations,  
        
#):
#    core.general.Validate.validateDownloadInformation(argument_name="download_information", download_information=download_information, caller="[providers] Suno.download")
#    core.general.Validate.validateHostPro(
#        url=download_information.url,
#        allowed_hostnames_list=["suno.com/", "www.suno.com/", "104.20.16.212", "172.66.144.155"],
#        caller="[providers] Suno.download"
#        )
#
  #  html = core.general.Html.getHtml(url=download_information.url, session=download_information.session)
 #   core.general.Validate.validateStr(argument_name="html", string=html, caller="[providers] Suno.download")
#
#
 #   strip = download_information.url.replace("https://suno.com/song/", "")
#    identifier = strip

#    songUrl = _searchMedia(html=html, identifier=identifier, mediatype=download_information.fileending)

#    
#    core.download.File.downloadToFile(
#        url=songUrl, out_file=download_information.outFile,
#        session=download_information.session,
#        progress_dict=download_information.downloadProgress
#        )

