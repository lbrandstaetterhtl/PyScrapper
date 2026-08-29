# Core Improts

from ...models.Download import DownloadContext
from ...models.errors import TaskFailedError
from ...network.Session import Session
from ...general import DataSearch


#Own imports

from . import models
from .downloader import HLSDownload





#Doesn't actually download anything, just prepares download_informations for IndexDownload and chooses audio and stream url
class MasterHLSDownload(HLSDownload):
    """
    Class for handling HLS download from a master m3u8 file.
    It selects the best quality stream and audio track based on the provided download context and preferred languages.
    Doesn't start the actual download, but prepares the necessary information (returns tuple[str, str | None]) for the IndexHLSDownload class to perform the download.
    Use the run() method to start the process of selecting the best stream and audio track.
    """
    def __init__(
            self,
            download_context : DownloadContext,
            session : Session | None = None,
            preferred_languages: list[str] | None = None
            ):
        
        super().__init__(
            download_context,
            session,
            )
        
        
        if preferred_languages is not None:
            from ...general import Validate
            Validate.general.validateListStr(
                argument_name="prefered_languages",
                liste=preferred_languages,
                caller="[CORE] HLSDownload.init"
                )

        self.preferredLanguages:list[str] = preferred_languages





        
    def getUrls(self) -> tuple[str, str | None]:

#First we must get the master file itself where all playlists/indexes are written down
        masterFile: str = self._get_Master_File()
        
        stream: models.M3U8Stream = self._select_Index_From_Master_File(masterFile)
        if not stream:
            raise TaskFailedError(
                task="[CORE] MasterHLSDownload.run",
                reason="Couldn't get a valid stream",
                extraMessages=[
                    "You will now see the master file:",
                    masterFile
                ]
            )

        message =(
            f"DownloadJob {self.downloadContext.context_id}: Successfully found stream valid stream"
            f"Found stream data:"
            f"Stream URL: {stream.stream_url}"
            f"Stream Bandwidth: {stream.stream_bandwidth}"
            f"Stream audiotype: {stream.audio_information.audio_type}"
        )
        if stream.audio_information.audio_seperated:
            message += (
                "Extra audio informations were found:"
                "Audio is in a seperated file"
                f"Audio URL: {stream.audio_information.audio_url}"
                f"Audio Language: {stream.audio_information.audio_language}"
            )
        print(message)


        return (stream.stream_url, stream.audio_information.audio_url)



        

    


    def _get_Master_File(self):
        masterFile: str = self._get_html(
            self.downloadContext.target.url,
            variable_name="masterFile",
            caller="[CORE] MasterHLSDownload._get_Master_File",
            extra_headers=self.downloadContext.target.extra_headers
        )
        return masterFile




#Uses 2 help functions to prepare the stream object
    def _select_Index_From_Master_File(
            self,
            master_file: str
            ) -> models.M3U8Stream:
        
        from . import finder

#Optional media block exists for carrying audio
        mediaBlocks: list[str] = DataSearch.searchBlocksAll(
            models.PATTERN_MAPPING.get(models.PatternTypes.MEDIA),
            master_file,

        )

#Actuall Streamblocks with "video"
        streamBlocks: list[tuple[str, str]] = DataSearch.searchBlocksAll(
            models.PATTERN_MAPPING.get(models.PatternTypes.STREAM),
            master_file
        )

#Searching for stream
        stream: models.M3U8Stream = finder.findBestQualityStream(
            streamBlocks,
            master_url=self.downloadContext.target.url,
            caller="[CORE] MasterHLSDownload._select_Index"
        )

#Optional if mediablocks were found search for audio url
        if mediaBlocks and stream.audio_information.audio_type:
            finder.findAudioUrl(
                mediaBlocks, 
                preferred_languages=self.preferredLanguages,
                master_url=self.downloadContext.target.url,
                audio_information=stream.audio_information,
                caller="[CORE] MasterHLSDownload._select_Index"
            )

        return stream
