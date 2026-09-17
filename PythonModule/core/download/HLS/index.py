#Core Imports

from ...general import Validate
from ...models.errors import TaskFailedError


from ...network.Session import Session
from ...network import file
from ...network import progress


#Own imports

from .downloader import HLSDownload
from . import finder
from . import models


#Python Default Imports
import asyncio





#Classes
class IndexHLSDownload(HLSDownload):
    """
    Class for handling HLS download from an index m3u8 file.
    Takes in url of the index file and downloads the segments.
    Has methods for yielding and writing to a file
    """
    def __init__(
            self,
            index_url,
            session : Session,
            extra_headers: dict | None = None
  
            ):
        
        super().__init__(
            index_url,
            session,
            extra_headers
        )


        
    def downloadToFile(
            self,
            out_file: str,
            download_progress,
            ):

        Validate.download.validateDownloadProgress(
            argument_name="download_progress",download_progress=download_progress, caller="[CORE] IndexHLSDownload.downloadToFile"
            )
        Validate.download.validateOutFile(
            out_file=out_file,
            caller="[CORE] IndexHLSDownload.downloadToFile"
        )

        segmentList = self.getIndexSegmentList()

        if download_progress.total_segments < 0:
            download_progress.total_segments = len(segmentList)

        
        for segment in segmentList:

            downloadedBytes: int = file.downloadToFileSimple(
                out_file=out_file,
                session=self.session,
                url=segment.url,
                extra_headers=self.extraHeaders,
                open_file_method="ab"
            )
        
        
            progress.updateDownloadProgress(
                download_progress,
                downloadedBytes,
                downloaded_segments=1,
                caller="[CORE] IndexHLSDownload"
    
            )






    async def downloadAndYield(
            self,
            download_progress
            ):
        segmentList = await asyncio.to_thread(self.getIndexSegmentList)

        if download_progress.total_segments < 0:
            download_progress.total_segments = len(segmentList)

        for segment in segmentList:
        
            async for chunk in file.asyncDownloadYieldSimple(
                session=self.session,
                url=segment.url,
                start_byte=segment.start_byte,
                end_byte=segment.end_byte,
                extra_headers=self.extraHeaders
            ):
                progress.updateDownloadProgress(
                    download_progress,
                    downloaded_bytes=len(chunk)
                )
                yield chunk

            progress.updateDownloadProgress(
                download_progress,
                downloaded_segments=1
            )

        
          


    def getIndexSegmentList(
            self
            ) -> list[models.HLSSegment] | None:
       
        

        indexFile = self._get_html(
            self.url,
            variable_name="indexFile", 
            caller="[CORE] IndexHLSDownload.run",
            extra_headers=self.extraHeaders)

        
        
        segmentList: list[models.HLSSegment] = []
      
        
        segmentList = finder.findSegments(
            indexFile,
            self.url,
            caller="[CORE] IndexHLSDownload.getIndexSegmentList"
        )


        if not segmentList:
            raise TaskFailedError(
                task="[CORE] IndexHLSDownload.run",
                reason="Couldn't find segments",
                extraMessages=[
                    "Index file is following now:",
                    indexFile
                ],
                caller="[CORE] IndexHLSDownload.run"
            )
 
        return segmentList

        
