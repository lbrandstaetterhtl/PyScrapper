#Core Imports
#Python Default Imports
from dataclasses import dataclass
from enum import Enum, auto




class MediaType(Enum):
    MASTER_M3U8 = auto()
    INDEX_M3U8 = auto()
    SEGMENT_M3U8 = auto()
    UNKNOWN_M3U8 = auto()
   
    MASTER_MPD = auto()
    SEGMENTTEMPLATE_MPD = auto()
    SEGMENTLIST_MPD = auto()
    SEGMENT_MPD = auto()
    UNKNOWN_MPD = auto()

    FILE = auto()
    UNKNOWN = auto()



class StreamType(Enum):
    HLS = auto()
    DASH = auto()
    DIRECT = auto()
    UNKNOWN = auto()



@dataclass
class Headers:
    origin: str = ""
    referer: str = ""
    accept: str = ""
    cookieFile: str = ""
    authorization: str = ""
    userAgent: str = ""

    def to_dict(self) -> dict[str, str]:
        headers = {
            "Origin": self.origin,
            "Referer": self.referer,
            "Accept": self.accept,
            "Authorization": self.authorization,
            "User-Agent": self.userAgent,
        }

        
        return {
            name: value.strip()
            for name, value in headers.items()
            if isinstance(value, str) and value.strip()
        }




@dataclass
class Media:
    headers: Headers
    mediaUrl: str = ""
    mediaType: MediaType = MediaType.UNKNOWN
    streamType: StreamType = MediaType.UNKNOWN
    priority: int = -1
    curlCommand: str = ""
    


@dataclass
class MediaList:
    candidates: list[Media]

    @property
    def primary(self) -> Media | None:
        return self.candidates[0] if self.candidates else None
    
    @property
    def fallback(self) -> Media | None:
        return self.candidates[1] if len(self.candidates) > 1 else None
    
    def add(self, media: Media) -> None:
        self.candidates.append(media)
        self.candidates.sort(key=lambda item: item.priority, reverse=True)

