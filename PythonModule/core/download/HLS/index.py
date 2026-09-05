#Core Imports

from ...general import Validate
from ...models.errors import TaskFailedError, MergeError
from ...models.Convert import FFMPEG_FORMAT_MAPPING
from ...models import Download

from ...network.Session import Session
from ...network import file
from ...network import progress
from ...processes import ProcessDrainType, AsyncProcessManager

#Own imports

from .downloader import HLSDownload
from . import finder
from . import models


#Python Default Imports

import shutil
import asyncio
import os




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
            audio_url: str | None = None,
  
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

        self.downloadContext.download_progress.total_segments = (
            len(segmentList)
            + len(segmentAudioList)
        )

        audioReadFd = None
        audioWriteFd = None

        outputFormat = FFMPEG_FORMAT_MAPPING.get(self.downloadContext.media_info.file_extension, "")
        if not outputFormat:
            raise TaskFailedError(
                task="[CORE] IndexHLSDownload.downloadAndYield",
                reason="Couldn't get format for ffmpeg",
                extraMessages=[
                    f"Found extension: {self.downloadContext.media_info.file_extension}",
                    "Available FFmpeg format mappings:",
                    *[
                        f"  {extension} -> {ffmpegFormat}"
                        for extension, ffmpegFormat in sorted(FFMPEG_FORMAT_MAPPING.items())
                    ],
                ],
                caller="[CORE] IndexHLSDownload.downloadAndYield"
            )

        args = [
            "ffmpeg",

    #Video from first pipe 
            "-i", "pipe:0",

        ]

        if segmentAudioList:
            audioReadFd, audioWriteFd = os.pipe()
            args += [
                "-i", f"pipe:{audioReadFd}",

                "-map", "0:v:0",
                "-map", "1:a:0",
            ]

        else:
            args += [
                "-map", "0:v:0",
                "-map", "0:a:0?",
            ]
        args += [
            "-c", "copy",
            "-f", outputFormat,
            "pipe:1",
        ]

        
        manager = AsyncProcessManager(
            args,
            stderr_drain_type=ProcessDrainType.PRINT,
            stdout_drain_type=ProcessDrainType.MANUAL,
            pass_fds=(
                (audioReadFd,)
                if audioReadFd is not None
                else ()
            ),
            process_name=f"HLS Download <{self.downloadContext.context_id}>"
        )

        await manager.start()

    #FFMPEG doesn't need the read part of the pipe
        if audioReadFd is not None:
            os.close(audioReadFd)

        async def _feedVideo():
            try:
                for segment in segmentList:
                    async for chunk in file.asyncDownloadYieldSimple(
                        session=self.session,
                        url=segment.url,
                        extra_headers=self.downloadContext.target.extra_headers
                    ):
                        progress.updateDownloadProgress(
                            self.downloadContext.download_progress,
                            downloaded_bytes=len(chunk)
                        )
                        try:
                            manager.process.stdin.write(chunk)
                            await manager.process.stdin.drain()

                        except (BrokenPipeError, ConnectionResetError, RuntimeError) as e:
                            raise TaskFailedError(
                                task="[CORE] IndexHLSDownload.downloadAndYield",
                                reason="FFmpeg closed video input unexpectedly",
                                extraMessages=[
                                    f"FFmpeg return code: {manager.process.returncode}",
                                    "FFmpeg stderr:",
                                    *manager.stderrLines[-20:],
                                ],
                                caller="[CORE] IndexHLSDownload.downloadAndYield",
                            ) from e
                    

                    progress.updateDownloadProgress(
                        self.downloadContext.download_progress,
                        downloaded_segments=1
                    )

            finally:
                manager.process.stdin.close()

                try:
                    await manager.process.stdin.wait_closed()
                except (BrokenPipeError, ConnectionResetError):
                    pass

        async def _feedAudio():
            if audioWriteFd is None:
                return

            try:
                for segment in segmentAudioList:
                    async for chunk in file.asyncDownloadYieldSimple(
                        session=self.session,
                        url=segment.url,
                        extra_headers=self.downloadContext.target.extra_headers,
                    ):
                        progress.updateDownloadProgress(
                            self.downloadContext.download_progress,
                            downloaded_bytes=len(chunk),
                        )

                        await file.writeFd(
                            audioWriteFd,
                            chunk,
                        )

                    progress.updateDownloadProgress(
                        self.downloadContext.download_progress,
                        downloaded_segments=1,
                    )

            finally:
                os.close(audioWriteFd)

        videoTask = asyncio.create_task(
            _feedVideo()
        )

        audioTask = (
            asyncio.create_task(_feedAudio())
            if segmentAudioList
            else None
        )

        try:
            while True:
                chunk, eof = await manager.readStdout()

                if eof:
                    break

                yield chunk


            await videoTask

            if audioTask:
                await audioTask

            returnCode = await manager.wait()

            if returnCode != 0:
                raise RuntimeError(
                    f"FFmpeg exited with code {returnCode}"
                )

            self.downloadContext.download_progress.status = Download.TaskStatus.FINISHED

        finally:
            if not videoTask.done():
                videoTask.cancel()

            if audioTask and not audioTask.done():
                audioTask.cancel()

            await manager.stop()




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

        
        
        segmentList: list[models.HLSSegment] = []
        segmentAudioList: list[models.HLSSegment] = []
        
        segmentList = finder.findSegments(
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

        
        

            



                        


                

                



            

        

