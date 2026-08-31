# Core imports
from ...models import Download
from ...models.errors import TaskFailedError

from ...general import Validate
from ...network import html

from  ..Dispatcher import Dispatcher

#Own Package imports
from . import models

from .index import IndexHLSDownload
from .master import MasterHLSDownload


#Default downloads
import asyncio


class HLSDispatcher(Dispatcher):
    """
    Main API for downloading HLS streams.
    It  takes in a url to either a master or index m3u8 file, determines the type of file, and dispatches the appropriate download process.
    It supports downloading multiple contexts concurrently and can optionally use ffmpeg for merging segments.
    Use the run() method to start the download process.
    """
    def __init__(
            self,
            download_information: Download.DownloadInformation,
            preferred_languages: list[str] | None = None,
            download_with_ffmpeg = False
            ):
        super().__init__(
            download_information
        )


        Validate.general.validateBool(
            boolean=download_with_ffmpeg, argument_name="download_with_ffmpeg", caller="[CORE] HLSDispatcher.init")
        
        if preferred_languages is not None:
            Validate.general.validateListStr(
                argument_name="preferred_languages",
                liste=preferred_languages,
                caller="[CORE] HLSDispatcher.init"
            )

        self.downloadWithFFmpeg = download_with_ffmpeg

        self.preferredLanguages = preferred_languages

   
    async def _runContextStream(self, context: Download.DownloadContext):
        async with self.downloadInformation.download_limiter:
            
            file = await asyncio.to_thread(
                html.getHtml,
                session=self.downloadInformation.session,
                url=context.target.resolved_url,
                extra_headers=context.target.extra_headers
            )

            if file is None:
                raise TaskFailedError(
                    task="[CORE] HLSDispatcher.run.getHtml",
                    reason="Returned html is None",
                    caller="[CORE] HLSDispatcher.run"
                )
            try:
                fileType = self.dertermineFileType(file)

                if fileType == models.FileType.MASTER_FILE:

                    master = MasterHLSDownload(
                        context,
                        self.downloadInformation.session,
                        preferred_languages=self.preferredLanguages
                    )
                    indexUrl, audioUrl = await asyncio.to_thread(
                        master.getUrls
                    )

                    context.target.resolved_url = indexUrl

                    index = IndexHLSDownload(
                        context,
                        self.downloadInformation.session,
                        audio_url=audioUrl
                    )

                    async for chunk in index.downloadAndYield():
                        yield chunk

                elif fileType == models.FileType.INDEX_FILE:
                    index = IndexHLSDownload(
                        context,
                        self.downloadInformation.session,
                    )

                    async for chunk in index.downloadAndYield():
                        yield chunk
                else:
                    raise TaskFailedError(
                        task="[CORE] HLSDispatcher._runContext",
                        reason=f"Couldn't determine file type: {context.target.resolved_url}"
                    )
                
            except Exception as e:
                context.download_progress.status = Download.TaskStatus.FAILED
                context.download_progress.error_message = str(e)
                raise



            
            
    async def _runContextLocal(
            self,
            context: Download.DownloadContext
    ):
        async with self.downloadInformation.download_limiter:

            
            file = await asyncio.to_thread(
                html.getHtml,
                session=self.downloadInformation.session,
                url=context.target.resolved_url,
                extra_headers=context.target.extra_headers
            )

            if file is None:
                raise TaskFailedError(
                    task="[CORE] HLSDispatcher.run.getHtml",
                    reason="Returned html is None",
                    caller="[CORE] HLSDispatcher.run"
                )
            try:
                fileType = self.dertermineFileType(file)

                if fileType == models.FileType.MASTER_FILE:

                    master = MasterHLSDownload(
                        context,
                        self.downloadInformation.session,
                        preferred_languages=self.preferredLanguages
                    )

                    indexUrl, audioUrl = await asyncio.to_thread(
                        master.getUrls
                    )

                    context.target.resolved_url = indexUrl

                    index = IndexHLSDownload(
                        context,
                        self.downloadInformation.session,
                        audio_url=audioUrl
                    )

                    await asyncio.to_thread(
                        index.downloadToFile,
                        
                    )

                elif fileType == models.FileType.INDEX_FILE:

                    index = IndexHLSDownload(
                        context,
                        self.downloadInformation.session
                    )

                    await asyncio.to_thread(
                        index.downloadToFile,
                       
                    )

                else:
                    raise TaskFailedError(
                        task="[CORE] HLSDispatcher._runContext",
                        reason=f"Couldn't determine file type: {context.target.resolved_url}"
                    )
            except Exception as e:
                context.download_progress.status = Download.TaskStatus.FAILED
                context.download_progress.error_message = str(e)
                raise
        



    def dertermineFileType(
            self,
            file: str
            ):

        MASTER_TAGS = [
            "#EXT-X-STREAM-INF:",
            "#EXT-X-I-FRAME-STREAM-INF:",
            "#EXT-X-MEDIA:"
        ]
        INDEX_TAGS = [
            "#EXTINF:",
            "#EXT-X-TARGETDURATION",
            "#EXT-X-ENDLIST",
            "#EXT-X-PLAYLIST-TYPE",
            "#EXT-X-MAP"
        ]

        if not file.lstrip().startswith("#EXTM3U"):
            return models.FileType.UNKNOWN_FILE

        if any(tag in file for tag in MASTER_TAGS):
            return models.FileType.MASTER_FILE

        if any(tag in file for tag in INDEX_TAGS):
            return models.FileType.INDEX_FILE

        return models.FileType.UNKNOWN_FILE
        
    
        

        