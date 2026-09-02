# core imports
from ...models import Download

from ...network import file

from ..Dispatcher.base import Dispatcher


# own imports

from . import download
from . import youtube_download_with_ytdlp

# python default imports
import asyncio
from urllib.parse import urlparse, parse_qs




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
                    mode = self.getUMPMode(context)
             

                    if mode == "sabr":
                        await asyncio.to_thread(
                            download.downloadToFileSABR,
                                out_file=context.output.out_file,
                                session=self.downloadInformation.session,
                                start_url=context.target.resolved_url,
                                extra_headers=context.target.extra_headers,
                                download_progress=context.download_progress,
                                post_body=context.target.post_body
                            
                        )

                    


                    else:
                        await asyncio.to_thread(
                            download.downloadToFileUMP,
                                out_file=context.output.out_file,
                                session=self.downloadInformation.session,
                                start_url=context.target.resolved_url,
                                extra_headers=context.target.extra_headers,
                                download_progress=context.download_progress,
                                max_len=context.media_info.total_size,
                                post_body=context.target.post_body
                                
                            
                        )
                        context.download_progress.speed = Download.TaskStatus.FINISHED
    
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
                    mode = self.getUMPMode(context)

                    if mode == "sabr":
                        generator = download.downloadAndYieldSABRSimple(
                        session=self.downloadInformation.session,
                        start_url=context.target.resolved_url,
                        extra_headers=context.target.extra_headers,
                        post_body=context.target.post_body,
                        download_progress=context.download_progress,
                    )

                    elif mode == "youtube":
                        generator = youtube_download_with_ytdlp.downloadAndYieldYTDLPSimple(context)
                        async for chunk in generator:
                            yield chunk

                    else:
                        generator = download.downloadAndYieldUMP(
                            session=self.downloadInformation.session,
                            start_url=context.target.resolved_url,
                            extra_headers=context.target.extra_headers,
                            download_progress=context.download_progress,
                            max_len=context.media_info.total_size,
                            post_body=context.target.post_body
                        )
                        async for chunk in generator:
                            yield chunk
                    
    
                    context.download_progress.status = Download.TaskStatus.FINISHED
    
                except Exception as e:
                    context.download_progress.status = Download.TaskStatus.FAILED
                    context.download_progress.error_message = str(e)
                    raise


    

    def getUMPMode(
              self,
              context: Download.DownloadContext
              ):
        query = parse_qs(
            urlparse(context.target.resolved_url).query
        )

        if query.get("sabr") == ["1"]:
            return "sabr"

        if query.get("ump") == ["1"]:
            return "ump"

        if "youtube.com/watch" in context.target.resolved_url:
            return "youtube"

        raise ValueError("Unknown UMP transport")