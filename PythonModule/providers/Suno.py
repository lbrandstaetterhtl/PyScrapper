#Core Imports
import PythonModule.core as core







def _searchMedia(
        html: str,
        mediatype: str = ".mp4",
        identifier: str = None
) -> str:
    wav = None
    core.general.Validate.validateStr(argument_name="html", string=html, caller="[providers] Suno._searchMedia")
    core.general.Validate.validateStr(argument_name="identifier", string=identifier, caller="[providers] Suno._searchMedia")
    core.general.Validate.validateStr(argument_name="mediatype", string=mediatype, caller="[providers] Suno._searchMedia")


    mediaPattern = rf"https://cdn1.suno.ai/{identifier}{mediatype}"
    
    songUrl:str = core.general.DataSearch.searchBlocks(mediaPattern, html, return_regex_exception=True)

    return songUrl







def download (
        download_information: core.models.General.DownloadInformations,  
        
):
    core.general.Validate.validateDownloadInformation(argument_name="download_information", download_information=download_information, caller="[providers] Suno.download")
    core.general.Validate.validateHostPro(
        url=download_information.url,
        allowed_hostnames_list=["suno.com/", "www.suno.com/", "104.20.16.212", "172.66.144.155"],
        caller="[providers] Suno.download"
        )

    html = core.general.Html.getHtml(url=download_information.url, session=download_information.session)
    core.general.Validate.validateStr(argument_name="html", string=html, caller="[providers] Suno.download")


    strip = download_information.url.replace("https://suno.com/song/", "")
    identifier = strip

    songUrl = _searchMedia(html=html, identifier=identifier, mediatype=download_information.fileending)

    
    core.download.File.downloadToFile(
        url=songUrl, out_file=download_information.outFile,
        session=download_information.session,
        progress_dict=download_information.downloadProgress
        )

