# Core imports
from ..general import Validate
from ..models import errors
from ..processes import AsyncProcessManager, ProcessDrainType
from ..network.file import writeFd

#Own imports
from . import ffmpeg_models

#Python default imports
import os
import shutil
import asyncio


class FFmpegProbeCodec():
    def __init__(
            self,
            file_input: str | None = None,
            use_pipe: bool = False,
            caller:str = "[CORE] FFmpegProbeCodec"
            ):

        self.pipe: ffmpeg_models.FFmpegPipe | None = None

        self.caller = caller

        if not file_input and not use_pipe:
            raise errors.ArgumentError(
                argument="file_input, pipe_input",
                wanted_type="None of them was given",
                caller=f"{self.caller} FFmpegMuxer.__init__"
            )

        if file_input and use_pipe:
            raise errors.ArgumentError(
                argument="file_input, pipe_input",
                wanted_type="Please only provide one",
                caller=f"{self.caller} FFmpegMuxer.__init__"
            )

        if file_input:
            Validate.general.validateStr(
                argument_name="file_input",
                string=file_input,
                caller=f"{self.caller} FFmpegMuxer.__init__"
            )

            if (
                not os.access(file_input)
                or not os.path.isfile(file_input)
            ):
                raise errors.ArgumentError(
                    argument="file_input",
                    wanted_type="string of file path that is accessible",
                    caller=f"{self.caller} FFmpegMuxer.__init__"
                )
            self.inputArg = file_input
            


        if use_pipe:
            
            readFd, writeFd = os.pipe()
            self.inputArg = f"pipe:{readFd}"
            
            self.pipe = ffmpeg_models.FFmpegPipe(
                pipe_index=0,
                read_pipe=readFd,
                write_pipe=writeFd,
                closed=False
            )

        
        self.ffprobePath = shutil.which("ffprobe")
        if not self.ffprobePath:
            raise errors.FFmpegNotFoundError(
                caller=f"{self.caller} FFmpegMuxer.__init__"
            )


    def _buildCommand(self, codec_type: ffmpeg_models.GetCodecTypes):
        ffmpegCommand = [
            self.ffprobePath,
            "-v", "error",
        ]
        if codec_type == ffmpeg_models.GetCodecTypes.VIDEO:
            ffmpegCommand.extend([
                "-select_streams", "v:0"
            ])
        elif codec_type == ffmpeg_models.GetCodecTypes.AUDIO:
            ffmpegCommand.extend([
                "-select_streams", "a:0"
            ])

        ffmpegCommand.extend(
            [
                "-show_entries",
                "stream=codec_type,codec_name",
                "-of", "csv=p=0",
                "-i", self.inputArg
            ]
        )

        return ffmpegCommand


    async def getCodec(
        self,
        codec_type: ffmpeg_models.GetCodecTypes = ffmpeg_models.GetCodecTypes.AUTO
        ) -> list[ffmpeg_models.FFmpegCodec]:

        Validate.general.validateGeneralType(
            argument_name="codec_type",
            obj=codec_type,
            objType=ffmpeg_models.GetCodecTypes,
            caller=self.caller
        )

        Fds = ()

        if self.pipe:
            Fds = (
                self.pipe.read_pipe,
            )

        command = self._buildCommand(
            codec_type
        )

        processManager = AsyncProcessManager(
            process_args=command,
            stdout_drain_type=ProcessDrainType.PRINT,
            stderr_drain_type=ProcessDrainType.PRINT,
            pass_fds=Fds,
            process_name=f"{self.caller} FFmpegProbeCodec-getCodec"
        )

        try:
            await processManager.start()

            if self.pipe and self.pipe.read_pipe is not None:
                os.close(
                    self.pipe.read_pipe
                )
                self.pipe.read_pipe = None


            while True:

                codecList = await self._readStdout(
                    processManager
                )

                if codecList:
                    return codecList


                if processManager.process.returncode is not None:

                    if processManager.stdoutDrainTask:
                        await asyncio.gather(
                            processManager.stdoutDrainTask,
                            return_exceptions=True
                        )

                    return await self._readStdout(
                        processManager
                    )


                await asyncio.sleep(0.02)

        finally:
            await self.closePipe()
            await processManager.stop()

            

    async def _readStdout(self, processManager: AsyncProcessManager):
        codecListRaw: list[str] = processManager.stdoutLines.copy()

        if not codecListRaw:
            return []

        codecList: list[ffmpeg_models.FFmpegCodec] = []

        seenCodecs = set()

        for codec in codecListRaw:

            split = codec.split(",")

            try:
                codecName = split[0]
                codecType = split[1]

            except IndexError:
                continue

            codecKey = (
                codecType,
                codecName
            )

            if codecKey in seenCodecs:
                continue

            seenCodecs.add(codecKey)

            codecList.append(
                ffmpeg_models.FFmpegCodec(
                    codec_type=codecType,
                    codec_name=codecName
                )
            )

        
        print(f"{self.caller} Found codec/s: '{codecList}'")
        return codecList




    async def writePipe(self, data:bytes):

        if not self.pipe:
            print(f"{self.caller} writePipe: choosen input type is file. Returning... ")
            return

        if self.pipe.closed:
            print(f"{self.caller} writePipe: Pipe is already closed")
            return

        Validate.general.validateGeneralType(
            argument_name="data",
            obj=data,
            objType=bytes,
            caller=self.caller
        )

        await writeFd(self.pipe.write_pipe, data)



    async def closePipe(self):
        if not self.pipe:
            print(f"{self.caller} writePipe: choosen input type is file. Returning... ")
            return

        if self.pipe.closed:
            print(f"{self.caller} writePipe: Pipe is already closed")
            return

        if self.pipe.read_pipe:
            os.close(self.pipe.read_pipe)
            self.pipe.read_pipe = None

        if self.pipe.write_pipe:
            os.close(self.pipe.write_pipe)
            self.pipe.write_pipe = None
        
        self.pipe.closed = True



