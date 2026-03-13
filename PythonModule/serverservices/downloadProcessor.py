from PythonModule.providers import Youtube, Suno, Archive
from PythonModule.models.requests import DownloadRequest
from PythonModule.Session import Session
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
            raise TypeError("progressDict needs to be from type 'dict'")
        
        if not isinstance(downloadRequest, DownloadRequest): 
            raise TypeError("downloadRequest needs to be from models.downloadRequest")
        
        if not isinstance(downloadLimiter, asyncio.Semaphore): 
            raise TypeError("downloadLimiter needs to be from type 'asyncio.Semaphore'")
        
        if not isinstance(session, Session): 
           raise TypeError("Session must be from type session")
        
        if not isinstance(logQueue, asyncio.Queue):
            raise TypeError("given Queue for logs must be an asyncio.Queue")
        
#progressDict is used to save the progress. server.py will give one and so it will be updated for the server in life time
        self.progressDict:dict = progressDict

#in Download Request is the data saved to determine what the Processor will do
        self.downloadRequest:DownloadRequest = downloadRequest

#downloadLimiter will be given from the server so not too many downlaod Jobs will run parralel and kill the bandwidth
        self.downloadLimiter:asyncio.Semaphore = downloadLimiter 

#Session is used to open the links with, save cookies...
        self.session:Session = session

        self.logQueue: asyncio.Queue = logQueue
        

    async def run(
            self
            ):
        try:
            out_path = self.downloadRequest.download_path
            os.makedirs(out_path, exist_ok=True)

            file = self.downloadRequest.filename
            self.downloadRequest.mediatype = utils.addpointtomediatype(mediatype=self.downloadRequest.mediatype)
            print(self.downloadRequest.mediatype)
            mediatype = self.downloadRequest.mediatype

            out_file = utils.make_out_file(
                out_path=out_path,
                filename=file,
                mediatype=mediatype
            )





        
        
            provider = utils.validateProviders(providerGiven=self.downloadRequest.provider)
            if not provider:
                raise ValueError("No supported provider was given")
            
    #Raises an exception if 

            utils.validateMediatype(provider=provider, mediatype=mediatype)

            
            if provider == "archive":
                await self.ArchiveDownload(out_file)
                

            elif provider == "youtube":
                await self.YoutubeDownload(out_file)

            elif provider == "suno":
                await self.SunoDownload(out_file)

            else:
                raise Exception("invalid provider was somehow passed")
            
            self.logQueue.put_nowait(f"[INFO] Successfully completed downloadjob {self.progressDict.get('id')}")
            
        except Exception as e:
            self.logQueue.put_nowait(f"[ERROR] Failed download for job {self.progressDict.get('id')}.\nError Message: {str(e)}")
            self.progressDict["status"] = "error"
            self.progressDict["errorMessage"] = str(e)
#END OF RUN        
        
    
        


    async def ArchiveDownload(
            self,
            out_file
            ):
        async with self.downloadLimiter:
            await asyncio.to_thread(
                Archive.download,
                url=self.downloadRequest.url,
                out_file=out_file,
                progress_dict= self.progressDict,
                session = self.session,
                mediatype=self.downloadRequest.mediatype
            )
#END OF ARCHIVE DOWNLOAD            
       



    async def YoutubeDownload(self,
                            out_file:str
                            ):
#Removing the file extensions because for youtube yt-dlp is used and yt-dlp adds its fileextensions on its own
        out_file = out_file.replace(f"{self.downloadRequest.mediatype}", "")

        async with self.downloadLimiter:
            if self.downloadRequest.mediatype.lower() == ".mp4":
                

                await asyncio.to_thread(
                    Youtube.download,
                    url=self.downloadRequest.url,
                    out_file=out_file,
                    progress_dict=self.progressDict
                    )
            else:
                await asyncio.to_thread(
                    Youtube.download_audio_only,
                    url=self.downloadRequest.url,
                    progress_dict=self.progressDict,
                    out_file=out_file
                    )
#END OF YOUTUBEDOWNLOAD              




    async def SunoDownload(
            self,
            out_file:str
    ):
        async with self.downloadLimiter:
            await asyncio.to_thread(
                Suno.download,
                url=self.downloadRequest.url,
                out_file=out_file,
                progress_dict=self.progressDict,
                session=self.session,
                mediatype=self.downloadRequest.mediatype

            )
#END OF SUNODOWNLOAD
                
        


    