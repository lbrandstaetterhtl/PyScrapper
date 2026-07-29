import PythonModule.core as core
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
    with session.open(request=request) as response:
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
        raise ArchiveArgumentError("ArchiveDownload: Invalid URL was given, wanted: 'https://archive.org/metadata/{identifier}'")
    
    if not session:
        session = core.request.Session.Session()
    
    if not progress_dict or not isinstance(progress_dict, dict):
        raise ArchiveArgumentError("ArchiveDownload: Either no Dictionary to write to was given or given object wasn't a Python dictionary")
    
    
    metadata_url = url
    
    split = url.rstrip("/").split("/")
    identifier = split[-1]


    request = urllib.request.Request(
        metadata_url,
        method="GET"
    )
    with session.open(request=request) as response:
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
            core.download.File._downloadToFile(
                request=download_request,
                out_file=out_file,
                session=session,
                progress_dict=progress_dict,
                chunk_size=chunk_size
                )
            break

    if not found:
        raise ArchiveDownloadError(f"No file with mediatype {mediatype} found in archive metadata")



           





    

        


