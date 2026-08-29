#Core Imports

from ...general import Validate
from ...models.errors import TaskFailedError, MergeError
from ...models import Download

from ...network.Session import Session
from ...network import file
from ...network import progress

#Own imports

from .downloader import HLSDownload
from . import finder
from . import models


#Python Default Imports

import shutil
import time
import asyncio



#Classes
class IndexHLSDownload(HLSDownload):
    """
    Class for handling HLS download from an index m3u8 file.
    Takes in url of the index file and optional audio url, downloads the segments, and optionally merges them using ffmpeg.
    Use the run() method to start the download process.
    """
    def __init__(
            self,
            download_context: Download.DownloadContext,
            session : Session | None = None,
            audio_url: str | None = None
            ):
        
        super().__init__(
            download_context,
            session,
        )
            
        
        if audio_url:
            Validate.special.validateHostDefault(
                audio_url, caller="[CORE] IndexHLSDownload.init"
            )
        self.audioUrl = audio_url

        self.ffmpegPath = shutil.which("ffmpeg")

        
    def downloadToFile(self):

        segmentResults = self.getIndexSegmentList()

        segmentList, segmentAudioList = segmentResults

        self._downloadSegmentsToFile(
                segmentList, segmentAudioList
            )
        
        self.downloadContext.download_progress.status = Download.TaskStatus.FINISHED





    async def downloadAndYield(self):
        segmentResults = await asyncio.to_thread(self.getIndexSegmentList)

        segmentList, segmentAudioList = segmentResults

        self.downloadContext.download_progress.total_segments = len(segmentList)

        for segment in segmentList:
            async for chunk in file.asyncDownloadYieldSimple(
                session=self.session,
                url=segment.url,
                extra_headers=self.downloadContext.target.extra_headers
            ):
                progress.updateDownloadProgress(
                    self.downloadContext.download_progress,
                    downloaded_bytes=len(chunk),
                    
                )
                yield chunk

            progress.updateDownloadProgress(
                self.downloadContext.download_progress,
                downloaded_segments=1
            )

        self.downloadContext.download_progress.status = Download.TaskStatus.FINISHED

#Ich lasse getrennte auido und video streamen mal aus



    
      







    def getIndexSegmentList(
            self
            ) -> tuple[list[models.HLSSegment] | None, list[models.HLSSegment] | None]:
        """
        """
        indexUrl = self.downloadContext.target.resolved_url if self.downloadContext.target.resolved_url else self.downloadContext.target.url

        indexFile = self._get_html(
            indexUrl,
            variable_name="indexFile", 
            caller="[CORE] IndexHLSDownload.run",
            extra_headers=self.downloadContext.target.extra_headers)
        
        segmentList = None
        segmentAudioList = None
        
        segmentList:list[models.HLSSegment] = finder.findSegments(
            indexFile,
            indexUrl,
            caller="[CORE] IndexHLSDownload.run"
        )


        if not segmentList:
            raise TaskFailedError(
                task="[CORE] IndexHLSDownload.run",
                reason="Couldn't find segments",
                extraMessages=[
                    "Index file is following now:",
                    indexFile
                ],
                caller="[CORE] IndexHLSDownload.run"
            )
        segmentAudioList:list[models.HLSSegment] = None


        if self.audioUrl:
            audioIndexFile = self._get_html(
                self.audioUrl,
                variable_name="audioIndexFile",
                caller="[CORE] IndexHLSDownload.run",
                extra_headers=self.downloadContext.target.extra_headers
            )

            segmentAudioList= finder.findSegments(
                audioIndexFile,
                self.audioUrl,
                caller="[CORE] IndexHLSDownload.run"
            )

        return (segmentList, segmentAudioList)

        


        
    




    def _downloadSegmentsToFile(
            self,
            segment_list: list[models.HLSSegment],
            segment_audio_list: list[models.HLSSegment]
            ):
        


        if self.audioUrl and segment_audio_list:
            audioOutFile = self.downloadContext.output.out_file + ".audio_tmp"
            videoOutFile = self.downloadContext.output.out_file + ".video_tmp"

            Validate.download.validateOutFile(out_file=audioOutFile, caller="[CORE] IndexHLSDownload._downloadSegmentsManual")
            Validate.download.validateOutFile(out_file=videoOutFile, caller="[CORE] IndexHLSDownload._downloadSegmentsManual")



            self.downloadContext.download_progress.total_segments = len(segment_list) + len(segment_audio_list)


            for segment in segment_list:
                self._downloadWrapperToFile(
                    segment,

                    videoOutFile
                    )


            for segment in segment_audio_list:
                self._downloadWrapperToFile(
                    segment,

                    audioOutFile
                    )



            if not self.ffmpegPath:
                raise MergeError(
                    videoFile=videoOutFile,
                    audioFile=audioOutFile
                )
            print(
                "Working on FFMPEG Command handler class. Not muxing files together  but also not deleting yet"
                f"audio output = {audioOutFile}"
                f"video output = {videoOutFile}"
                )
            #os.remove(videoOutFile)
            #os.remove(audioOutFile)
            

        else:

            self.downloadContext.download_progress.total_segments = len(segment_list)

            for segment in segment_list:
                self._downloadWrapperToFile(
                    segment,

                    self.downloadContext.output.out_file
                    )


        
        
                

    def _downloadWrapperToFile(
            self, 
            segment: models.HLSSegment,
            out_file: str
            ):
        
        downloadedBytes: int = file.downloadToFileSimple(
            out_file=out_file,
            session=self.session,
            url=segment.url,
            extra_headers=self.downloadContext.target.extra_headers,
            open_file_method="ab"
        )


        progress.updateDownloadProgress(
            self.downloadContext.download_progress,
            downloadedBytes,
            downloaded_segments=1,
            caller="[CORE] IndexHLSDownload"

        )

        
        

            



                        


                

                



            

        

