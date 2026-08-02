import PythonModule.core as core

from PythonModule.models import processorModels

import urllib.error

import subprocess

MEDIATYPE_MAPPING = {
    core.models.media.MediaType.MASTER_M3U8 : core.download.HLS.DownloadM3U8FromMaster,
    core.models.media.MediaType.INDEX_M3U8 : core.download.HLS.DownloadM3U8FromIndex,
    core.models.media.MediaType.FILE : core.download.File._downloadToFile
    }






def download(
        download_information: processorModels.DownloadInformations,
        retry_with_FFmpeg:bool = False
) -> None:

    

    if not download_information or not isinstance(download_information, processorModels.DownloadInformations):
        raise ValueError("DefaultDownload: Given download information is either None or has the wrong type")

    medialist: core.models.media.MediaList = core.request.EmergencyBrowser.BrowserDiscoverStreamURLs(
        url = download_information.url,
        ad_block=True,
        headless=True
    )

    if not medialist:
        raise ValueError(f"[ERROR] DefaultDownload: Current Code isn't capable of finding media on url '{download_information.url}'")
    print("DefaultDownload: Successfully found media for download")

    try:
        for candidate in medialist.candidates:
            
            candidate: core.models.media.Media
            downloadFunction = MEDIATYPE_MAPPING.get(candidate.mediaType, None)
            
            
            if not downloadFunction:
                raise ValueError("DefaultDownload: Valid Media was found but the download isn't supported yet. Only direct files and HLS Streaming is currently supported")

            
            if isinstance(downloadFunction, type):
                
                downloader = downloadFunction(
                    url = candidate.mediaUrl,
                    out_file = download_information.outFile,
                    session = download_information.session,
                    progress_dict = download_information.downloadProgress
                )
                
                downloader.run()
                return
                
               

            else:
              
                downloadFunction(
                    url= candidate.mediaUrl,
                    out_file = download_information.outFile,
                    session = download_information.session,
                    progress_dict = download_information.downloadProgress,
                
                )
                return
                
            
            
            
    except urllib.error.HTTPError as e:
        if e.code == 403 and retry_with_FFmpeg == True:
            print("GeneralDownload: Couldn't download because of 403 http error. Trying with curl/ffmpeg")
            command: str = core.general.CurlToFFMPEG.get_curlToFFmpeg(
                candidate.curlCommand,
                output=download_information.outFile
            )

            subprocess.run(
                command,
                shell=True,
                check=True,
            )
    
        else:
            raise
    except Exception:
        raise


    



