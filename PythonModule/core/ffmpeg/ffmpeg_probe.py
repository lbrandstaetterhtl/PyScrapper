# Core imports
from ..general import Validate
from ..models import errors
from ..processes import AsyncProcessManager, ProcessDrainType


#Own imports
from . import ffmpeg_models

#Python default imports
import os
import shutil
import asyncio


class AsyncFFmpegProbeCodec():
    def __init__(
            self,
            file_input: str | None = None,
            use_pipe: bool = False,
            caller:str = "[CORE] FFmpegProbeCodec"
            ):

        self.usePipe:bool = use_pipe

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

        self.processManager = AsyncProcessManager(
                    
            stdout_drain_type=ProcessDrainType.PRINT,
            stderr_drain_type=ProcessDrainType.PRINT,
            input_count=1 if use_pipe else 0,
            process_name=f"{self.caller} FFmpegProbeCodec-getCodec"
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

        elif use_pipe:
            self.inputArg = self.processManager.getInputName(0)
            
            


        
            
            

        
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

        

       

        self.command = self._buildCommand(
            codec_type
        )

        

        try:
            await self.processManager.start(self.command)

            while True:

                codecList = await self._readStdout(
                    self.processManager
                )

                if codecList:
                    return codecList


                if self.processManager.process.returncode is not None:

                    if self.processManager.stdoutDrainTask:
                        await asyncio.gather(
                            self.processManager.stdoutDrainTask,
                            return_exceptions=True
                        )

                    return await self._readStdout(
                        self.processManager
                    )


                await asyncio.sleep(0.02)

        finally:
            await self.closePipe()
            await self.processManager.stop()

            

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
        if not self.usePipe:
            print(f"{self.caller} writePipe: choosen input type is file. Returning... ")
            return
        await self.processManager.writePipe(pipe_index=0, data=data)

        



    async def closePipe(self):
        if not self.usePipe:
            print(f"{self.caller} writePipe: choosen input type is file. Returning... ")
            return

        await self.processManager.closePipe(pipe_index=0)



