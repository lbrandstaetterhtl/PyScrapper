#Core Imports
import PythonModule.core as core
from PythonModule.models import settings
from PythonModule.models.requests import DownloadRequest
from . import utils

#Python Default Imports
import asyncio
import os
        
class DownloadProcessor():
    def __init__(
            self,
            progressDict: dict,
            downloadRequest: DownloadRequest,
            session: core.request.Session.Session,
            downloadLimiter: asyncio.Semaphore,
            logQueue: asyncio.Queue
            ):

        core.general.Validate.validateDict(
            argument_name="progressDict", dictionary=progressDict, caller="[serverservices] downloadProcessor.init")
        core.general.Validate.validateGeneralType(
            argument_name="downloadRequest", obj=downloadRequest, objType=DownloadRequest, caller="[serverservices] downloadProcessor.init"
        )
        core.general.Validate.validateSession(
            session=session, argument_name="session", caller="[serverservices] downloadProcessor.init"
        )
        core.general.Validate.validateGeneralType(
            argument_name="downloadLimiter", obj=downloadLimiter, objType=asyncio.Semaphore
        )
        core.general.Validate.validateGeneralType(
            argument_name="logQueue", obj=logQueue, objType=asyncio.Queue, caller="[serverservices] downloadProcessor.init"
        )
        


#Session is used to open the links with, save cookies...
        self._createDownloadInformations(
            download_request=downloadRequest,
            progress_dict=progressDict,
            session=session,
            download_limiter = downloadLimiter
        )



        self.logQueue: asyncio.Queue = logQueue
        self.downloadInformation: core.models.General.DownloadInformations



    async def run(
            self
            ):
        try:
            provider:settings.ProviderTypes = utils.validateProviders(providerGiven=self.downloadInformation.providerStr)
            
            
            downloadFunction = settings.providerDownloadMapping.get(provider, None)
            if downloadFunction is None:
                raise core.models.errors.TaskFailedError(
                    task="providerDownloadMapping.get()",
                    reason="Provider string given isn't supported",
                    extraMessages=[f"Provider string that was given {self.downloadInformation.providerStr}",f"Provider Type that got used: '{provider}'."]
                )
                

            async with self.downloadInformation.downloadLimiter:
                await asyncio.to_thread(
                    downloadFunction,
                    self.downloadInformation
                )


#If everything runs without raising an error the Processor will think that everything went according to plan and finished successfully            
            self.logQueue.put_nowait(f"[INFO] DownloadProcessor: Successfully completed downloadjob {self.downloadInformation.downloadProgress.get('id')}")
            
        except Exception as e:
            self.logQueue.put_nowait(f"[ERROR] DownloadProcessor: Failed download for job {self.downloadInformation.downloadProgress.get('id')}.\nError Message: {str(e)}")
            self.downloadInformation.downloadProgress["status"] = "error"
            self.downloadInformation.downloadProgress["errorMessage"] = str(e)
#END OF RUN        
        
    





    def _createDownloadInformations(
            self,
            download_request: DownloadRequest,
            progress_dict: dict,
            session: core.request.Session.Session,
            download_limiter: asyncio.Semaphore

            
            ):

        self.downloadInformation = core.models.General.DownloadInformations()
#Creating filename with ending 
        self.downloadInformation.filename = download_request.filename + download_request.mediatype
        self.downloadInformation.fileending = download_request.mediatype

#Creating Folder where file will get saved into
        self.downloadInformation.downloadPath = download_request.download_path
        os.makedirs(self.downloadInformation.downloadPath, exist_ok=True)

#Creating outfile where the modules will save the files to
        self.downloadInformation.outFile = os.path.join(self.downloadInformation.downloadPath, self.downloadInformation.filename)

        self.downloadInformation.url = download_request.url

        self.downloadInformation.session = session

        self.downloadInformation.downloadProgress = progress_dict

        self.downloadInformation.providerStr = download_request.provider

        self.downloadInformation.downloadLimiter = download_limiter






    