#Core imports
from ..general import Validate
from ..models import errors
from ..processes import AsyncProcessManager, ProcessDrainType

# Own imports
from .ffmpeg_models import FFMPEG_FORMAT_MAPPING


#Python default imports
import shutil
import os
import subprocess


class FFmpegDownload:
    def __init__(
            self,
            ffmpeg_path:str | None = None,
            chunk_size:int = 8192,
            extra_headers :dict | None = None
            ):

        Validate.general.validateInt(argument_name="chunk_size", integer=chunk_size, caller="[CORE] FFmpegDownload.__init__")

        if not ffmpeg_path:
            ffmpeg_path = shutil.which("ffmpeg")

            if not ffmpeg_path:
                raise errors.FFmpegNotFoundError(caller="[FFmpegDownload].__init__")

        
        self.chunkSize = chunk_size
        self.ffmpegPath = ffmpeg_path
        self.headers = ""
        if extra_headers:
            self._makeFFmpegHeaders(extra_headers)



    def _makeFFmpegHeaders(self, headers: dict):
        Validate.general.validateDict(argument_name="extra_headers", dictionary=headers, caller="[CORE] FFmpegDownload._makeFFmpegHeaders")
        for header, value in headers.items():
            self.headers += f"{header}: {value}\r\n"


    def downloadToFile(
            self,
            input1:str,
            output:str,
            input2:str | None = None,

    ):
        Validate.general.validateStr(argument_name="input1", string=input1, caller="[CORE] FFmpegDownload.downloadToFile")
        Validate.general.validateStr(argument_name="output", string=output, caller="[CORE] FFmpegDownload.downloadToFile")
        args = [
            self.ffmpegPath,
            
            ]

        if self.headers:
            args += [
                "-headers",
                self.headers
            ]

        args += [
            "-i", 
            input1
        ]
            

        if input2:
            Validate.general.validateStr(argument_name="input2", string=input2, caller="[CORE] FFmpegDownload.downloadToFile")
            if self.headers:
                args += [
                    "-headers",
                    self.headers
                ]

            args += [
                "-i", input2,

                "-map", "0:v:0",
                "-map", "1:a:0",
            ]
        args += [
            "-c", "copy",
            "-y",
            output,
        ]

        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode != 0:
            stderr = result.stderr.decode(
                errors="replace"
            )

            raise errors.TaskFailedError(
                task="[CORE] FFmpegDownload.downloadToFile",
                reason=f"FFmpeg exited with code {result.returncode}",
                extraMessages=[stderr[-4000:]],
            )


            





    async def downloadAndYield(
            self,
            input1:str,
            file_ending: str,
            input2: str | None = None,
            
    ):

        Validate.general.validateStr(argument_name="input1", string=input1, caller="[CORE] FFmpegDownload.downloadAndYield")
        Validate.general.validateStr(argument_name="file_ending", string=file_ending, caller="[CORE] FFmpegDownload.downloadAndYield")

        args = [
            self.ffmpegPath,
        ]
        if self.headers:
            args += [
                "-headers",
                self.headers
            ]

        args += [
            "-i", 
            input1
        ]

        if input2:
            Validate.general.validateStr(argument_name="input2", string=input2, caller="[CORE] FFmpegDownload.downloadAndYield")
            if self.headers:
                args += [
                    "-headers",
                    self.headers
                ]

            args += [
                "-i", input2,

                "-map", "0:v:0?",
                "-map", "1:a:0?",
            ]

        args.extend(self._getOutputArgs(file_ending))


        ffmpegProcess = AsyncProcessManager(
            process_args=args,
            stdout_drain_type=ProcessDrainType.MANUAL,
            process_name="FFmpegDownload"
            )

        
        await ffmpegProcess.start()

        
        try:
            while True:
                chunk, eof = await ffmpegProcess.readStdout(self.chunkSize)

                if eof:
                    break

                yield chunk

            returnCode = await ffmpegProcess.wait()

            if returnCode != 0:
                stderr = "\n".join(ffmpegProcess.stderrLines)

                if "403 Forbidden" in stderr or "HTTP error 403" in stderr:
                    raise errors.FFmpegHttpError(
                        status_code=403,
                        url=input1
                    )

                if "401 Unauthorized" in stderr or "HTTP error 401" in stderr:
                    raise errors.FFmpegHttpError(
                        status_code=401,
                        url=input1
                    )
                raise errors.TaskFailedError(
                    task="[CORE] FFmpegDownload.downloadAndYield",
                    reason=f"FFmpeg exited with code {returnCode}",
                )

        finally:
            await ffmpegProcess.stop()
        




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
                "-movflags", "frag_keyframe+empty_moov",
            ]

        args += [
            "-c", "copy",
            "-f", format,
            "pipe:1",
        ]

        return args
