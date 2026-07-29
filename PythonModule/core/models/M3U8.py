from dataclasses import dataclass

@dataclass
class M3U8Stream:
    streamUrl: str = ""
    streamBandwidth: int = 0
    streamAudioType: str = ""
    audioUrl: str = ""
    language: str = ""



