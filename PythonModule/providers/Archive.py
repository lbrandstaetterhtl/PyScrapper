#Core Imports
import PythonModule.core as core
from PythonModule.models.requests import SearchFilters

#Own imports

from . import models


#Python Default Imports
import urllib.parse
import json




class ArchiveError(Exception): ...
class ArchiveSearchError(ArchiveError): ...
class ArchiveArgumentError(ArchiveError): ...
class ArchiveDownloadError(ArchiveError): ...



def search(
        search_term: str,
        session=None,
        filters: SearchFilters = None,
        top=5,

)-> list[dict]:
    core.general.Validate.general.validateStr(argument_name="search_term", string=search_term, caller="[providers] Archive.search")
    core.general.Validate.special.validateSession(session=session, argument_name="session", caller="[providers] Archive.search")
    core.general.Validate.general.validateInt(argument_name="top", integer=top, caller="[providers] Archive.search")
    
    query = f'(mediatype:audio OR mediatype:movies) AND title:("{search_term}")'

    params = {
        "q": query,
        "output": "json",
        "rows": top,
        "page": 1,
        "fl[]": ["identifier", "title"]
    }

    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params, doseq=True)
    
    with session.open(url=url) as response:
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






def getMediaInformation(
        request: models.ProviderResultRequest,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="Soundcloud.getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_hostnames_list=["archive.org", "www.archive.org"],
        caller="[providers] Archive.getMediaInformation"
    )

    with request.ses.open(url=request.url, headers=request.extra_headers) as response:
        metadata = json.loads(response.read().decode("utf-8"))


    bestFile: str | None = None

    bestPriority: int = 0

    identifier = request.url.rstrip("/").split("/")[-1]

#Looking every file and priorites them. since this is used by a video/audio download containers like mkv are more important than mp3
#Saves the file with highest priority and result will be that file
    for file in metadata.get("files", []):
        name: str = file.get('name')
        

        if not name:
            continue

        source = file.get("source")

        extension = name.rsplit(".", 1)[-1]
        prio = models.MEDIA_EXTENSION_PRIORITY.get(extension.lower(), None)

        if prio is None:
            continue

        if source and source == "original":
            prio += 15

        if prio > bestPriority:
            bestPriority = prio
            bestFile = name
            

    if bestFile is None:
        raise core.models.errors.TaskFailedError(
            task="Archive.getMediaInformation",
            reason="No supported audio/video file found",
            extraMessages=[
                f"Used metadata url: {request.url}"
            ],
            caller="[providers] Archive.getMediaInformation"
        )
 
    downloadUrl: str = f"https://archive.org/download/{identifier}/{urllib.parse.quote(bestFile)}"

    fileEnding = models.getContentType(downloadUrl, request.ses, request.extra_headers)

    return models.makeProviderResult(
        url=downloadUrl,
        fileending=fileEnding,
        type = core.models.Download.DownloadType.FILE,
        extra_headers=request.extra_headers

    )

    
    






#def download(
#        download_information: core.models.Download.DownloadInformation,
        
#    ):

#    core.general.Validate.download.validateDownloadInformation(argument_name="download_information", download_information=download_information, caller="[providers] Archive.download")
    
#    metadata_url = download_information.url
    
#    split = download_information.url.rstrip("/").split("/")
#    identifier = split[-1]


#    with download_information.session.open(url=metadata_url) as response:
#        metadata = json.loads(response.read().decode("utf-8"))

#    found:bool = True

#    foundMedia: list[str] = []

#    for file in metadata.get("files", []):
#        name: str = file.get('name')
#        foundMedia.append(name)
#        if name.endswith(download_information.fileending):
#            found = True
#
#            download_url = f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}"

#            download_information.downloadProgress['status'] = "downloading..."
#            core.download.File.downloadToFile(
#                url=download_url,
#                out_file=download_information.outFile,
#                session=download_information.session,
#                progress_dict=download_information.downloadProgress,

#                )
#            break

#    if not found:
#        raise core.models.errors.TaskFailedError(
#            task="metadata.get()",
#            reason=f"No file with mediatype {download_information.fileending}",
#            extraMessages=["If any other ressources were found, it will get listed here", f"Found ressources: {', '.join(foundMedia)}"],
#            caller="[providers] Archive.download"
#        )
#        raise ArchiveDownloadError(f"No file with mediatype {download_information.fileending} found in archive metadata")



           





    

        


