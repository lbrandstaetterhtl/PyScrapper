from PythonModule.models.requests import DownloadRequest
from PythonModule.core.request.Session import Session
from PythonModule.models import processorModels
from . import utils

import asyncio
import os
        
class DownloadProcessor():
    def __init__(
            self,
            progressDict: dict,
            downloadRequest: DownloadRequest,
            session: Session,
            downloadLimiter: asyncio.Semaphore,
            logQueue: asyncio.Queue
            ):
        
        if not isinstance(progressDict, dict): 
            raise TypeError("[ERROR] DownloadProcessor: progressDict needs to be from type 'dict'")
        
        if not isinstance(downloadRequest, DownloadRequest): 
            raise TypeError("[ERROR] DownloadProcessor: downloadRequest needs to be from models.downloadRequest")
        
        if not isinstance(downloadLimiter, asyncio.Semaphore): 
            raise TypeError("[ERROR] DownloadProcessor: downloadLimiter needs to be from type 'asyncio.Semaphore'")
        
        if not isinstance(session, Session): 
           raise TypeError("[ERROR] DownloadProcessor: Session must be from type session")
        
        if not isinstance(logQueue, asyncio.Queue):
            raise TypeError("[ERROR] DownloadProcessor: given Queue for logs must be an asyncio.Queue")
        


#Session is used to open the links with, save cookies...
        self._createDownloadInformations(
            download_request=downloadRequest,
            progress_dict=progressDict,
            session=session,
            download_limiter = downloadLimiter
        )



        self.logQueue: asyncio.Queue = logQueue


        
        

    async def run(
            self
            ):
        try:
            provider:processorModels.ProviderTypes = utils.validateProviders(providerGiven=self.downloadInformation.providerStr)
            
            downloadFunction = processorModels.providerDownloadMapping.get(provider, None)
            if downloadFunction is None:
                raise Exception(f"Provider {self.downloadInformation.providerStr} isn't supported for downloading yet")

            if not downloadFunction:
                raise Exception("No download function was found for this provider")


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
            session: Session,
            download_limiter: asyncio.Semaphore

            
            ):
        self.downloadInformation = processorModels.DownloadInformations()
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






    