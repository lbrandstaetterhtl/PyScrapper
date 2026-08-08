#Core Imports

from ..models.Convert import ConvertRequest, AUDIO_ONLY_FORMATS, VIDEO_ONLY_FORMATS, VIDEO_AND_AUDIO_FORMATS, MediaFormat, InputFile, OutputFile, VIDEO_SINGLE_STREAM, AUDIO_SINGLE_STREAM, AUDIO_MULTI_STREAM, AUDIO_AND_VIDEO_MULTI_STREAM, StreamCapacity, VideoInfo, AudioInfo
from ..models.errors import TaskFailedError

#Python Default Imports
import json
import os
import shutil
import subprocess



class FileConverter():
    def __init__(
            self,
            convert_request: ConvertRequest,
            caller: str = "[CORE] Converter"
            ):
        from . import Validate
        Validate.validateStr(argument_name="caller", string=caller, caller="[CORE] Converter.init")

#Dataclass ConvertRequest items get validated by the class itself, so only check if the given obj is really ConvertRequest
        Validate.validateGeneralType(argument_name="convert_request", obj=convert_request, objType=ConvertRequest, caller="[CORE] Converter.init")



        fileMissingList: list[str] = []
        for input_file in convert_request.input_file_list:

            if not os.path.exists(input_file):
                fileMissingList.append(input_file)

            if not os.path.isfile(input_file):
                fileMissingList.append(input_file)
                


        if fileMissingList:
            raise TaskFailedError(
                task="[CORE] FileConverter.init",
                reason="Given input file doesn't exist",
                caller=caller,
                extraMessages=["Atleast one given input file doesn't exist", f"Files that didn't exist: {', '.join(fileMissingList)}"]
            )

        for output_file in convert_request.output_file_list:
            Validate.validateStr(argument_name="output_file", string=output_file, caller=caller)
            parentDir = os.path.dirname(output_file)

            if parentDir and not os.path.isdir(parentDir) or not parentDir:
                raise TaskFailedError(
                    task="[CORE] FileConvert.init",
                    reason="Invlaid Parent dir",
                    caller=caller
                )

        self.convertRequest = convert_request
        self.caller: str = caller

        self.ffmpegPath = shutil.which("ffmpeg")
        self.ffprobePath = shutil.which("ffprobe")
        self.inputList = self.convertRequest.input_file_list.copy()
        self.outputList = self.convertRequest.output_file_list.copy()

        if self.ffmpegPath is None:
            raise TaskFailedError(
                task="[CORE] FileConverter.init",
                reason="ffmpeg wasn't found on the system",
                caller=self.caller
            )
        if self.ffprobePath is None:
            raise TaskFailedError(
                task="[CORE] FileConverter.init",
                reason="ffprobe wasn't found on the system",
                caller=self.caller
            )

        self.tempList: list[str] =  []

    def run(self):
        self._convert_dict_init()    
        
        print("\n[CORE] Fileconverter.run: Started converting, this may take a while...")
        while self.convertRequest.convert_progress_dict.get("totalConverts", 0) != self.convertRequest.convert_progress_dict.get("finishedConverts", 0):
            self.convertRequest.convert_progress_dict["status"] = "converting"

            command = self._buildCommand()
            try:
                subprocess.run(
                            command,
                            check=True,
                            text=True,
                        )
            except subprocess.CalledProcessError as e:
                    raise TaskFailedError(
                        task="[CORE] FileConverter.run",
                        reason="ffmpeg encountered a problem while converting files",
                        extraMessages=["The following ffmpeg error has occured", e.stderr or str(e)],
                        caller=self.caller
                    ) from e

            self.convertRequest.convert_progress_dict["finishedConverts"] += 1
            if self.convertRequest.convert_progress_dict["totalConverts"] > 0:
                self.convertRequest.convert_progress_dict["convertProgress"] = (
                    self.convertRequest.convert_progress_dict["finishedConverts"] / self.convertRequest.convert_progress_dict["totalConverts"] * 100
                )

            print(
                f"\rConvertJob: {self.convertRequest.convert_progress_dict.get('id', 'unknown')} "
                f"Converted "
                f"{self.convertRequest.convert_progress_dict.get('finishedConverts', 0)}/"
                f"{self.convertRequest.convert_progress_dict.get('totalConverts', 0)} files "
                f"({self.convertRequest.convert_progress_dict.get('convertProgress', 0):.2f}%, "
                f"Status: {self.convertRequest.convert_progress_dict.get('status', 'unknown')})",
                end="",
                flush=True
            )

        if self.tempList:
            for path in self.tempList:
                os.remove(path)
    
            
        
            

    #Finished yay
        self.convertRequest.convert_progress_dict["status"] = "finished"

    def _buildCommand(self):

        command: list[str] = [
            self.ffmpegPath,
            "-y"
        ]
        outObj = OutputFile()

        outObj.file_path = self.outputList.pop(0)
        self._mediatypeMapping(outObj)

        files:list[InputFile] = []

        for _ in range(self.convertRequest.inputs_per_output):
            inputObj:InputFile = self._probeInput()
            if inputObj.file_path == outObj.file_path:
                newPath = inputObj.file_path + ".tmp"
                os.replace(inputObj.file_path, newPath)
                
                inputObj.file_path = newPath
                self.tempList.append(newPath)

            command.append(f"-i")
            command.append(inputObj.file_path)

            files.append(inputObj)



#Matching the format and add parameters like -vn for no video
        match outObj.format:
            case MediaFormat.AUDIO_ONLY:
                command.append("-vn")

            case MediaFormat.VIDEO_ONLY:
                command.append("-an")
            
            case MediaFormat.UNKNOWN:
                raise TaskFailedError(
                    task="[CORE] FileConverter._buildCommand",
                    reason="Unknown mediatype was given",
                    extraMessages=[
                        f"Supported Audio only Formats: {', '.join(AUDIO_ONLY_FORMATS)}",
                        f"Supported Video only Formats: {', '.join(VIDEO_ONLY_FORMATS)}",
                        f"Supported Video + Audio Formats: {', '.join(VIDEO_AND_AUDIO_FORMATS)}",
                        f"Given file: {outObj.file_path}"
                    ],
                    caller=self.caller
                )

        bestVideo: tuple[int, VideoInfo] | None = None
        bestAudio: tuple[int, AudioInfo] | None = None
#Now looking if multi or single stream, multi stream = All valid streams get added, single stream -> only the best stream
        if outObj.stream_capacity == StreamCapacity.MULTI_STREAM:
            for inputIndex, inputObj in enumerate(files):

                if "-an" not in command:
                    for audio in inputObj.audioStreams:
                        command.extend([
                            "-map",
                            f"{inputIndex}:a:{audio.index}"
                        ])

                if "-vn" not in command:
                    for video in inputObj.videoStreams:
                        command.extend([
                            "-map",
                            f"{inputIndex}:v:{video.index}"
                        ])           


        elif outObj.stream_capacity == StreamCapacity.SINGLE_STREAM:
            

            for inputIndex, inputObj in enumerate(files):

                for video in inputObj.videoStreams:
                    if bestVideo is None:
                        bestVideo = (inputIndex, video)
                        continue

                    _, currentBest = bestVideo 
                    currentResolution = video.widthVid * video.heightVid
                    bestResolution = currentBest.widthVid * currentBest.heightVid

                    if currentResolution > bestResolution:
                        bestVideo = (inputIndex, video)
                
                    
                    
                for audio in inputObj.audioStreams:
                    if bestAudio is None:
                        bestAudio = (inputIndex, audio)
                        continue

                    _, currentBest = bestAudio
#Python compares tuples one after each other, the first value to win is the general winner
#This just makes sure if fore example bitsPerSample are both times the same that the other values also gets checked and compared
                    currentQuality = (
                        audio.channels,
                        audio.sampleRate,
                        audio.bitsPerSample,
                        audio.bitrateAudio,
                        
                    )

                    bestQuality = (
                        currentBest.channels,
                        currentBest.sampleRate,
                        currentBest.bitsPerSample,
                        currentBest.bitrateAudio
                    )

                    if currentQuality > bestQuality:
                        bestAudio = (inputIndex, audio)
                                

            

            if outObj.format == MediaFormat.AUDIO_ONLY and bestAudio is None:
                        raise TaskFailedError(
                            task="[CORE] FileConverter._buildCommand",
                            reason="No audio stream found for audio output",
                            extraMessages=[
                                f"Output file: {outObj.file_path}"
                            ],
                            caller=self.caller
                )
            if outObj.format == MediaFormat.VIDEO_ONLY and bestVideo is None:
                raise TaskFailedError(
                    task="[CORE] FileConverter._buildCommand",
                    reason="No video found for video output",
                    extraMessages=[
                        f"Output file: {outObj.file_path}"
                    ],
                    caller=self.caller
                )
            
            if bestVideo is not None and "-vn" not in command:
                            inputIndex, video = bestVideo
                            command.extend([
                                "-map",
                                f"{inputIndex}:v:{video.index}"
                            ])
            if bestAudio is not None and "-an" not in command:
                inputIndex, audio = bestAudio
                command.extend([
                    "-map",
                    f"{inputIndex}:a:{audio.index}"
                ])


        else:
            raise TaskFailedError(
                task="[CORE] FileConverter._buildCommand",
                reason="Couldn't map stream type",
                extraMessages=[
                    f"Supported audio single streams: {', '.join(AUDIO_SINGLE_STREAM)}",
                    f"Supported audio multi streams: {', '.join(AUDIO_MULTI_STREAM)}",
                    f"Supported video single streams: {', '.join(VIDEO_SINGLE_STREAM)}",
                    f"Supported video + audio multi streams: {', '.join(AUDIO_AND_VIDEO_MULTI_STREAM)}",
                    f"Given file: {outObj.file_path}"
                ],
                caller=self.caller
            )
        

        command.append(outObj.file_path)

        return command
 
    def _probeInput(self):
        FFPROBE_COMMAND = [
            self.ffprobePath,
            "-v", "error",
            "-show_streams",
            "-show_format",
            "-of", "json",
        ]
        
        inputObj = InputFile()
        inputObj.file_path= self.inputList.pop(0)

        

        ffprobeCommand = FFPROBE_COMMAND.copy()
        ffprobeCommand.append(inputObj.file_path)

        try:
            ffprobeResult = subprocess.run(
                ffprobeCommand,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise TaskFailedError(
                task="[CORE] FileConverter._probeInput",
                reason="ffprobe couldn't probe input file",
                extraMessages=[
                    f"File: {inputObj.file_path}",
                    e.stderr or str(e)
                ],
                caller=self.caller
            ) from e
        jsonData = json.loads(ffprobeResult.stdout)

        hasAudio = False
        hasVideo = False

        videoIndex = 0
        audioIndex = 0

        for stream in jsonData.get("streams", []):

            codecType = stream.get("codec_type")

            if codecType == "video":
                
                currentVideoIndex = videoIndex
                videoIndex += 1

                if stream.get("disposition", {}).get("attached_pic", 0) == 1:
                    continue
                hasVideo = True
               
                videoInfo = VideoInfo(
                    index=currentVideoIndex,
                    bitrateVid=self._saveInt(stream.get("bit_rate")),
                    widthVid=self._saveInt(stream.get("width")),
                    heightVid=self._saveInt(stream.get("height")),
                )

                inputObj.videoStreams.append(videoInfo)
  



            elif codecType == "audio":
                hasAudio = True

                
                audioInfo = AudioInfo(
                    index=audioIndex,
                    bitrateAudio=self._saveInt(stream.get("bit_rate")),
                    sampleRate=self._saveInt(stream.get("sample_rate")),
                    bitsPerSample=self._saveInt(
                        stream.get("bits_per_sample")
                        or stream.get("bits_per_raw_sample")
                        ),
                    channels=self._saveInt(stream.get("channels"))
                    )

                
                inputObj.audioStreams.append(audioInfo)
                audioIndex += 1

                    

        if hasAudio and hasVideo:
            inputObj.type = MediaFormat.VIDEO_AND_AUDIO

        elif hasAudio:
            inputObj.type = MediaFormat.AUDIO_ONLY

        elif hasVideo:
            inputObj.type = MediaFormat.VIDEO_ONLY

        else:
            inputObj.type = MediaFormat.UNKNOWN

        return inputObj

    def _saveInt(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _convert_dict_init(self):
       
        self.convertRequest.convert_progress_dict["totalConverts"] = len(self.convertRequest.output_file_list)

#Int converted jobs accomplished
        self.convertRequest.convert_progress_dict["finishedConverts"] = 0

#In Percent
        self.convertRequest.convert_progress_dict["convertProgress"] = 0

        self.convertRequest.convert_progress_dict["status"] = "convert queued"

    def _mediatypeMapping(self, outObj: OutputFile):
        split: list[str] = outObj.file_path.split(".")
        fileEnding: str = split[-1].lower()

        if fileEnding in AUDIO_ONLY_FORMATS:
            outObj.format = MediaFormat.AUDIO_ONLY
        
        elif fileEnding in VIDEO_ONLY_FORMATS:
            outObj.format = MediaFormat.VIDEO_ONLY
        
        elif fileEnding in VIDEO_AND_AUDIO_FORMATS:
            outObj.format = MediaFormat.VIDEO_AND_AUDIO
        
        else:
            outObj.format = MediaFormat.UNKNOWN


        if fileEnding in AUDIO_MULTI_STREAM:
            outObj.stream_capacity = StreamCapacity.MULTI_STREAM

        elif fileEnding in AUDIO_AND_VIDEO_MULTI_STREAM:
            outObj.stream_capacity = StreamCapacity.MULTI_STREAM
        elif fileEnding in VIDEO_ONLY_FORMATS:
            outObj.stream_capacity = StreamCapacity.SINGLE_STREAM

        elif fileEnding in AUDIO_ONLY_FORMATS:
            outObj.stream_capacity = StreamCapacity.SINGLE_STREAM

        

        outObj.file_ending = fileEnding
  