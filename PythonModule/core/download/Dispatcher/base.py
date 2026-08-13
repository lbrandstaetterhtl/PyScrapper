#Core imports

from ...models import Download
from ...models.errors import TaskFailedError

from ...general import Validate

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
            argument_name="download_information", download_information=download_information, caller="[CORE] HLSDispatcher.init")

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
        


    @abstractmethod
    async def _runContextLocal(self, context):
         pass

    @abstractmethod
    async def _runContextStream(self, context):
        pass

    

             
         
