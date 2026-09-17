#Core imports

from ...models import Download
from ...models.errors import TaskFailedError

from ...general import Validate
from ...ffmpeg import FFmpegMuxer

#Own imports

#Python default imports
import asyncio
from abc import ABC, abstractmethod




class Dispatcher(ABC):
    def __init__(
              self,
              download_information: Download.DownloadInformation
              ):
        

        Validate.download.validateDownloadInformation(
            argument_name="download_information", download_information=download_information, caller="[CORE] Dispatcher.init")

        self.downloadInformation = download_information

    async def downloadToFile(self):
            tasks = []


            for context in self.downloadInformation.contexts:
                task = asyncio.create_task(
                    self._runContextLocal(context)
                )
    
                tasks.append(task)
    
            results = await asyncio.gather(
                        *tasks,
                        return_exceptions=True
                    )
            
            resultList = []
    
            for result in results:
                if isinstance(result, Exception):
                    resultList.append(str(result))
                if resultList:
                    raise TaskFailedError(
                        task="[CORE] FileDispatcher.run",
                        reason="One or more tasks failed during execution.",
                        extraMessages=resultList
                    )
            print(self.downloadInformation)





    async def downloadAndYield(self):
        for context in self.downloadInformation.contexts:
            async for chunk in self._runContextStream(context):
                yield chunk


    async def _asyncProcessSources(
            self,
            video_source,
            context: Download.DownloadContext,
            audio_source = None,
            ):
    
    #setup of downloader
            
    
            videoIndex = 0
            audioIndex = 1


            codecs:list[str] = []
            videoBuffer = bytearray()

            
            muxer = FFmpegMuxer(
                file_ending=context.info.preferred_file if context.output.auto_convert else context.info.found_file,
                input_count=2 if audio_source else 1,
                maps=[f"{videoIndex}:v:0", f"{audioIndex}:a:0"] if audio_source else [],
                allow_re_encoding=True,
                caller=f"{self.__class__.__name__}-{context.context_id}"
            )
    #Setup of downloader end
    
            async def _feedVideo():
                try:
                    async for chunk in video_source():
                        await muxer.writePipe(data=chunk, pipe_index=videoIndex)
                finally:
                    await muxer.closePipe(videoIndex)
    
    
            async def _feedAudio():
                try:
                    async for chunk in audio_source():
                        await muxer.writePipe(data=chunk, pipe_index=audioIndex)
                finally:
                    await muxer.closePipe(audioIndex)
    
            await muxer.start()

            tasks = [
                asyncio.create_task(_feedVideo())
            ]
            
            if audio_source:
                tasks.append(asyncio.create_task(_feedAudio()))
                
            
    
            try:
                async for chunk in muxer.output():
                    yield chunk
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
    
                await asyncio.gather(
                    *tasks,
                    return_exceptions=True
                )
        


    @abstractmethod
    async def _runContextLocal(self, context):
         pass

    @abstractmethod
    async def _runContextStream(self, context):
        pass

    

             
         
