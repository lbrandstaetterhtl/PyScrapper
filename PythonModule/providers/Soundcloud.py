import PythonModule.core as core
import urllib.error
import asyncio
import subprocess

from PythonModule.models import processorModels

async def run_shell_command_async(command: str):
        await asyncio.to_thread(
            subprocess.run,
            command,
            shell=True,
            check=True,
            executable="/bin/bash"
        )

MEDIATYPE_MAPPING = {
    core.models.media.MediaType.MASTER_M3U8 : core.download.HLS.DownloadM3U8FromMaster,
    core.models.media.MediaType.INDEX_M3U8 : core.download.HLS.DownloadM3U8FromIndex,
}


def download(
        download_information: processorModels.DownloadInformations,
        retry_with_FFmpeg:bool = False
        
):
    
    

    if not download_information or not isinstance(download_information, processorModels.DownloadInformations): raise ValueError("SoundcloudDownload: Given download information is either None or has the wrong type")

    if not "soundcloud.com" in download_information.url.lower(): raise core.models.errors.ArgumentError("Given URL wasn't a soundcloud.com URL")


    buttonList=[
    "#onetrust-reject-all-handler",
    "button.modal__closeButton[title='Close']"
    ]

    medialist: core.models.media.MediaList = core.request.EmergencyBrowser.BrowserDiscoverStreamURLs_ButtonList(
        download_information.url,
        headless=False,
        adBlock=True,
        buttonList=buttonList
    )
    
    if not medialist: raise ValueError("SoundcloudDownload: Didn't find media to download")
    
    try:
        for candidate in medialist.candidates:
            
            candidate: core.models.media.Media
            print(candidate)
            downloadFunction = MEDIATYPE_MAPPING.get(candidate.mediaType, None)
            print("test1234")
            
            if not downloadFunction:
                raise ValueError("SoundcloudDownload: Best found ressource doesn't have a function to download it with")

            
            print("test1")
                
            downloader = downloadFunction(
                url = candidate.mediaUrl,
                out_file = download_information.outFile,
                session = download_information.session,
                progress_dict = download_information.downloadProgress
            )
            print("test2")
            downloader.run()
            print("test3")
            return
                
 
    except urllib.error.HTTPError as e:
        if e.code == 403 and retry_with_FFmpeg:
            print(f"Error 403, trying with CURL and FFMPEG")

            ffmpegCommand = core.general.CurlToFFMPEG.get_curlToFFmpeg(
                candidate.curlCommand,
                output=download_information.outFile
            )

            run_shell_command_async(ffmpegCommand)

            return

        raise
    except Exception:
         raise


   