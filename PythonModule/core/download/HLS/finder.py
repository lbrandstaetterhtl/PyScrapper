#Core imports

from ...models.errors import TaskFailedError
from ...general import Validate
from ...general import DataSearch

#Own imports
from . import models

#Python Default Imports
import urllib.parse


def parseUrl(
    base_url: str,
    url: str,
    caller: str = "[CORE] HLS.finder.parseUrl"
) -> str:

    Validate.special.validateHostDefault(
        url=base_url, caller=caller)
    
    Validate.general.validateStr(
        argument_name="url", string=url, caller=caller)

    
    if url.startswith("http://") or url.startswith("https://"):
        return url
    
    return urllib.parse.urljoin(base_url, url)





def findBestQualityStream(
        stream_block_list: list[tuple[str, str]],
        master_url: str,
        caller: str = "[CORE] HLS.finder.findBestQualityStream"

) -> models.M3U8Stream:


    bestStream = models.M3U8Stream()


    for stream, url in stream_block_list:
        curStream = models.M3U8Stream()
#Getting Bandwidth of the stream
        bandwidth = DataSearch.searchBlocks(
            models.PATTERN_MAPPING.get(models.PatternTypes.BANDWIDTH), stream, False
            )

        
        curStream.stream_bandwidth = int(bandwidth) if bandwidth else 0

#Checking if current found stream has higher bandwidth, if yes get bonus information
        if curStream.stream_bandwidth > bestStream.stream_bandwidth:
            curStream.audio_information.audio_type = DataSearch.searchBlocks(
                models.PATTERN_MAPPING.get(models.PatternTypes.AUDIO_STREAM_TYPE), stream, False
            )
            curStream.stream_url = parseUrl(
                master_url, url, caller="[CORE] HLS.finder.findBestQualityStream")

            bestStream = curStream


    return bestStream




def _searchAudioBlock(
        audio_block: str,
        
) -> tuple[str, str, str, str]:
    
    audioType:str = DataSearch.searchBlocks(
        models.PATTERN_MAPPING.get(models.PatternTypes.AUDIO_BLOCK_TYPE), audio_block, False
    )

    audioLanguage: str = DataSearch.searchBlocks(
        models.PATTERN_MAPPING.get(models.PatternTypes.AUDIO_BLOCK_LANGUAGE), audio_block, False
    )

    audioName: str = DataSearch.searchBlocks(
        models.PATTERN_MAPPING.get(models.PatternTypes.AUDIO_BLOCK_NAME), audio_block, False
    )

    audioUri: str = DataSearch.searchBlocks(
        models.PATTERN_MAPPING.get(models.PatternTypes.AUDIO_BLOCK_URI), audio_block, False
    )
    return (audioType, audioLanguage, audioName, audioUri)

    
    

def findAudioUrl(
        media_block_list: list[str],
        preferred_languages: list[str],
        master_url: str,
        audio_information: models.M3U8Audio,
        caller: str = "[CORE] HLS.finder.findAudioUrl"
):
    if preferred_languages is not None:
        Validate.general.validateListStr(
            argument_name="preferred_languages", liste=preferred_languages, caller=caller)

    Validate.general.validateListStr(
        argument_name="media_block_list", liste=media_block_list, caller=caller)


    def _update_audio_information(
            audio_information: models.M3U8Audio,
            audio_uri: str,
            audio_language: str
            
    ):
        audio_information.audio_url = parseUrl(master_url, audio_uri, caller=caller)
        audio_information.audio_language = audio_language
        audio_information.audio_seperated = True
        


#First check is trying to find a preferred language
    if preferred_languages:
        for audio in media_block_list:
            if "TYPE=AUDIO" not in audio:
                continue
            searchResult = _searchAudioBlock(
                audio
            )
            audioType, audioLanguage, audioName, audioUri = searchResult

            


            if (
                not audioType
                or not audio_information.audio_type
                or audioType.lower() != audio_information.audio_type.lower()
                or (not audioLanguage and not audioName)
                or not audioUri
            ):
                continue

            if audioName:
                if any(l.lower() == audioName.lower() for l in preferred_languages ):
                    _update_audio_information(audio_information, audioUri, audioLanguage)
                    return
                
            elif audioLanguage:
                if any(l.lower() == audioLanguage.lower() for l in preferred_languages):
                    _update_audio_information(audio_information, audioUri, audioLanguage)
                    return
            


#Now doing the same thing again but just take the first valid one
    for audio in media_block_list:
        searchResult = _searchAudioBlock(
            audio
        )
        audioType, audioLanguage, audioName, audioUri = searchResult
        if (
            not audioType
            or not audio_information.audio_type
            or audioType.lower() != audio_information.audio_type.lower()
            or not audioUri
        ):
            continue

        _update_audio_information(audio_information, audioUri, audioLanguage)
        return
   




def findSegments(
        index_file: str,
        index_url: str,
        caller: str = "[CORE] HLS.finder.findSegments"
) -> list[models.HLSSegment]:

    Validate.special.validateHostDefault(
        index_url, caller=caller
    )
    length: float | None = None

#Checking if it has encrypted segments
    if "#EXT-X-KEY" in index_file or "#EXT-X-SESSION-KEY" in index_file:
        raise TaskFailedError(
            task="[CORE] IndexHLSDownload._get_Segments",
            reason="Encrypted segments found in index file",
            extraMessages=[
                "Decryption will likely never be implemented sorry",
                "Index file coming up",
                index_file
            ],
            caller=caller
        )
    
    segmentList = []
    lines = index_file.splitlines()

    def _update_SegmentList(
        url: str,
        pos: int,
        duration: int

    ):
        segment = models.HLSSegment(
            url,
            pos,
            duration=float(duration) if duration is not None else None
        )
        
        message = (
            "Found SEGMENT:"
            f"Segment url: {url}"
            f"Segment position: {pos}"
            f"Segment duration: {duration} seconds"
        )
        #print(message)

        segmentList.append(segment)
        


    for line in lines:
#Yes AUDIO_BLOCK_URI has the same pattern
        
        if line.startswith("#EXT-X-MAP"):
            initUrl = DataSearch.searchBlocks(
                models.PATTERN_MAPPING.get(models.PatternTypes.AUDIO_BLOCK_URI), line, False
            )
            if initUrl: 
                url =parseUrl(index_url, initUrl, caller)
                _update_SegmentList(
                    url, (len(segmentList) + 1), duration=0
                )

        if line.startswith("#EXTINF:"):
            length = DataSearch.searchBlocks(
                r'#EXTINF:([\d.]+)', line, False
            )

        if (
            not line
            or not line.strip()
            or line.startswith("#")
        ):
            continue


        url = parseUrl(index_url, line, caller=caller)
 
        _update_SegmentList(
            url, (len(segmentList) + 1), length)
        length = None


 
    return segmentList
        


            
            



    




        
