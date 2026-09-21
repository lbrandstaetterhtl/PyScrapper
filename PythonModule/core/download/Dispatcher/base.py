#Core imports

from ...models import Download
from ...models.errors import TaskFailedError

from ...general import Validate
from ...ffmpeg import AsyncFFmpegMuxer, AsyncFFmpegProbeCodec, FFmpegCodec, canMuxCodecsIntoContainer

#Own imports

#Python default imports
import asyncio
from abc import ABC, abstractmethod

#Pip install imports
import os
if os.name == "nt": 
    import pywintypes


BROKEN_PIPE_ERROS = (
    BrokenPipeError,
    pywintypes.error
) if os.name == "nt" else (BrokenPipeError)

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






    async def _getCodec(
            self,
            generator,
            index: int,
            caller: str = "[CORE] Dispatcher._getCodec",
            
            ):

        prober = AsyncFFmpegProbeCodec(use_pipe=True, caller=caller)
        codecTask = asyncio.create_task(prober.getCodec())

        buffer = bytearray()
        
        async for chunk in generator:

            buffer.extend(chunk)


            if codecTask.done():
                
                break

            try:
                await prober.writePipe(chunk)

            except BROKEN_PIPE_ERROS:
                
                break

        codecs = await codecTask

        for codec in codecs:
            codec.input_index = index

        return codecs, buffer

    


    async def _asyncProcessSources(
            self,
            video_source,
            context: Download.DownloadContext,
            audio_source = None,
            ):
    
    #setup of downloader
            
    
            videoIndex = 0
            audioIndex = 1


            codecList:list[str] = []

        
            videoGenerator = video_source()
            codecs, primaryBuffer =await self._getCodec(
                generator=videoGenerator,
                index=0,
                caller=f"{self.__class__.__name__}-{context.context_id}",
      
            )
            codecList.extend(codecs)

            if audio_source:
                audioGenerator = audio_source()
                codecs, secondaryBuffer = await self._getCodec(
                    generator=audioGenerator,
                    index=1,
                    caller=f"{self.__class__.__name__}-{context.context_id}",

                )
                codecList.extend(codecs)

            finalFile: str = context.info.preferred_file if context.output.auto_convert else context.info.found_file
            if (
                canMuxCodecsIntoContainer(
                codecs=codecList,
                file_ending=finalFile,
                caller=f"{self.__class__.__name__}-{context.context_id}")
                and finalFile == context.info.found_file
                and not audio_source
            ):
                
                yield bytes(primaryBuffer)

                async for chunk in videoGenerator:
                    yield chunk
                return

        
            
            muxer = AsyncFFmpegMuxer(
                file_ending=context.info.preferred_file if context.output.auto_convert else context.info.found_file,
                input_count=2 if audio_source else 1,
                codecs=codecList,
                caller=f"{self.__class__.__name__}-{context.context_id}"
            )
    #Setup of downloader end
    
            async def _feedVideo():
                await muxer.writePipe(
                    bytes(primaryBuffer),
                    videoIndex
                )
                try:
                    async for chunk in videoGenerator:
                        await muxer.writePipe(data=chunk, pipe_index=videoIndex)
                finally:
                    await muxer.closePipe(videoIndex)
    
    
            async def _feedAudio():
                await muxer.writePipe(
                    bytes(secondaryBuffer),
                    audioIndex
                )
                try:
                    async for chunk in audioGenerator:
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

    

             
         
