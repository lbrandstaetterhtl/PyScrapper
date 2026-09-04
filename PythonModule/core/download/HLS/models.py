from dataclasses import dataclass, field
from enum import Enum, auto

class PatternTypes(Enum):
    MEDIA = auto()
    STREAM = auto()
    BANDWIDTH = auto()

    AUDIO_STREAM_TYPE =auto()

    AUDIO_BLOCK_TYPE = auto()
    AUDIO_BLOCK_NAME = auto()
    AUDIO_BLOCK_URI = auto()
    AUDIO_BLOCK_LANGUAGE = auto()



class FileType(Enum):
    AUDIO_FILE = auto()
    INDEX_FILE = auto()
    MASTER_FILE = auto()
    UNKNOWN_FILE = auto()






PATTERN_MAPPING = {
    PatternTypes.MEDIA: r'(#EXT-X-MEDIA:[^\r\n]*)',
    PatternTypes.STREAM: r'(#EXT-X-STREAM-INF:.*?)\n([^\n]+)',
    PatternTypes.BANDWIDTH: r'BANDWIDTH=(\d+)',
    PatternTypes.AUDIO_STREAM_TYPE: r'AUDIO="(.*?)"',
    PatternTypes.AUDIO_BLOCK_TYPE: r'GROUP-ID="(.*?)"',
    PatternTypes.AUDIO_BLOCK_NAME: r'NAME="(.*?)"',
    PatternTypes.AUDIO_BLOCK_URI: r'URI="([^"]+)"',
    PatternTypes.AUDIO_BLOCK_LANGUAGE: r'LANGUAGE="(.*?)"',
}




@dataclass
class HLSSegment:
    url: str
    pos: int
    duration: float | None = None



@dataclass
class M3U8Audio:
    audio_url: str | None = None
    audio_seperated: bool = False
    audio_type: str | None = None
    audio_language: str | None = None



@dataclass
class M3U8Stream:

    stream_url: str = ""
    stream_bandwidth: int = 0

    audio_information: M3U8Audio = field(
        default_factory=M3U8Audio
    )

