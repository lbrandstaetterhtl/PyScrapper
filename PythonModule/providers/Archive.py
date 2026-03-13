from PythonModule.core import get_html
import urllib.parse, urllib.request, urllib.error
import json, os, time

class ArchiveError(Exception): ...
class ArchiveSearchError(ArchiveError): ...
class ArchiveArgumentError(ArchiveError): ...
class ArchiveDownloadError(ArchiveError): ...



def search(
        search: str,
        session=None,
        top=5,
        chunk_size: int = 1024*512
)-> list[dict]:
    
    if not search:
        raise ArchiveArgumentError("No search query for archive was given")
    if not session:
        raise ArchiveArgumentError("No session was given to open the query with")
    
    query = f'(mediatype:audio OR mediatype:movies) AND title:("{search}")'

    params = {
        "q": query,
        "output": "json",
        "rows": top,
        "page": 1,
        "fl[]": ["identifier", "title"]
    }

    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params, doseq=True)
    request = urllib.request.Request(
        url,
        method="GET"
    )
    with session.open(request) as response:
        data = json.loads(response.read().decode("utf-8"))
    docs = data.get('response', {}).get("docs", [])
    docs_new = []
    for doc in docs:
        if not doc.get('identifier', None):
            continue
        doc['thumbnail'] = f"https://archive.org/download/{doc.get('identifier')}/__ia_thumb.jpg"
        doc['url'] = f"https://archive.org/metadata/{doc.get('identifier')}"
        docs_new.append(doc)
    return docs_new





def download(
        url: str,
        progress_dict: dict,
        session,
        out_file: str,
        mediatype=".mp3",
        chunk_size:int = 8096,
        
    ):

    if not url:
        raise ArchiveArgumentError("No Url was given for Archive download")
    if not isinstance(url, str) or not url.startswith(("https://archive.org/metadata", "https://www.archive.org/metadata", "www.archive.org/metadata", "archive.org/metadata")):
        raise ArchiveArgumentError("Invalid URL was given, wanted: 'https://archive.org/metadata/{identifier}'")
    
    if not session:
        raise ArchiveArgumentError("No session was given to open url with")
    
    if not progress_dict:
        raise ArchiveArgumentError("No dict to write progress in was given")
    
    
    metadata_url = url
    
    split = url.rstrip("/").split("/")
    identifier = split[-1]


    request = urllib.request.Request(
        metadata_url,
        method="GET"
    )
    with session.open(request) as response:
        metadata = json.loads(response.read().decode("utf-8"))

    found=False
    for file in metadata.get("files", []):
        name = file.get('name')
        if name.endswith(mediatype):
            found=True



            download_url = f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}"

            download_request = urllib.request.Request(
                download_url,
                method="GET"
            )

            
            progress_dict['status'] = "downloading..."
            download_to_file(session=session, download_request=download_request, out_file=out_file, progress_dict=progress_dict)
            break
    if not found:
        raise ArchiveDownloadError(f"No file with mediatype {mediatype} found in archive metadata")



           


        
def download_to_file(
        session,
        download_request,
        out_file: str,
        progress_dict: dict,
        chunk_size: int = 8096,
    
):
    
    if not session or not download_request or not progress_dict or not out_file:
        raise ArchiveArgumentError("Download to file needs a session, download_request and progress_dict to work")
    
    try:
        
        with session.open(download_request) as response, open(out_file, "wb") as f:
                total_size = response.headers.get("Content-Length")
                if total_size:
                    total_size = int(total_size)
                    progress_dict['totalBytes'] = total_size
                else:
                    raise ArchiveDownloadError("No content length was given from soruce wtf")

                downloaded:int = 0
                start_time = time.time()

                downloading = True
        
                while downloading:
    
                    chunk = response.read(chunk_size)
                    if not chunk:
                        downloading = False
                        break
                       
                    
                    f.write(chunk)

                    downloaded += len(chunk)
                    percent = 100 / total_size * downloaded
                    elapsed_time = time.time() - start_time

                    progress_dict['downloadProgress'] = percent
                    progress_dict['downloadedBytes'] = downloaded

                    speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                    if speed:
                        progress_dict['speed'] = round(speed / 1024 / 1024, 2)
            
                progress_dict['status'] = "complete"
        
    except urllib.error.HTTPError as e:
        raise
    
    except urllib.error.URLError as e:
        raise



    

        


