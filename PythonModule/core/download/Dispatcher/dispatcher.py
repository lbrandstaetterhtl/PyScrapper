#Core imports

from ...models.errors import TaskFailedError
from ...models import Download
from ...general import Validate



#Own imports


#Python default imports

from dataclasses import replace
import asyncio





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

        self._splitContext()

        

    async def downloadContextAndYield(self, context: Download.DownloadContext):

        from ..File import FileDispatcher
        from ..HLS import HLSDispatcher
        Validate.download.validateDownloadContext(argument_name="context", download_context=context, caller="[CORE] DownloadDispatcher.downloadContextAndYield")
        if context.target.download_type == Download.DownloadType.FILE:
            dispatcher = FileDispatcher(
                replace(
                    self.downloadInformation,
                    contexts=[context]
                )
            )
        elif context.target.download_type == Download.DownloadType.HLS:
            dispatcher = HLSDispatcher(
                replace(
                    self.downloadInformation,
                    contexts=[context]
                )
            )
        else:
            context.download_progress.status = Download.TaskStatus.FAILED
            context.download_progress.error_message = "Unsupported DownloadType was given"
            raise TaskFailedError(
                task="[CORE] DownloadDispatcher.downloadContextAndYield",
                reason="Unknown download type was given",
                caller="[CORE] DownloadDispatcher.downloadContextAndYield"
            )
        async for chunk in dispatcher.downloadAndYield():
            yield chunk




    async def downloadToFile(self):
        tasks = []
        from ..File import FileDispatcher
        from ..HLS import HLSDispatcher

        
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

        if tasks:
            await asyncio.gather(*tasks)



    async def downloadAndYield(self):
        """
        Streams all contexts sequentially into one raw byte stream
        For http requests or without knowing when one file ends it isn't recommend using this function
        Recommendation: Use downloadContextAndYield() instead
        """

        from ..File import FileDispatcher
        from ..HLS import HLSDispatcher
        
        if self.downloadInformationFile.contexts:
            async for chunk in FileDispatcher(self.downloadInformationFile).downloadAndYield():
                yield chunk

        if self.downloadInformationHLS.contexts:
            async for chunk in HLSDispatcher(self.downloadInformationHLS).downloadAndYield():
                yield chunk




    def _splitContext(self):
        for context in self.downloadInformation.contexts:
            if context.target.download_type == Download.DownloadType.FILE:
                self.downloadInformationFile.contexts.append(context)

            elif context.target.download_type == Download.DownloadType.HLS:
                self.downloadInformationHLS.contexts.append(context)

            else:
                context.download_progress.status = Download.TaskStatus.FAILED
                context.download_progress.error_message = "Couldn't resolve type of target and target will be dismissed"



        


        