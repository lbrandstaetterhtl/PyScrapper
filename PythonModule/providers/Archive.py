from __future__ import annotations
import PythonModule.core as core
import urllib.parse, urllib.request, urllib.error
import json
from PythonModule.models import processorModels
from PythonModule.models.requests import SearchFilters

class ArchiveError(Exception): ...
class ArchiveSearchError(ArchiveError): ...
class ArchiveArgumentError(ArchiveError): ...
class ArchiveDownloadError(ArchiveError): ...



def search(
        search: str,
        session=None,
        filters: SearchFilters = None,
        top=5,

)-> list[dict]:
    
    if not search:
        raise ArchiveArgumentError("No search query for archive was given")
    if not session:
        raise ArchiveArgumentError("No session was given to open the query with")
    if not isinstance(top, int) or top < 0: raise ValueError("'top' must be an integer above 0")
    
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
        download_information: processorModels.DownloadInformations,
        
    ):

    if not download_information or not isinstance(download_information, processorModels.DownloadInformations): raise ValueError("ArchiveDownload: Given download information is either None or has the wrong type")
    
    metadata_url = download_information.url
    
    split = download_information.url.rstrip("/").split("/")
    identifier = split[-1]


    request = urllib.request.Request(
        metadata_url,
        method="GET"
    )
    with download_information.session.open(request=request) as response:
        metadata = json.loads(response.read().decode("utf-8"))

    found=False
    for file in metadata.get("files", []):
        name = file.get('name')
        if name.endswith(download_information.fileending):
            found=True



            download_url = f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}"

            download_request = urllib.request.Request(
                download_url,
                method="GET"
            )

            
            download_information.downloadProgress['status'] = "downloading..."
            core.download.File._downloadToFile(
                request=download_request,
                out_file=download_information.outFile,
                session=download_information.session,
                progress_dict=download_information.downloadProgress,

                )
            break

    if not found:
        raise ArchiveDownloadError(f"No file with mediatype {download_information.fileending} found in archive metadata")



           





    

        


