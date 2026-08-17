#Core Imports
import PythonModule.core as core
from PythonModule.core.network import EmergencyBrowser
from PythonModule.core.network.Session import Session
from PythonModule.models.requests import SearchFilters

from PythonModule.core.network import html

#Own imports

from . import models

#Python Default Imports
import urllib.parse, urllib.request, urllib.error




class BandCampSearchError(Exception): ...


def search(
        search_term: str,
        filters: SearchFilters,
        session: Session,
        top: int = 5
) -> list[dict]:

    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Bandcamp.search")
    core.general.Validate.general.validateGeneralType(argument_name="filters", obj=filters, objType=SearchFilters, caller="[providers] Bandcamp.search")
    core.general.Validate.special.validateSession(session=session, argument_name="session", caller="[providers] Bandcamp.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Bandcamp.search")
    searchURL = _buildSearchUrl(
                search_term=search_term,
            )
    
    def _getSearchHtml():
        searchHtml = html.getHtml(
            url=searchURL,
            session=session
        )
        core.general.Validate.general.validateStr(argument_name="searchHtml", string=searchHtml, caller="[providers] Bandcamp._getSearchHtml")
        return searchHtml
         
    
    
    
    try:
        results= _get_searchResults(
            searchHtml=_getSearchHtml(),
            top=top,
            filters=filters   
        )
#Sometimes Bandcamp hates python and wants javascript to be executed
    except Exception:
        
        EmergencyBrowser.BrowserButtonPress(
            url=searchURL,
            button_name="",
            headless=False,
            wait_after_click_ms=15000,
            wait_before_click_ms=10000
        )
        session.reloadCookies()
        
        results= _get_searchResults(
                    searchHtml=_getSearchHtml(),
                    top=top,
                    filters=filters
                )

 

    return results
       





def _buildSearchUrl(
        search_term: str,
        
) -> list[str]:
    
    base_url = "https://bandcamp.com/search?"

    
    params = {
        "q" : search_term
    }
    searchURL = base_url + urllib.parse.urlencode(params)
    return searchURL
    





def _get_searchResults(
        searchHtml: str,
        top: int,
        filters: SearchFilters
        
)-> list[dict]:

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
            extraMessages=["Maybe Bandcamp wants the user to solve captcha.", "Try sending a headful browser and see if there is javascript or captchas that needs to be solved"],
            caller="[providers] Bandcamp._get_searchResults",
        )
    tracks = core.general.DataSearch.searchBlocksAll(pattern=r'<li class="searchresult.*?</li>', search_block=allTracks, return_regex_exception=True)


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
        
#Default "nothing" that gets sended for tags is [''] that's why filtering for that    
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
        "t" : "track",
        "a" : "album",
        "b" : "creator"
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
    




def _extractStreamingURL(
        urlType: str,
        url: str,
        session
) -> list[str]:
    
    match urlType:
        case "streamURL":
            streamingURL = url
            return [streamingURL],[None]
        
        case "trackURL":
            trackHtml = html.getHtml(
            url=url,
            session=session
            )
            core.general.Validate.general.validateStr(argument_name="trackHtml", string=trackHtml, caller="[providers] Bandcamp._extractStreamingUrl")
            with open("test.html", "w", encoding="utf-8") as f:
                f.write(trackHtml)


            streamurl_pattern = r'(https://t4.bcbits.com/stream/.*?);}'

            streamingUrl = core.general.DataSearch.searchBlocks(
                pattern=streamurl_pattern,
                search_block=trackHtml,
                return_regex_exception=True
            )
            

            
            return [streamingUrl], [url]
        
        case "albumURL":
            raise Exception("albumURL not yet supported")
        case _:
            raise core.models.errors.TaskFailedError(
                task="match urlType",
                reason=f"None supported urltype '{urlType}' was given",
                caller="[providers] Bandcamp._extractStreamingURL"
            )
       


def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:
    urlType = _validateURL(
        url=request.url
    )
    print("test")
    print(request.url)
    streamingURLList, trackURLList = _extractStreamingURL(
        url=request.url,
        urlType=urlType,
        session=request.ses
    )
    url = streamingURLList[0]
    retry = True
    try:
        extension = models.getContentType(url, request.ses)
    except Exception:
        if retry == True:
            trackHTML = html.getHtml(
                    url=request.url,
                    session=request.ses
                 )
            core.general.Validate.general.validateStr(argument_name="trackHTML", string=trackHTML, caller="[providers] Bandcamp.download.error")

            embeddedplayer_pattern = r'<meta property="og:video".*?content="(https://bandcamp.com/EmbeddedPlayer.*?)">'
            embeddedPlayerUrl = core.general.DataSearch.searchBlocks(
                    pattern=embeddedplayer_pattern,
                    search_block=trackHTML
            )
            core.general.Validate.general.validateStr(argument_name="embeddedPlayerUrl", string=embeddedPlayerUrl, caller="[providers] Bandcamp.download.error")

            EmergencyBrowser.BrowserButtonPress(url=embeddedPlayerUrl, button_name="#big_play_button")
            extension = models.getContentType(url, request.ses)

    

    result:models.ProviderResult = models.makeProviderResult(
        url,
        extension,
        core.models.Download.DownloadType.FILE,
        )
    result.total_size = models.getFileInformations(session=request.ses, url=url, extra_headers=request.extra_headers)
    return result
    
    
    
    
        
        


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

        


   

