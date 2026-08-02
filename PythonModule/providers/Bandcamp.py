import PythonModule.core as core

from PythonModule.models.requests import SearchFilters
from PythonModule.models.exceptions import InvalidURL
import urllib.parse, urllib.request, urllib.error
import re
from PythonModule.models import processorModels


class BandCampSearchError(Exception): ...


def search(
        search: str,
        filters: SearchFilters,
        session: core.request.Session.Session,
        top: int = 5
) -> list[dict]:
    
    if not isinstance(search, str): raise ValueError("'search' must be an string")
    if not isinstance(filters, SearchFilters): raise ValueError("'filters' must be from type SearchFilters")
    if not isinstance(top, int) or top < 0: raise ValueError("'top' must be an integer above 0")
    
    searchURL = _buildSearchUrl(
                search=search,
            )
    
    def _getSearchHtml():
        html = core.general.Html.getHtml(
            url=searchURL,
            session=session
        )
        return html
         
    
    
    
    try:
        results= _get_searchResults(
            html=_getSearchHtml(),
            top=top,
            filters=filters   
        )
#Sometimes Bandcamp hates python and wants javascript to be executed
    except Exception:
        
        core.request.EmergencyBrowser.BrowserButtonPress(
            url=searchURL,
            button_name="",
            headless=False,
            wait_after_click_ms=20000,
            wait_before_click_ms=20000
        )
        session.reloadCookies()
        
        results= _get_searchResults(
                    html=_getSearchHtml(),
                    top=top,
                    filters=filters
                )
        



    return results
       





def _buildSearchUrl(
        search: str,
        
) -> list[str]:
    
   
    
    base_url = "https://bandcamp.com/search?"

    
    params = {
        "q" : search
    }
    searchURL = base_url + urllib.parse.urlencode(params)
    return searchURL
    





def _get_searchResults(
        html: str,
        top: int,
        filters: SearchFilters
        
)-> list[dict]:
    if not isinstance(html, str): raise ValueError("Please provide html to search")
    results = []
    


    
    result_items_pattern = r'<ul class="result-items">(.*?)</ul>'

    
    try:
        allTracks = core.general.DataSearch.searchBlocks(
            pattern=result_items_pattern,
            searchBlock=html,
            returnException=True
        )

    except core.general.DataSearch.RegexSearchError as error:
        raise BandCampSearchError(
            "BandcampSearch: Search results were not found. "
            "Bandcamp may have returned a JavaScript challenge."
        ) from error

    if not allTracks:
        raise BandCampSearchError(
            "BandcampSearch: Didn't find tracks with given HTML"
        )



    tracks = re.findall(
        r'<li class="searchresult.*?</li>',
        allTracks,
        re.DOTALL
    )
    
    

    for track in tracks:
        
        if len(results) >= top:
            break
        type_pattern = r'data-search=.*?(?:&quot;|")type(?:&quot;|")\s*:\s*(?:&quot;|")(.*?)(?:&quot;|")'
    
        
       
        trackType = core.general.DataSearch.searchBlocks(
            pattern=type_pattern,
            searchBlock=track
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
        searchBlock=track
    )
    titel_pattern = r'<div class="heading">.*?<a.*?>(.*?)</a>'
    dictionary['title'] = core.general.DataSearch.searchBlocks(
        pattern=titel_pattern,
        searchBlock=track
    )

    url_pattern = r'<div class="heading">.*?<a href="(.*?)"'
    dictionary['url'] = core.general.DataSearch.searchBlocks(
        pattern=url_pattern,
        searchBlock=track
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

    
    







def validateURL(
        url: str,
) -> str:
   

    if url.startswith("https://t4.bcbits.com/"):
        return "streamURL"
    
    elif url.startswith("https://") and "track" in url:
        return "trackURL"
    
    elif url.startswith("https://") and "album" in url:
        return "albumURL"
    
    else:

        raise InvalidURL(
            url=url,
            supported=["streamURL", "trackURL", "albumURL"]
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
            html = core.general.Html.getHtml(
            url=url,
            session=session
            )


            streamurl_pattern = r'(https://t4.bcbits.com/stream/.*?);}'

            streamingUrl = core.general.DataSearch.searchBlocks(
                pattern=streamurl_pattern,
                searchBlock=html
            )
            

            if not streamingUrl:
                raise ValueError(f"No streaming URL was found, can't download with given url {url}")
            
            return [streamingUrl], [url]
        
        case "albumURL":
            raise Exception("albumURL not yet supported")
        case _:
            raise Exception(f"None supported urlType was given. '{urlType}'")


    



def download(
        download_information: processorModels.DownloadInformations,
): 
    if not download_information or not isinstance(download_information, processorModels.DownloadInformations): raise ValueError("BandcampDownload: Given download information is either None or has the wrong type")
    
    urlType = validateURL(
        url=download_information.url
    )

    streamingURLList, trackURLList = _extractStreamingURL(
        url=download_information.url,
        urlType=urlType,
        session=download_information.session
    )
    
    
    retry = True
    for streamingURL, trackURL in zip(streamingURLList, trackURLList):
        
        request = urllib.request.Request(
            streamingURL,
            method="GET",
            headers={
                "Referer" : streamingURL,
                "Origin" : download_information.url,
                "Range": "bytes=0-",
                }   
            )


        try:
            core.download.File._downloadToFile(
                request=request,
                session=download_information.session,
                out_file=download_information.outFile,
                progress_dict=download_information.downloadProgress,
                
            )
        except urllib.error.HTTPError as e:
            if e.code == 403 and retry and urlType !="streamURL":
                retry = False

                trackHTML = core.general.Html.getHtml(
                    url=trackURL,
                    session=download_information.session
                )

                embeddedplayer_pattern = r'<meta property="og:video".*?content="(https://bandcamp.com/EmbeddedPlayer.*?)">'
                embeddedPlayerUrl = core.general.DataSearch.searchBlocks(
                    pattern=embeddedplayer_pattern,
                    searchBlock=trackHTML
                )
                if not embeddedPlayerUrl:
                    raise Exception

                core.request.EmergencyBrowser.BrowserButtonPress(url=embeddedPlayerUrl, button_name="#big_play_button")


                core.download.File._downloadToFile(
                    request=request,
                    session=download_information.session,
                    out_file=download_information.outFile,
                    progress_dict=download_information.downloadProgress

                )
            else: raise

        except Exception:
            raise


   

