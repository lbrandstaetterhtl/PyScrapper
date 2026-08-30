# core imports
from ...models import Download

from ...network import file

from ..Dispatcher.base import Dispatcher


# own imports

from . import download

# python default imports
import asyncio




class UMPDispatcher(Dispatcher):
    def __init__(
            self,
            download_information: Download.DownloadInformation
            ):
        super().__init__(
            download_information
        )


    async def _runContextLocal(
                self,
                context: Download.DownloadContext
        ):
            async with self.downloadInformation.download_limiter:
                try:
                    await asyncio.to_thread(
                        download.downloadToFileUMP,
                            out_file=context.output.out_file,
                            session=self.downloadInformation.session,
                            start_url=context.target.resolved_url,
                            extra_headers=context.target.extra_headers,
                            download_progress=context.download_progress,
                            max_len=context.media_info.total_size
                             
                        
                    )
    
                except Exception as e:
                    context.download_progress.status = Download.TaskStatus.FAILED
                    context.download_progress.error_message = str(e)
                    raise




    async def _runContextStream(
                self,
                context: Download.DownloadContext
        ):
            async with self.downloadInformation.download_limiter:
                try:
                    async for chunk in download.downloadAndYieldUMP(
                        session=self.downloadInformation.session,
                        start_url=context.target.resolved_url,
                        extra_headers=context.target.extra_headers,
                        download_progress=context.download_progress,
                        max_len=context.media_info.total_size
                    ):
                        yield chunk
    
                    context.download_progress.status = Download.TaskStatus.FINISHED
    
                except Exception as e:
                    context.download_progress.status = Download.TaskStatus.FAILED
                    context.download_progress.error_message = str(e)
                    raise