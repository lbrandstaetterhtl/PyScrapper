# Core Imports
import PythonModule.core as core

#Python Default Imports

import urllib.error
import subprocess



MEDIATYPE_MAPPING = {
    core.models.media.MediaType.MASTER_M3U8 : core.download.HLS.DownloadM3U8FromMaster,
    core.models.media.MediaType.INDEX_M3U8 : core.download.HLS.DownloadM3U8FromIndex,
    core.models.media.MediaType.FILE : core.download.File.downloadToFile
    }


def download(
        download_information: core.models.General.DownloadInformations,
        retry_with_FFmpeg:bool = True
) -> None:

    core.general.Validate.validateDownloadInformation(
        argument_name="download_information",
        download_information=download_information,
        caller="[providers] Default.download"
    )
    core.general.Validate.validateBool(
        boolean=retry_with_FFmpeg,
        argument_name="retry_with_FFmpeg",
        caller="[providers] Default.download"
        )

    

    medialist: core.models.media.MediaList = core.request.EmergencyBrowser.BrowserDiscoverStreamURLs(
        url = download_information.url,
        ad_block=True,
        headless=True
    )

    if not medialist:
        raise core.models.errors.TaskFailedError(
            task="BrowserDiscoverStreamURLs",
            reason="Browser isn't currently capable of finding medias on given url",
            extraMessages=[f"Given url: {download_information.url}"]
        )
 

    try:
        for candidate in medialist.candidates:
            
            candidate: core.models.media.Media
            downloadFunction = MEDIATYPE_MAPPING.get(candidate.mediaType, None)
            
            if downloadFunction == None:
                raise core.models.errors.TaskFailedError(
                    task="MEDIATYPE_MAPPING.get()",
                    reason="Mediatype Mapping didn't give back a function",
                    extraMessages=["Mediatype Mapping only has functions for HLS and FILE download", f"Mediatype of the highest prio media: '{candidate.mediaType}'"],
                    caller="[providers] Default.download",
                )
           
            extraHeaders = candidate.headers.to_dict()
            
            if isinstance(downloadFunction, type):
                
                downloader = downloadFunction(
                    url = candidate.mediaUrl,
                    out_file = download_information.outFile,
                    session = download_information.session,
                    progress_dict = download_information.downloadProgress,
                    extra_headers = extraHeaders,

                )
                
                downloader.run()
                return
                
               

            else:
              
                downloadFunction(
                    url= candidate.mediaUrl,
                    out_file = download_information.outFile,
                    session = download_information.session,
                    progress_dict = download_information.downloadProgress,
                    extra_headers=extraHeaders,

                    
                
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


    



