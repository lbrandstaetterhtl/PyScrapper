import PythonModule.core as core
import urllib.error
import asyncio
import subprocess

async def run_shell_command_async(command: str):
        await asyncio.to_thread(
            subprocess.run,
            command,
            shell=True,
            check=True,
            executable="/bin/bash"
        )

def download(
        url: str,
        outFile: str,
        session: core.request.Session.Session = None,
        
):
    
    

    if not url or not isinstance(url, str): raise core.models.errors.ArgumentError("Invalid URL or None URL was given")

    if not "soundcloud.com" in url.lower(): raise core.models.errors.ArgumentError("Given URL wasn't a soundcloud.com URL")

    if session == None or not isinstance(session, core.request.Session.Session): 
        session = core.request.Session.Session()

    buttonList=[
    "#onetrust-reject-all-handler",
    "button.modal__closeButton[title='Close']"
    ]

    mediaList: core.models.media.MediaList = core.request.EmergencyBrowser.BrowserDiscoverStreamURLs_ButtonList(
        url,
        headless=False,
        adBlock=True,
        buttonList=buttonList
    )
    
    if not mediaList: raise core.models.errors.ArgumentError("Didn't find media")

    for media in mediaList.candidates:
        media:core.models.media.Media
        lastCurlCommand: str = media.curlCommand
        url: str = media.mediaUrl.lower()
        try:
            if ".m3u8" in url:
                if "master" in url:
                    downloader = core.download.HLS.downloadM3U8FromMaster(
                        outFile=outFile,
                        masterUrl=url
                    )
                    downloader.run()
                    return
                elif "index" in url or "playlist" in url:
                    downloader = core.download.HLS.DownloadM3U8FromIndex(
                        outFile=outFile,
                        indexUrl=url
                    )
                    downloader.run()
                    return



        except urllib.error.HTTPError as e:
            if e.code == 403 and lastCurlCommand:
                print(f"Error 403, trying with CURL and FFMPEG")

                ffmpegCommand = core.general.CurlToFFMPEG.get_curlToFFmpeg(
                    lastCurlCommand,
                    output=outFile
                )

                run_shell_command_async(ffmpegCommand)

                return

            raise


   