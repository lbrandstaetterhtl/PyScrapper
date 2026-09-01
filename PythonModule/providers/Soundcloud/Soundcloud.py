#Core Imports
import PythonModule.core as core
from PythonModule.core.network import browser

from PythonModule.core.network import html


#Own imports
from .. import models

#Python Default Imports
import urllib.parse
import asyncio
import subprocess
import time









async def run_shell_command_async(command: str):
        await asyncio.to_thread(
            subprocess.run,
            command,
            shell=True,
            check=True,
            executable="/bin/bash"
        )







    
    




# def download(
#         download_information: core.models.General.DownloadInformations,
#         retry_with_FFmpeg:bool = False
        
# ):
    
    

#     core.general.Validate.validateDownloadInformation(argument_name="download_information", download_information=download_information, caller="[providers] Soundcloud.download")
#     core.general.Validate.validateBool(boolean=retry_with_FFmpeg, argument_name="retry_with_FFmpeg", caller="[providers] Soundcloud.download")

#     core.general.Validate.validateHostPro(
#         url=download_information.url,
#         allowed_protocols_list=["https"],
#         allowed_hostnames_list=["soundcloud.com", "www.soundcloud.com", "52.84.150.57", "52.84.150.39", "52.84.150.35", "52.84.150.52"],
#         caller="[providers] Soundcloud.download"
#         )


#     buttonList=[
#     "#onetrust-reject-all-handler",
#     "button.modal__closeButton[title='Close']"
#     ]

#     medialist: core.models.media.MediaList = core.request.EmergencyBrowser.BrowserDiscoverStreamURLs_ButtonList(
#         download_information.url,
#         headless=True,
#         adBlock=True,
#         buttonList=buttonList
#     )
    
#     if not medialist:
#         raise core.models.errors.TaskFailedError(
#             task="[CORE] BrowserDiscoverStreamUrls_ButtonList",
#             reason="Browser couldn't detect find valid media",
#             extraMessages=["Browser can't find media when the website is DRM protected/encrypted", "Try again with Headful Browser and see if Browser is now able to find Media"]
#         )
    
#     try:
#         for candidate in medialist.candidates:
            
#             candidate: core.models.media.Media
        
#             downloadFunction = MEDIATYPE_MAPPING.get(candidate.mediaType, None)
         
#             if downloadFunction == None:
#                 raise core.models.errors.TaskFailedError(
#                     task="[providers] Soundcloud.download",
#                     reason="Mediatype Mapping didn't give back a function",
#                     extraMessages=["Mediatype Mapping only has functions for HLS download", f"Mediatype of the highest prio media: '{candidate.mediaType}'"],
#                     caller="[providers] Soundcloud.download",
#                 )

                
#             downloader = downloadFunction(
#                 url = candidate.mediaUrl,
#                 out_file = download_information.outFile,
#                 session = download_information.session,
#                 progress_dict = download_information.downloadProgress
#             )
    
#             downloader.run()
     
#             return
                
 
#     except urllib.error.HTTPError as e:
#         if e.code == 403 and retry_with_FFmpeg:
#             print(f"Error 403, trying with CURL and FFMPEG")

#             ffmpegCommand = core.general.CurlToFFMPEG.get_curlToFFmpeg(
#                 candidate.curlCommand,
#                 output=download_information.outFile
#             )

#             run_shell_command_async(ffmpegCommand)

#             return

#         raise
#     except Exception:
#          raise


   