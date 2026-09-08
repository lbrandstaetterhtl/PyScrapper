#Core imports

from ...models.errors import TaskFailedError, FFmpegNotFoundError, FFmpegHttpError
from ...models import Download
from ...general import Validate



#Own imports


#Python default imports

from dataclasses import replace
import asyncio
from enum import Enum






class DownloadDispatcher():
    def __init__(self, download_information: Download.DownloadInformation):

        

        Validate.download.validateDownloadInformation(
            argument_name="download_information",
            download_information=download_information,
            caller="[CORE] DownloadDispatcher.init"
        )

        self.downloadInformation = download_information

        self.downloadInformationFile = replace(self.downloadInformation, contexts = [])
        self.downloadInformationHLS = replace(self.downloadInformation, contexts = [])
        self.downloadInformationUMP = replace(self.downloadInformation, contexts=[])

        self._splitContext()

        

    async def downloadContextAndYield(
            self,
            context: Download.DownloadContext,

            ):

        Validate.download.validateDownloadContext(argument_name="context", download_context=context, caller="[CORE] DownloadDispatcher.downloadContextAndYield")

        dispatcher = self._getManualDispatcher(context, caller="[CORE] DownloadDispatcher.downloadContextAndYield")
        async for chunk in dispatcher.downloadAndYield():
            yield chunk
        context.download_progress.status = Download.TaskStatus.FINISHED

       

        
        
        

            


    def _getManualDispatcher(
        self,
        context: Download.DownloadContext,
        caller: str = "[CORE] DownloadDispatcher._getManualDispatcher"
    ):

        from ..File import FileDispatcher
        from ..HLS import HLSDispatcher
        from ..UMP import UMPDispatcher
      
        
        downloadInformation = replace(
            self.downloadInformation,
            contexts=[context],
        )

        if context.target.download_type == Download.DownloadType.FILE:
            return FileDispatcher(downloadInformation)

        if context.target.download_type == Download.DownloadType.HLS:
            return HLSDispatcher(downloadInformation)

        if context.target.download_type == Download.DownloadType.UMP:
            return UMPDispatcher(downloadInformation)

        raise TaskFailedError(
            task="[CORE] DownloadDispatcher._getManualDispatcher",
            reason="Couldn't get manual dispatcher",
            caller=caller
        )



    async def downloadToFile(self):
        tasks = []
        from ..File import FileDispatcher
        from ..HLS import HLSDispatcher
        from ..UMP import UMPDispatcher

        
        if self.downloadInformationFile.contexts:
            tasks.append(
                asyncio.create_task(
                    FileDispatcher(self.downloadInformationFile).downloadToFile()
                )
            )

        if self.downloadInformationHLS.contexts:
            tasks.append(
                asyncio.create_task(
                    HLSDispatcher(self.downloadInformationHLS).downloadToFile()
                )
            )
        if self.downloadInformationUMP.contexts:
            tasks.append(
                asyncio.create_task(
                    UMPDispatcher(self.downloadInformationUMP).downloadToFile()
                )
            )


        if tasks:
            await asyncio.gather(*tasks)



    async def downloadAndYield(self):
        """
        Streams all contexts sequentially into one raw byte stream
        For http requests or without knowing when one file ends it isn't recommended using this function
        Recommendation: Use downloadContextAndYield() instead
        """

        from ..File import FileDispatcher
        from ..HLS import HLSDispatcher
        from ..UMP import UMPDispatcher
        
        if self.downloadInformationFile.contexts:
            async for chunk in FileDispatcher(self.downloadInformationFile).downloadAndYield():
                yield chunk

        if self.downloadInformationHLS.contexts:
            async for chunk in HLSDispatcher(self.downloadInformationHLS).downloadAndYield():
                yield chunk

        if self.downloadInformationUMP.contexts:
            async for chunk in UMPDispatcher(self.downloadInformationUMP).downloadAndYield():
                yield chunk




    def _splitContext(self):
        for context in self.downloadInformation.contexts:
            if context.target.download_type == Download.DownloadType.FILE:
                self.downloadInformationFile.contexts.append(context)

            elif context.target.download_type == Download.DownloadType.HLS:
                self.downloadInformationHLS.contexts.append(context)

            elif context.target.download_type == Download.DownloadType.UMP:
                self.downloadInformationUMP.contexts.append(context)

            else:
                context.download_progress.status = Download.TaskStatus.FAILED
                context.download_progress.error_message = "Couldn't resolve type of target and target will be dismissed"



        


        