from ...models import Download

import shutil
import asyncio

async def downloadAndYieldYTDLPSimple(
    context: Download.DownloadContext
):
    ffmpegPath = shutil.which("ffmpeg")

    if not ffmpegPath:
        raise ValueError("[CORE] downloadAndYieldYTDLP: Couldn't find ffmpeg on this system which is required for muxing")


    ytdlpSearch = "bestaudio" if context.info.preferred_type == "audio" else "bestvideo+bestaudio"

    args = [
        "yt-dlp",
        "--ignore-config",

        "-f", ytdlpSearch,
        "-o", "-",
        
        "--merge-output-format",
        context.info.found_file,
        "--ffmpeg-location",
        ffmpegPath,

        context.target.resolved_url,


    ]

    stderrLines :list[str] = []

    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )


    async def readStderr():
        while True:
            line = await process.stderr.readline()

            if not line:
                break

            text = line.decode(
                "utf-8",
                errors="replace",
            ).rstrip()

            stderrLines.append(text)

            print(f"[yt-dlp] {text}")

    stderrTask = asyncio.create_task(
        readStderr()
    )

    


    try:
        while True:
            chunk = await process.stdout.read(
                64 * 1024
            )

            if not chunk:
                break

            yield chunk

        returnCode = await process.wait()

        await stderrTask

        if returnCode != 0:
            raise RuntimeError(
                "[CORE] downloadAndYieldYTDLP failed\n"
                f"yt-dlp exited with code {returnCode}\n"
                + "\n".join(stderrLines[-20:])
            )

    finally:
        if process.returncode is None:
            process.terminate()

            try:
                await asyncio.wait_for(
                    process.wait(),
                    timeout=3
                )

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        if not stderrTask.done():
            stderrTask.cancel()

