# Core imports

from ..general import Validate
from ..models import errors
from ..processes import AsyncProcessManager, ProcessDrainType

#Own imports
from . import ffmpeg_models

#Python default imports
import shutil








class AsyncFFmpegMuxer:
    def __init__(
            self,
            file_ending: str,
            input_count: int = 2,
            codecs: list[ffmpeg_models.FFmpegCodec] | None = None,
            caller: str = "[CORE] FFmpegMuxer"
            ):
        """
        Create multiple pipes that you can give bytes to.
        FFmpeg will read the bytes inputed into these pipes and adds them together.
        Only one output via stdout as bytes.
        Default use case of this function is to add split video and audio back together.
        Maybe adding sync version later...
        """

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


        if codecs:
            Validate.general.validateGeneralType(
                argument_name="codecs",
                obj=codecs,
                objType=list,
                caller=f"{caller} FFmpegMuxer.__init__"
            )
            for codec in codecs:
                Validate.general.validateGeneralType(
                    argument_name="codec",
                    obj=codec,
                    objType=ffmpeg_models.FFmpegCodec,
                    caller=f"{caller} FFmpegMuxer.__init__"
                )

        

        self.caller = caller


        ffmpegPath = shutil.which("ffmpeg")
        if not ffmpegPath:
            raise errors.FFmpegNotFoundError(
                caller=f"{self.caller} FFmpegMuxer.__init__"
            )

        self.manager = AsyncProcessManager(
            stdout_drain_type=ProcessDrainType.MANUAL,
            process_name=caller,
            input_count=input_count
            
        )
        
        self.args = [ffmpegPath]

        for i in range(input_count):
            pipeName = self.manager.getInputName(i)
            self.args.extend([
                "-i", pipeName
            ])
      
        self.args.extend(self._getOutputArgs(file_ending, codecs))
        

        
        

        self.started: bool = False



    async def start(self):
        if self.started:
            print(f"{self.caller} start: Process has already started. Not starting again!")
            return

        await self.manager.start(self.args)
        self.started = True



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
            await self.manager.stop()


    async def writePipe(
            self, 
            data: bytes,
            pipe_index: int
            ):
        await self.manager.writePipe(data, pipe_index)



    async def closePipe(
            self,
            pipe_index: int
    ):
        await self.manager.closePipe(pipe_index)
    



    
    


    def _getOutputArgs(
            self,
            file_ending: str,
            codecs: list[ffmpeg_models.FFmpegCodec] | None = None
            ) -> list[str]:

        codecs = codecs or []

        ending = file_ending.lower()

        args = []

        container = ffmpeg_models.CONTAINERS.get(ending)

        if not container:
            raise errors.TaskFailedError(
                task=f"{self.caller}._getOutputArgs",
                reason="Unsupported File was given",
                extraMessages=[
                    f"Given file: '{ending}'",
                    f"Supported files: {', '.join(ffmpeg_models.CONTAINERS.keys())}"
                ],
                caller=self.caller
            )


        allowedCodecTypes = container.get(
            "allowed_codec_types",
            []
        )

        allowedCodecs = container.get(
            "allowed_codecs",
            {}
        )

        defaultEncoders = container.get(
            "default_encoders",
            {}
        )

        copyCodecArgs = container.get(
            "copy_codec_args",
            {}
        )


        for codec in codecs:

            if codec.codec_type not in allowedCodecTypes:
                print(
                    f"{self.caller}._getOutputArgs: "
                    f"Skipping codec '{codec.codec_name}' because codec type "
                    f"'{codec.codec_type}' is not allowed in '{ending}'"
                )
                continue


            if codec.codec_type == "video":
                codecArg = f"-c:v"
                mapArg = f"{codec.input_index}:v:0"

            elif codec.codec_type == "audio":
                codecArg = f"-c:a"
                mapArg = f"{codec.input_index}:a:0"

            else:
                print(
                    f"{self.caller}._getOutputArgs: "
                    f"Skipping unsupported codec type '{codec.codec_type}'"
                )
                continue

            args.extend([
                "-map",
                mapArg
            ])


            allowedForType = allowedCodecs.get(
                codec.codec_type,
                []
            )


            if codec.codec_name in allowedForType:

                args.extend([
                    codecArg,
                    "copy"
                ])

                args.extend(
                    copyCodecArgs.get(
                        codec.codec_name,
                        []
                    )
                )

                print(
                    f"{self.caller}._getOutputArgs: "
                    f"Codec '{codec.codec_name}' can be copied into '{ending}'"
                )


            else:

                encoder = defaultEncoders.get(
                    codec.codec_type
                )

                if not encoder:
                    raise errors.TaskFailedError(
                        task=f"{self.caller}._getOutputArgs",
                        reason="No encoder available for codec type",
                        extraMessages=[
                            f"File ending: '{ending}'",
                            f"Codec type: '{codec.codec_type}'",
                            f"Input codec: '{codec.codec_name}'"
                        ],
                        caller=self.caller
                    )


                args.extend([
                    codecArg,
                    encoder
                ])

                print(
                    f"{self.caller}._getOutputArgs: "
                    f"Codec '{codec.codec_name}' cannot be copied into "
                    f"'{ending}'. Using encoder '{encoder}'"
                )


        args.extend(
            container.get(
                "extra_output_args",
                []
            )
        )

        args.extend([
            "-f",
            container.get("ffmpeg_format"),
            "pipe:1"
        ])


        return args
      
                
        