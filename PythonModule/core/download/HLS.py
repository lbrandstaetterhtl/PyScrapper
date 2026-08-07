#Imports
from ..request.Session import Session
from ..general.DataSearch import searchBlocks, searchBlocksAll
from ..general.Html import getHtml
from ..models.errors import ArgumentError, MergeError, TaskFailedError
from ..models.M3U8 import M3U8Stream
import urllib.request, urllib.parse
import shutil
import subprocess
import os
import time

from ..general import Validate

def _validateArguments_DownloadM3U8FromXInit(
        out_file: str,
        url: str,
        session: Session,
        progress_dict: dict,
        extra_headers:dict,
        preferedAudioLanguages: list[str] = None,
        audio_url: str = None,
        caller: str = "[CORE] _validateArguments_DownloadM3U8FromXInit"
):
    
    Validate.validateDict(argument_name="progress_dict", dictionary=progress_dict, caller=caller)
    Validate.validateSession(session=session, argument_name="session", caller=caller)
    Validate.validateOutFile(out_file=out_file, caller=caller)

    if preferedAudioLanguages:
        Validate.validateListStr(argument_name="preferedAudioLanguages", liste=preferedAudioLanguages, caller=caller)

    if extra_headers:
        Validate.validateDict(argument_name="extra_headers", dictionary=extra_headers, caller=caller)

    if audio_url:
        Validate.validateHostDefault(url=audio_url, caller=caller)

    Validate.validateHostDefault(url)
    
    


#Classes
class DownloadM3U8FromMaster():
    def __init__(
            self,
            out_file: str,
            url: str = "",
            session: Session = None,
            progress_dict: dict = None, 
            extra_headers: dict = None,
            preferedAudioLanguages: list[str] = None,

            ):
        

        if preferedAudioLanguages is None:
            preferedAudioLanguages = ["de", "deutsch", "ger", "german"]
        _validateArguments_DownloadM3U8FromXInit(out_file, url, session, progress_dict, extra_headers, preferedAudioLanguages=preferedAudioLanguages, caller="[CORE] DownloadM3U8FromMaster.init")

        self.masterUrl = url
        self.outFile = out_file
        self.downloadProgress = progress_dict
        self.extraHeaders = extra_headers
        self.preferedAudioLanguages = preferedAudioLanguages
        self.session = session


    def run(self):
        result: M3U8Stream = _selectIndexFromMaster(
        masterUrl=self.masterUrl,
        preferedAudioLanguages=self.preferedAudioLanguages,
        session=self.session,
        extra_headers=self.extraHeaders
    )
        
        if not result.streamUrl:
            raise TaskFailedError(
                task="DownloadM3U8FromMaster.run",
                reason="Downloader couldn't find a stream URL",
                caller="[CORE] DownloadM3U8FromMaster"
            )
        
        print(f"[CORE] DownloadM3U8FromMaster.run: Found index url: '{result.streamUrl}'. Bandwidth: {result.streamBandwidth}")

        if result.audioUrl:
            print(f"[CORE] DownloadM3U8FromMaster.run: Found optional audio url: '{result.audioUrl}'")

        DownloadM3U8FromIndex(
            out_file=self.outFile,
            url=result.streamUrl,
            audio_url=result.audioUrl,
            session=self.session,
            progress_dict=self.downloadProgress,
            extra_headers = self.extraHeaders
        ).run()





class DownloadM3U8FromIndex():
    def __init__(
            self,
            out_file: str,
            url: str = "",
            audio_url: str = "",
            session: Session = None,
            progress_dict:dict = None,
            extra_headers: dict = None
            ):
        
        _validateArguments_DownloadM3U8FromXInit(out_file, url, session, progress_dict,extra_headers, audio_url=audio_url, caller="[CORE] DownloadM3U8FromIndex.init")

        self.ffmpegPath = shutil.which("ffmpeg")
        
        self.session = session
        
        self.indexUrl = url

        self.outFile = out_file
        self.outPath = os.path.dirname(os.path.dirname(out_file))
        self.downloadProgress = progress_dict

       
        self.audioUrl = audio_url
        self.extraHeaders = extra_headers


    def run(
            self,
            download_with_ffmpeg: bool = False
            ):
        Validate.validateBool(boolean=download_with_ffmpeg, argument_name="download_with_ffmpeg", caller="[CORE] DownloadM3U8FromIndex.run")
        
        #Main method for downloading m3u8 files, it will try to use ffmpeg if it is installed and in the PATH, if not it will fallback to downloading the segments manually and merging them together. It also updates the given download progress dict with the current progress of the download
        if download_with_ffmpeg == False:       
                    self.downloadM3U8Manual()
                    return
        

        if self.ffmpegPath:
            print("[CORE] DownloadM3U8FromIndex.run: ffmpeg found, using ffmpeg to download m3u8")
            if self.audioUrl:
                command = [
                    self.ffmpegPath,
                    "-i", self.indexUrl,
                    "-i", self.audioUrl,
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c", "copy",
                    self.outFile
                ]
            else:
                command = [
                    self.ffmpegPath,
                    "-i", self.indexUrl,
                    "-c", "copy",
                    self.outFile
                ]
            _downloadM3U8FFMPEG(command, self.downloadProgress)
            return
        else:
            raise TaskFailedError(
                task="[CORE] DownloadM3U8FromIndex.run",
                reason="ffmpeg path wasn't found on this system",
                caller="[CORE] DownloadM3U8FromIndex.run"
            )
        

    
        


    def downloadM3U8Manual(self):
    
        _indexFile =getHtml(
            session=self.session,
            url=self.indexUrl,
            extra_headers=self.extraHeaders
        )
        
            
        
        segmentUrls = _getSegmentUrlsFromIndex(
            _indexFile,
            playlistUrl=self.indexUrl
        )

        if not segmentUrls:
            raise ValueError("downloadM3U8Manual: No segment urls found in index file")
        if not self.audioUrl:
            _downloadM3U8SegmentsToFile(
                segmentUrls,
                self.outFile,
                self.session,
                self.downloadProgress,
                extra_headers=self.extraHeaders
            )
        else:
            audioSegmentUrls = _getSegmentUrlsFromIndex(
                indexFile=getHtml(
                    session=self.session,
                    url=self.audioUrl,
                    extra_headers=self.extraHeaders
                ),
                playlistUrl=self.audioUrl
            )
            _downloadM3U8SegmentsAndAudioToFile(
                segmentUrls,
                audioSegmentUrls,
                self.outFile,
                self.outPath,
                self.session,
                self.downloadProgress,
                self.ffmpegPath,
                extra_headers=self.extraHeaders
            )

    
#Functions for Master

def _findBestQualityMasterM3U8(
        manifestUrls,
        prefferedLanguages: list[str] = None,
        masterUrl: str = ""
) -> M3U8Stream:

    
    if not isinstance(prefferedLanguages, list) or prefferedLanguages is None:
        prefferedLanguages = ["de", "deutsch", "ger", "german"]

    if not isinstance(manifestUrls, str): raise ValueError("_findBestQualityMasterM3U8: given file is not a string")

    
    mediaPattern = r'(#EXT-X-MEDIA:TYPE=AUDIO.*?)'
    
    mediaBlocks = searchBlocksAll(
        pattern=mediaPattern,
        search_block=manifestUrls
    )
    
    streamPattern = r'(#EXT-X-STREAM-INF:.*?)\n([^\n]+)'
    streamBlocks = searchBlocksAll(
        pattern=streamPattern,
        search_block=manifestUrls
    )

    result = M3U8Stream()


    for stream,url in streamBlocks:

        bandwidthPattern = r'BANDWIDTH=(\d+)'
        bandwidth = searchBlocks(
            pattern=bandwidthPattern,
            search_block=stream
        )

        audioTypePattern = r'AUDIO="(.*?)"'
        audioType = searchBlocks(
            pattern=audioTypePattern,
            search_block=stream
        )

        bandwidth = int(bandwidth) if bandwidth else 0


        if result.streamBandwidth < bandwidth:
            result.streamBandwidth = bandwidth

            if url.startswith("http") or url.startswith("https"):
                result.streamUrl = url

            else:
                if not masterUrl:
                    raise ValueError("_findBestQualityMasterM3U8: Master url is required to resolve relative stream url")
                result.streamUrl = urllib.parse.urljoin(masterUrl, url)

            result.streamAudioType = audioType


    if mediaBlocks and result.streamAudioType:
        _findAudioUrlFromMasterM3U8(
            mediaBlocks=mediaBlocks,
            result=result,
            prefferedLanguages=prefferedLanguages,
            masterUrl=masterUrl
        )
    
    return result





def _findAudioUrlFromMasterM3U8(
        mediaBlocks: str,
        result: M3U8Stream,
        prefferedLanguages: list[str] | None = None,
        masterUrl: str = ""
):
    audioTypePattern = r'GROUP-ID="(.*?)"'
    audioNamePattern = r'NAME="(.*?)"'
    audioUriPattern = r'URI="([^"]+)"'
    audioLanguagePattern = r'LANGUAGE="(.*?)"'

    if prefferedLanguages is None or not isinstance(prefferedLanguages, list):
        prefferedLanguages = ["de"]  

    prefferedLanguages = [lang.lower() for lang in prefferedLanguages]

    if prefferedLanguages:
        for audio in mediaBlocks:
            audioType = searchBlocks(
                    pattern=audioTypePattern,
                    search_block=audio
                )
            if not audioType:
                continue
            if audioType.lower() != result.streamAudioType.lower():
                continue
                
            audioName = searchBlocks(
                pattern=audioNamePattern,
                search_block=audio
            )

            audioLanguage = searchBlocks(
                pattern=audioLanguagePattern,
                search_block=audio
            )
            if audioName:
                audioName = audioName.lower()
            if audioLanguage:
                audioLanguage = audioLanguage.lower()
            if not audioLanguage and not audioName:
                continue
            if audioLanguage in prefferedLanguages or audioName in prefferedLanguages:
                audioUrl = searchBlocks(
                    pattern=audioUriPattern,
                    search_block=audio
                )
                if not audioUrl:
                    continue
                if audioUrl.startswith("http") or audioUrl.startswith("https"):
                    result.audioUrl = audioUrl
                else:
                    if not masterUrl:
                        raise ValueError("_findAudioUrlFromMasterM3U8: Master url is required to resolve relative audio url")
                    result.audioUrl = urllib.parse.urljoin(masterUrl, audioUrl)
                return


    for audio in mediaBlocks:
        audioType = searchBlocks(
            pattern=audioTypePattern,
            search_block=audio
        )
        if not audioType:
            continue
        if audioType.lower() == result.streamAudioType.lower():
            audioUrl = searchBlocks(
                pattern=audioUriPattern,
                search_block=audio
            )
            if not audioUrl:
                continue
            if audioUrl.startswith("http") or audioUrl.startswith("https"):
                result.audioUrl = audioUrl
            else:
                if not masterUrl:
                    raise ValueError("_findAudioUrlFromMasterM3U8: Master url is required to resolve relative audio url")
                result.audioUrl = urllib.parse.urljoin(masterUrl, audioUrl)
            return
                



def _selectIndexFromMaster(
        preferedAudioLanguages,
        masterUrl: str = "",
        session: Session = None,
        extra_headers: dict = None,
        
) -> str:
    if not masterUrl:
        raise ArgumentError("_selectIndexFromMaster: No master url was given")
    
    manifestUrls = getHtml(
        session=session,
        url=masterUrl,
        extra_headers=extra_headers
    )

    
    result: M3U8Stream = _findBestQualityMasterM3U8(manifestUrls, prefferedLanguages=preferedAudioLanguages, masterUrl=masterUrl)
    return result



    


#Functions for Index
def _downloadM3U8FFMPEG(
        command: list,
        downloadProgress: dict = None
):
    if not isinstance(downloadProgress, dict) or downloadProgress is None:
        downloadProgress = {}
    try:
        subprocess.run(command, check=True)

    except Exception:
        raise





def _downloadM3U8SegmentsToFile(
        segmentUrls: list[str],
        outFile: str,
        session: Session,
        downloadProgress: dict,
        chunkSize: int = 8192,
        extra_headers:dict = None
):
    if not segmentUrls:
        raise ValueError(
            "_downloadM3U8SegmentsToFile: No segment URLs were given"
        )

    if downloadProgress is None:
        downloadProgress = {}

    totalSegments = len(segmentUrls)
    downloadedSegments = 0
    downloadedBytes = 0

    startTime = time.time()

    downloadProgress["status"] = "downloading..."
    downloadProgress["totalSegments"] = totalSegments
    downloadProgress["downloadedSegments"] = 0
    downloadProgress["downloadedBytes"] = 0
    downloadProgress["downloadProgress"] = 0.0
    downloadProgress["totalBytes"] = -1
    downloadProgress["speed"] = 0.0
    downloadProgress["eta"] = None

    try:
        with open(outFile, "wb") as file:
            for segmentIndex, url in enumerate(segmentUrls, start=1):
                segmentSize = 0

                request = urllib.request.Request(
                    url,
                    method="GET"
                )

                with session.open(request=request, headers=extra_headers) as response:
                    while True:
                        chunk = response.read(chunkSize)

                        if not chunk:
                            break

                        file.write(chunk)

                        chunkLength = len(chunk)
                        segmentSize += chunkLength
                        downloadedBytes += chunkLength

                        elapsedTime = time.time() - startTime

                        if elapsedTime > 0:
                            bytesPerSecond = downloadedBytes / elapsedTime

                            downloadProgress["speed"] = round(
                                bytesPerSecond / 1024 / 1024,
                                2
                            )

                        downloadProgress["downloadedBytes"] = (
                            downloadedBytes
                        )

                downloadedSegments += 1

                progressPercent = (
                    downloadedSegments / totalSegments * 100
                )

                elapsedTime = time.time() - startTime
                averageSegmentTime = (
                    elapsedTime / downloadedSegments
                )

                remainingSegments = (
                    totalSegments - downloadedSegments
                )

                estimatedRemainingTime = (
                    remainingSegments * averageSegmentTime
                )

                downloadProgress["downloadedSegments"] = (
                    downloadedSegments
                )
                downloadProgress["downloadProgress"] = round(
                    progressPercent,
                    2
                )
                downloadProgress["eta"] = round(
                    estimatedRemainingTime,
                    1
                )

                print(
                    f"\rDownloadJob: {downloadProgress.get("id", "unknown")} "
                    f"Downloaded segment "
                    f"{downloadedSegments}/{totalSegments} "
                    f"({segmentSize} bytes, "
                    f"{downloadProgress['speed']} MiB/s, "
                    f"ETA {downloadProgress['eta']} s)",
                    end="",
                    flush=True
                )

        downloadProgress["downloadProgress"] = 100.0
        downloadProgress["eta"] = 0.0
        downloadProgress["status"] = "complete"

        print()

    except Exception:
        downloadProgress["status"] = "failed"
        raise





def _downloadM3U8SegmentsAndAudioToFile(
        segmentUrls: list[str],
        audioSegmentUrls: list[str],
        outFile: str,
        outPath: str,
        session: Session,
        downloadProgress: dict,
        ffmpegPath: str | None = None,
        extra_headers: dict = None
):
    
    outVideoFile = os.path.join(outPath, "video.ts")
    outAudioFile = os.path.join(outPath, "audio.ts") 

    _downloadM3U8SegmentsToFile(
        segmentUrls=segmentUrls,
        outFile=outVideoFile,
        session=session,
        downloadProgress=downloadProgress,
        extra_headers=extra_headers
    )
    print("\nFinished downloading video segments, now downloading audio segments...")
    
    segments = len(audioSegmentUrls)
    segment = 0


    with open(outAudioFile, "wb") as f:

        for url in audioSegmentUrls:
            segment += 1
            segmentSize:int = 0
            request = urllib.request.Request(
                url,
                method="GET"
            )

            try:
                with session.open(request=request, headers=extra_headers) as response:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        segmentSize += len(chunk)
                        f.write(chunk)

                print(f"\rDownloaded audio segment {segment}/{segments} ({segmentSize} bytes)", end="", flush=True)
                downloadProgress['downloadedBytes'] += segmentSize

            except Exception as e:
                downloadProgress['status'] = "failed"
                raise ValueError(f"_downloadM3U8SegmentsAndAudioToFile: An error occurred while downloading audio segment {url}. Error: {e}")
    
    if not ffmpegPath:
        raise MergeError(videoFile=outVideoFile, audioFile=outAudioFile)
    
    command = [
        ffmpegPath,
        "-i", outVideoFile,
        "-i", outAudioFile,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c", "copy",
        outFile
    ]
    _downloadM3U8FFMPEG(command=command, downloadProgress={})
        






def _getSegmentUrlsFromIndex(
        indexFile: str,
        playlistUrl: str = ""
) -> list[str]:
    
    if "#EXT-X-KEY" in indexFile or "#EXT-X-SESSION-KEY" in indexFile:
        raise NotImplementedError("_getSegmentUrlsFromIndex: Encrypted m3u8 files are not supported yet")
    

    lines = indexFile.splitlines()
    segmentUrls = []

    for line in lines:
        line = line.strip()
        if line.startswith("#EXT-X-MAP:"):
            initUrl = searchBlocks(
                pattern=r'URI="([^"]+)"',
                search_block=line
            )
            if initUrl:
                if initUrl.startswith("http") or initUrl.startswith("https"):
                    segmentUrls.append(initUrl)
                else:
                    if not playlistUrl:
                        raise ValueError("_getSegmentUrlsFromIndex: Playlist url is required to resolve relative init segment url")
                    segmentUrls.append(urllib.parse.urljoin(playlistUrl, initUrl))
    
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue
        if line.startswith("http") or line.startswith("https"):
            segmentUrls.append(line)
        else:
            if not playlistUrl:
                raise ValueError("_getSegmentUrlsFromIndex: Playlist url is required to resolve relative segment url")
            segmentUrls.append(urllib.parse.urljoin(playlistUrl, line))
    
    return segmentUrls
            