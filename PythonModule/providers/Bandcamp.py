from PythonModule.emergencyBrowser import BrowserButtonPress
import PythonModule.core as core
from PythonModule.models.requests import SearchFilters
from PythonModule.models.exceptions import InvalidURL
import urllib.parse, urllib.request, urllib.error
import re




def search(
        search: str,
        filters: SearchFilters,
        session,
        top: int = 5
) -> list[dict]:
    
    if not isinstance(search, str): raise ValueError("'search' must be an string")
    if not isinstance(filters, SearchFilters): raise ValueError("'filters' must be from type SearchFilters")
    if not isinstance(top, int) or top < 0: raise ValueError("'top' must be an integer above 0")
    
    
    
    searchURL = build_search_url(
        search=search,
    )

    
    html = core.get_html(
        url=searchURL,
        session=session
    )
         
    

    
    
    results= get_searchResults(
        html=html,
        top=top,
        filters=filters   
    )

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


    allTracks = searchBlocks(
        pattern=result_items_pattern,
        searchBlock=html
    )
    if allTracks is None:
        raise ValueError("Didn't find tracks with given html")


    tracks = re.findall(
        r'<li class="searchresult.*?</li>',
        allTracks,
        re.DOTALL
    )
    
    

    for track in tracks:
        if len(results) >= top:
            break
        type_pattern = r'data-search=.*?(?:&quot;|")type(?:&quot;|")\s*:\s*(?:&quot;|")(.*?)(?:&quot;|")'
    
        
       
        trackType = searchBlocks(
            pattern=type_pattern,
            searchBlock=track
        )
        MyType = typeMapping(trackType)
        if MyType is None:
                
            continue
    
        if filters.tags:
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

    dictionary['thumbnail'] = searchBlocks(
        pattern=thumbnail_pattern,
        searchBlock=track
    )
    titel_pattern = r'<div class="heading">.*?<a.*?>(.*?)</a>'
    dictionary['title'] = searchBlocks(
        pattern=titel_pattern,
        searchBlock=track
    )

    url_pattern = r'<div class="heading">.*?<a href="(.*?)"'
    dictionary['url'] = searchBlocks(
        pattern=url_pattern,
        searchBlock=track
    )
    dictionary["type"] = typeGiven 
    return dictionary  
    
    


def typeMapping(givenType: str) -> str:
    mapping = {
        "t" : "track",
        "a" : "album"
    }
    return mapping.get(givenType, None)

    
    


def searchBlocks(
        pattern: str,
        searchBlock: str
):
    match = re.search(pattern, searchBlock, re.DOTALL)

    if match:
        result_block = match.group(1).strip()
        return result_block
    else:
        return None





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
        supported = ["streamURL", "trackURL", "albumURL"]
        raise InvalidURL(
            url=url,
            supported=supported
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
            html = core.get_html(
            url=url,
            session=session
            )


            streamurl_pattern = r'(https://t4.bcbits.com/stream/.*?);}'

            streamingUrl = searchBlocks(
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
            core.download_to_file(
                request=request,
                session=session,
                out_file=out_file,
                progress_dict=progress_dict,
                
            )
        except urllib.error.HTTPError as e:
            if e.code == 403 and retry and urlType !="streamURL":
                retry = False

                trackHTML = core.get_html(
                    url=trackURL,
                    session=session
                )

                embeddedplayer_pattern = r'<meta property="og:video".*?content="(https://bandcamp.com/EmbeddedPlayer.*?)">'
                embeddedPlayerUrl = searchBlocks(
                    pattern=embeddedplayer_pattern,
                    searchBlock=trackHTML
                )
                if not embeddedPlayerUrl:
                    raise Exception

                BrowserButtonPress(url=embeddedPlayerUrl, button_name="#big_play_button")


                core.download_to_file(
                    request=request,
                    session=session,
                    out_file=out_file,
                    progress_dict=progress_dict

                )
            else: raise

        except Exception:
            raise


   

