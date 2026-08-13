#Core Imports
from .errors import TaskFailedError

#Python default imports
from dataclasses import dataclass, field
from enum import Enum, auto


class ConvertTypes(Enum):
    SINGLE_TO_SINGLE = auto(),
    MULTIPLE_TO_SINGLE = auto(),

CONVERT_PROGRESS_DICT = {
    "id": "",
    "status" : "",
    "totalConverts" : 0,
    "finishedConverts" : 0,
    "convertProgress" : 0,
}


AUDIO_ONLY_FORMATS = [
    # Single stream
    "mp3",
    "wav",
    "flac",
    "aac",
    "ac3",
    "eac3",
    "dts",
    "amr",
    "au",
    "aiff",
    "aif",
    "w64",

    # Multi stream capable
    "mka",
    "m4a",
    "ogg",
    "opus",
    "wma",
]

VIDEO_ONLY_FORMATS = [
    "h264",
    "264",

    "h265",
    "265",
    "hevc",

    "m4v",
    "m2v",
    "h261",
    "h263",

    "ivf",
]

VIDEO_AND_AUDIO_FORMATS = [
    "mkv",
    "mp4",
    "mov",
    "webm",

    "avi",
    "flv",

    "ts",
    "m2ts",

    "mpeg",
    "mpg",
    "vob",

    "asf",
    "wmv",
]

AUDIO_SINGLE_STREAM = [
    "mp3",
    "wav",
    "flac",
    "aac",
    "ac3",
    "eac3",
    "dts",
    "amr",
    "au",
    "aiff",
    "aif",
    "w64",
]


AUDIO_MULTI_STREAM = [
    "mka",
    "m4a",
    "ogg",
    "opus",
    "wma",
]

VIDEO_SINGLE_STREAM = [
    "h264",
    "264",

    "h265",
    "265",
    "hevc",

    "m4v",
    "m2v",
    "h261",
    "h263",

    "ivf",
]

AUDIO_AND_VIDEO_MULTI_STREAM = [
    "mkv",
    "mp4",
    "mov",
    "webm",

    "avi",
    "flv",

    "ts",
    "m2ts",

    "mpeg",
    "mpg",
    "vob",

    "asf",
    "wmv",
]

ALL_SUPPORTED_FILETYPES = list(dict.fromkeys(
    AUDIO_ONLY_FORMATS
    + VIDEO_ONLY_FORMATS
    + VIDEO_AND_AUDIO_FORMATS
))

class MediaFormat(Enum):
    AUDIO_ONLY = auto()
    VIDEO_ONLY = auto()
    VIDEO_AND_AUDIO = auto()
    UNKNOWN = auto()

class StreamCapacity(Enum):
    SINGLE_STREAM = auto()
    MULTI_STREAM = auto()
    UNKNOWN = auto()

@dataclass
class VideoInfo:
    index: int = 0
    bitrateVid: int = 0
    widthVid: int = 0
    heightVid: int = 0

@dataclass
class AudioInfo:
    index: int = 0
    bitrateAudio: int = 0
    sampleRate: int = 0
    bitsPerSample: int = 0
    channels: int = 0
    

@dataclass
class InputFile:
    file_path: str = ""

    type: MediaFormat = MediaFormat.UNKNOWN

    videoStreams: list[VideoInfo] = field(default_factory=list)
    audioStreams: list[AudioInfo] = field(default_factory=list)

@dataclass 
class OutputFile:
    file_path: str = ""
    format: MediaFormat = MediaFormat.UNKNOWN

    stream_capacity: StreamCapacity = StreamCapacity.UNKNOWN
    file_ending: str = ""



@dataclass
class ConvertRequest:
    
    input_file_list: list[str]
    output_file_list: list[str]
 
    inputs_per_output: int

    convert_progress_dict: dict

    def __post_init__(self):
        
        from ..general import Validate

        Validate.general.validateInt(argument_name="inputs_per_output", integer=self.inputs_per_output, caller="[CORE] ConverRequest.__post_init__")
        Validate.general.validateListStr(argument_name="input_file_list", liste=self.input_file_list, caller="[CORE] ConverRequest.__post_init__")
        Validate.general.validateListStr(argument_name="output_file_list", liste=self.output_file_list, caller="[CORE] ConverRequest.__post_init__")
        Validate.general.validateDict(argument_name="convert_progress_dict", dictionary=self.convert_progress_dict, caller="[CORE] ConverRequest.__post_init__")

        self._validateInputOutputFiles()


        
    def _validateInputOutputFiles(self):
        

        expected_inputs: int = len(self.output_file_list) * self.inputs_per_output

        if len(self.input_file_list) != expected_inputs:
            raise TaskFailedError(
                task="[CORE] ConverRequest._validateInputOutputFiles",
                reason="Expected input files didn't match the actual input files",
                extraMessages=[
                    f"Input file amount: {len(self.input_file_list)}",
                    f"Output file amount: {len(self.output_file_list)}",
                    f"How many input files per output: {self.inputs_per_output}",
                    f"Expected files: {expected_inputs}",
                    
                ],
                caller="[CORE] ConverRequest.__post_init__"
            )
    