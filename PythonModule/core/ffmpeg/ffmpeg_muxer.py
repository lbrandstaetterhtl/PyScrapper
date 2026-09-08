# Core imports

from ..general import Validate
from ..models import errors
from ..processes import AsyncProcessManager, ProcessDrainType
from ..network.file import writeFd

#Own imports
from .ffmpeg_models import FFMPEG_FORMAT_MAPPING

#Python default imports
import os
import shutil
from dataclasses import dataclass


@dataclass
class FFmpegPipe:
    pipe_index: int
    read_pipe: int
    write_pipe: int
    closed : bool = False



class FFmpegMuxer:
    def __init__(
            self,
            file_ending: str,
            input_count: int = 2,
            maps: list[str] | None = None,
            caller: str = "[CORE] FFmpegMuxer"
            ):
        """
        Create multiple pipes that you can give bytes to.
        FFmpeg will read the bytes inputed into these pipes and adds them together.
        Only one output via stdout as bytes.
        Default use case of this function is to add split video and audio back together.
        Maybe adding sync version later...
        """

        if maps is None:
            maps = [
                "0:v:0",
                "1:a:0",
            ]

        Validate.general.validateInt(
            argument_name="input_count",
            integer=input_count,
            caller=f"{caller} FFmpegMuxer.__init__"
        )

        Validate.general.validateStr(
            argument_name="file_ending",
            string=file_ending,
            caller=f"{caller} FFmpegMuxer.__init__"
        )

        Validate.general.validateListStr(
            argument_name="maps",
            liste=maps,
            caller=f"{caller} FFmpegMuxer.__init__"
        )

        

        self.caller = caller


        ffmpegPath = shutil.which("ffmpeg")
        if not ffmpegPath:
            raise errors.FFmpegNotFoundError(
                caller=f"{self.caller} FFmpegMuxer.__init__"
            )
        
        args = [ffmpegPath]

        self.pipes: list[FFmpegPipe] = []

        Fds = ()
        for p in range(input_count):
            readFd, writeFd = os.pipe()
            args.extend([
                "-i",
                f"pipe:{readFd}"
            ])


            self.pipes.append(
                FFmpegPipe(
                    pipe_index=p,
                    read_pipe=readFd,
                    write_pipe=writeFd
                )
            )
            Fds += (readFd,)

        for map in maps:
            args.extend([
                "-map",
                map
            ])

        outputFormat = FFMPEG_FORMAT_MAPPING.get(file_ending.lower(), None)
        if not outputFormat:
            raise errors.TaskFailedError(
                task="[CORE] FFmpegMuxer.__init__",
                reason="Couldn't get outputFormat for given file ending",
                extraMessages=[
                    f"Given file ending: '{file_ending}'",
                    f"Supported file endings: {', '.join(FFMPEG_FORMAT_MAPPING.keys())}"
                ],
                caller=f"{self.caller} FFmpegMuxer.__init__"
            )
        args.extend(self._getOutputArgs(file_ending))

        
        self.manager = AsyncProcessManager(
            args,
            stdout_drain_type=ProcessDrainType.MANUAL,
            process_name=caller,
            pass_fds=Fds
        )

        self.started: bool = False



    async def start(self):
        if self.started:
            print(f"{self.caller} start: Process has already started. Not starting again!")
            return

        await self.manager.start()
        self.started = True

        # FFmpeg inherited these FDs.
        # Parent doesn't need its read sides anymore.
        for pipe in self.pipes:
            if pipe.read_pipe is not None:
                os.close(pipe.read_pipe)
                pipe.read_pipe = None





    async def output(
            self
            ):
        
        if not self.started:
            print(f"{self.caller} output: Process hasn't started yet. Please call 'start' first")
            return

        try:
            while True:
                chunk, eof = await self.manager.readStdout()

                if eof:
                    break

                yield chunk

            returnCode = await self.manager.wait()

            if returnCode != 0:
                raise errors.TaskFailedError(
                    task="FFmpegMuxer.downloadAndYield",
                    reason=f"FFmpeg returned code '{returnCode}'",
                    caller=self.caller,
                    extraMessages=[
                        "FFmpeg stderr:",
                        *self.manager.stderrLines[-30:],
                    ],
                )

        finally:
            for pipe in self.pipes:
                if pipe.write_pipe is not None:
                    os.close(pipe.write_pipe)
                    pipe.write_pipe = None

                if pipe.read_pipe is not None:
                    os.close(pipe.read_pipe)
                    pipe.read_pipe = None

                pipe.closed = True

            await self.manager.stop()



    def _checkPipeIndex(self, pipe_index: int, call_function: str):
        if not isinstance(pipe_index, int):
            raise errors.ArgumentError(
                argument="pipe_index",
                wanted_type="int",
                obj=pipe_index,
                caller=f"{self.caller} {call_function}"
            )

        if pipe_index not in range(len(self.pipes)):
            raise errors.ArgumentError(
                argument="pipe_index",
                wanted_type=f"valid pipe index from 0 to {len(self.pipes) - 1}",
                obj=pipe_index,
                caller=f"{self.caller} {call_function}",
            )




    async def closePipe(
            self,
            pipe_index: int = 0
    ):
        self._checkPipeIndex(pipe_index, "closePipe")


        
        pipe = self.pipes[pipe_index]

           
        if pipe.closed:
            print(f"{self.caller} Pipe '{pipe_index}' is already closed")
            return

        if pipe.write_pipe is not None:
            
            os.close(pipe.write_pipe)
            pipe.write_pipe = None
            
        print(f"{self.caller} Successfully closed pipe with the index {pipe_index}")
        pipe.closed = True
        
        
                

    async def writePipe(
            self,
            data: bytes,
            pipe_index: int = 0
    ):
        if not self.started:
            print(f"{self.caller} writePipe: Process hasn't started yet. Please call 'start' first")
            return
        
        Validate.general.validateGeneralType(
            argument_name="data",
            obj=data,
            objType=bytes,
            caller=f"{self.caller} writePipe"
        )


        self._checkPipeIndex(pipe_index, "writePipe")

        pipe = self.pipes[pipe_index]

       

        if pipe.closed:
            print(f"{self.caller} writePipe: Pipe with the index {pipe_index} is already closed")
            return

        await writeFd(pipe.write_pipe, data)



    def _getOutputFormatFromFileEnding(self, file_ending:str):
            Validate.general.validateStr(argument_name="file_ending", string=file_ending, caller="[CORE] FFmpegDownload._getOutputFormatFromFileEnding")
            format = FFMPEG_FORMAT_MAPPING.get(file_ending.lower())
    
            if not format:
                raise ValueError(f"[FFmpegDownload]._getOutputFormatFromFileEnding: Unsupported file ending: {file_ending}")
            return format
    


    def _getOutputArgs(self, file_ending: str) -> list[str]:
            ending = file_ending.lower()
    
            format = self._getOutputFormatFromFileEnding(ending)
    
            args = []
    
            if ending in ("mp4", "m4a"):
                args += [
                    "-movflags",
                    "+frag_keyframe+empty_moov+default_base_moof",
                    "-bsf:a",
                    "aac_adtstoasc",
                ]
    
            args += [
                "-c", "copy",
                "-f", format,
                "pipe:1",
            ]
    
            return args
      
                
        