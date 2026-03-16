import urllib.parse, urllib.request, urllib.error
from PythonModule.core import get_html
from PythonModule.models.requests import SearchFilters
import re
import time
from html import unescape
from PythonModule.emergencyBrowser import BrowserButtonPress

def search(
        search: str,
        filters: SearchFilters,
        session,
        top: int = 5
) -> list[dict]:
    
    if not isinstance(search, str): raise ValueError("'search' must be an string")
    if not isinstance(filters, SearchFilters): raise ValueError("'filters' must be from type SearchFilters")
    if not isinstance(top, int) or top < 0: raise ValueError("'top' must be an integer above 0")
    
    
    
    search_url = build_search_url(
        search=search,
        filters=filters
    )

    html = get_html(
        url=search_url,
        session=session
    )

    

    results =get_searchResults(
        html=html,
        top=top   
    )

    return results
       





def build_search_url(
        search: str,
        filters: SearchFilters
):
    if not isinstance(filters, SearchFilters): raise ValueError("'filters' must be from Type SearchFilters")
    
    base_url = "https://bandcamp.com/search?q="
    search_url = base_url + urllib.parse.quote(search)

    if isinstance(filters.creator, str) and filters.creator:
        search_url = search_url + urllib.parse.quote(filters.creator)

    return search_url





def get_searchResults(
        html: str,
        top: int
        
)-> list[dict]:
    if not isinstance(html, str): raise ValueError("Please provide html to search")
    results = []
    



    result_items_pattern = r'<ul class="result-items">(.*?)</ul>'


    allTracks = searchBlocks(
        pattern=result_items_pattern,
        searchBlock=html
    )


    tracks = re.findall(
        r'<li class="searchresult.*?</li>',
        allTracks,
        re.DOTALL
    )
    


    for track in tracks[:top]:
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

        results.append(dictionary)
        
        

    return results
        
    
    
    
    

    
    


def searchBlocks(
        pattern: str,
        searchBlock: str
):
    match = re.search(pattern, searchBlock, re.DOTALL)

    if match:
        result_block = match.group(1).strip()
        return result_block
    else:
        return ""




def download(
        url: str,
        session,
        progress_dict: dict,
        out_file: str,
        chunk_size: int = 8192
):
    html = get_html(
        url=url,
        session=session
    )
    streamurl_pattern = r'(https://t4.bcbits.com/stream/.*?);}'
    streamingUrl = searchBlocks(
        pattern=streamurl_pattern,
        searchBlock=html
    )
    
    embeddedplayer_pattern = r'<meta property="og:video".*?content="(https://bandcamp.com/EmbeddedPlayer.*?)">'
    embeddedPlayerUrl = searchBlocks(
        pattern=embeddedplayer_pattern,
        searchBlock=html
    )

    
    embeddedPlayer_request = urllib.request.Request(
        embeddedPlayerUrl,
        headers={
            "Origin" : url
        }
    )
    session.open(embeddedPlayer_request).read()
    
    
    request = urllib.request.Request(
        streamingUrl,
        method="GET",
        headers={
            "Referer" : streamingUrl,
            "Origin" : url,
            "Range": "bytes=0-",
        }
        
        
    )

    download_to_file(
        request=request,
        session=session,
        out_file=out_file,
        progress_dict=progress_dict,
        embeddedPlayerUrl=embeddedPlayerUrl
    )


   

def download_to_file(
        request,
        session,
        out_file:str,
        progress_dict: dict,
        embeddedPlayerUrl: str,
        chunk_size: int = 8192,
        retry: bool = True,
        
):
    try:
        with session.open(request) as response, open(out_file, "wb") as f:
            downloading = True

            progress_dict['status'] = "downloading..."

            total_size = int(response.headers.get("Content-Length", 0))
            progress_dict["totalBytes"] = total_size

            downloaded: int = 0
            start_time = time.time()

            while downloading:
                chunk = response.read(chunk_size)
                if not chunk:
                    downloading=False
                    break

                
                f.write(chunk)


                downloaded += len(chunk)
                percent = 100 / total_size * downloaded
                elapsed_time = time.time() - start_time
                


                progress_dict['downloadProgress'] = percent
                progress_dict['downloadedBytes'] = downloaded

                speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                if speed:
                    progress_dict["speed"] = round(speed / 1024 / 1024, 2)

        progress_dict['status'] = "complete"

    except urllib.error.HTTPError as e:
        if e.code == 403 and retry == True:
            print("Trying the emergency Browser")
            BrowserButtonPress(url=embeddedPlayerUrl, button_name="#big_play_button")
            download_to_file(
    request=request,
    session=session,
    out_file=out_file,
    progress_dict=progress_dict,
    embeddedPlayerUrl=embeddedPlayerUrl,
    retry=False
)
        else:
            raise



    except Exception:
        raise