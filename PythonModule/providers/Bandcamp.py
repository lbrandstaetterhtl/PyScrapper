import PythonModule.core as core

from PythonModule.models.requests import SearchFilters
from PythonModule.models.exceptions import InvalidURL
import urllib.parse, urllib.request, urllib.error
import re


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
    
    searchURL = build_search_url(
                search=search,
            )
    
    def _getSearchHtml():
        html = core.general.Html.getHtml(
            url=searchURL,
            session=session
        )
        return html
         
    
    
    
    try:
        results= get_searchResults(
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
        
        results= get_searchResults(
                    html=_getSearchHtml(),
                    top=top,
                    filters=filters
                )
        


    print(results)
    return results
       





def build_search_url(
        search: str,
        
) -> list[str]:
    
   
    
    base_url = "https://bandcamp.com/search?"

    
    params = {
        "q" : search
    }
    searchURL = base_url + urllib.parse.urlencode(params)
    return searchURL
    





def get_searchResults(
        html: str,
        top: int,
        filters: SearchFilters
        
)-> list[dict]:
    if not isinstance(html, str): raise ValueError("Please provide html to search")
    results = []
    


    
    result_items_pattern = r'<ul class="result-items">(.*?)</ul>'

    
    try:
        allTracks = core.general.RegexFind.searchBlocks(
            pattern=result_items_pattern,
            searchBlock=html,
            returnException=True
        )

    except core.general.RegexFind.RegexSearchError as error:
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
    
        
       
        trackType = core.general.RegexFind.searchBlocks(
            pattern=type_pattern,
            searchBlock=track
        )
        MyType = typeMapping(trackType)
        
#Default "nothing" that gets sended for tags is [''] that's why filtering for that    
        if filters.tags != ['']:
            
            if MyType not in filters.tags:
                continue
            
        result = buildResult(
            track=track,
            typeGiven=MyType
            
        )
                   
        results.append(result)
                

    return results
        
    


def buildResult(
        track: str,
        typeGiven: str

) -> dict:
    dictionary = {}
    thumbnail_pattern = r'<img src="(.*?)">'

    dictionary['thumbnail'] = core.general.RegexFind.searchBlocks(
        pattern=thumbnail_pattern,
        searchBlock=track
    )
    titel_pattern = r'<div class="heading">.*?<a.*?>(.*?)</a>'
    dictionary['title'] = core.general.RegexFind.searchBlocks(
        pattern=titel_pattern,
        searchBlock=track
    )

    url_pattern = r'<div class="heading">.*?<a href="(.*?)"'
    dictionary['url'] = core.general.RegexFind.searchBlocks(
        pattern=url_pattern,
        searchBlock=track
    )
    dictionary["type"] = typeGiven 
    return dictionary  
    
    


def typeMapping(givenType: str) -> str:
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
    




def extractStreamingURL(
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

            streamingUrl = core.general.RegexFind.searchBlocks(
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
        url: str,
        session,
        progress_dict: dict,
        out_file: str,
):
    
    urlType = validateURL(
        url=url
    )

    streamingURLList, trackURLList = extractStreamingURL(
        url=url,
        urlType=urlType,
        session=session
    )
    
    
    retry = True
    for streamingURL, trackURL in zip(streamingURLList, trackURLList):
        
        request = urllib.request.Request(
            streamingURL,
            method="GET",
            headers={
                "Referer" : streamingURL,
                "Origin" : url,
                "Range": "bytes=0-",
                }   
            )


        try:
            core.download.File._downloadToFile(
                request=request,
                session=session,
                out_file=out_file,
                progress_dict=progress_dict,
                
            )
        except urllib.error.HTTPError as e:
            if e.code == 403 and retry and urlType !="streamURL":
                retry = False

                trackHTML = core.general.Html.getHtml(
                    url=trackURL,
                    session=session
                )

                embeddedplayer_pattern = r'<meta property="og:video".*?content="(https://bandcamp.com/EmbeddedPlayer.*?)">'
                embeddedPlayerUrl = core.general.RegexFind.searchBlocks(
                    pattern=embeddedplayer_pattern,
                    searchBlock=trackHTML
                )
                if not embeddedPlayerUrl:
                    raise Exception

                core.request.EmergencyBrowser.BrowserButtonPress(url=embeddedPlayerUrl, button_name="#big_play_button")


                core.download.File._downloadToFile(
                    request=request,
                    session=session,
                    out_file=out_file,
                    progress_dict=progress_dict

                )
            else: raise

        except Exception:
            raise


   

