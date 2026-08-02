import PythonModule.core as core
import urllib.request, urllib.parse
import gzip
import zlib
import asyncio
import subprocess



async def run_shell_command_async(command: str):
    await asyncio.to_thread(
        subprocess.run,
        command,
        shell=True,
        check=True,
        executable="/bin/bash"
    )

ses:core.request.Session.Session = core.request.Session.Session()

iFramePattern = r'<iframe[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>'

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:149.0) Gecko/20100101 Firefox/149.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Sec-Fetch-Storage-Access": "none",
    "Connection": "keep-alive",
    "Referer": "https://www.wcoflix.tv/",
    "Cookie": "PHPSESSID=fir8vjjgm4b0qcm41be8sp6ire",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "DNT": "1",
    "Sec-GPC": "1",
    "Priority": "u=4",
    "TE": "trailers",
}

def _indexUrlToPlayerUrl (
        indexUrl: str 
        ) -> str:
    parts = urllib.parse.urlsplit(indexUrl)
    return urllib.parse.urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            "/inc/embed/video-js.php",
            parts.query,
            parts.fragment
        )
    )
    
startEpisode: int = 1
episodes: int = 26
startStaffel: int = 1
endStaffel: int = 1


async def downloadEpisodeInner(staffel: int, episode: int):

    url: str = f"https://www.wcoflix.tv/azumanga-daioh-episode-{episode}-english-dubbed"
    outFile: str = f"Azumanga Daioh S{staffel:02d}E{episode:02d} - English.ts"

    episodeHTML: str = core.general.html.getHtml(ses, url)


    indexUrl:str = core.general.regexFind.searchBlocks(iFramePattern, episodeHTML)
    print(indexUrl)
    request = urllib.request.Request(indexUrl, headers=headers)

    with ses.open(request=request) as response: 
        indexHTMLRAW = response.read()

        encoding = response.headers.get("Content-Encoding", "").lower()
        

        if encoding == "gzip":
            indexHTMLRAW = gzip.decompress(indexHTMLRAW)
        elif encoding == "deflate":
            indexHTMLRAW = zlib.decompress(indexHTMLRAW)
        playerHTML: str = indexHTMLRAW.decode("utf-8", errors="replace")

#    with open("test3.txt", "w", encoding="utf-8") as f:
#        f.write(playerHTML)
    playerUrl: str = _indexUrlToPlayerUrl(indexUrl)
    print(playerUrl)

    mediaList: core.models.media.MediaList = await asyncio.to_thread(core.request.emergencyBrowser.wcoflixBrowserDiscoverStreamUrls,
        indexUrl,
        headless=True,
        adBlock=True,
        extraHeaders={
            "Referer": "https://www.wcoflix.tv/"
        }
    )
    candidate = mediaList.candidates[-1]
    ffmpegCommand = core.general.curlToFFMPEG.curl_to_ffmpeg_command(
                candidate.curlCommand,
                output=outFile
            )

    await run_shell_command_async(ffmpegCommand)

    print(f"E{episode}: downloaded with ffmpeg")
    

async def downloadEpisode(staffel: int, episode:int, sem: asyncio.Semaphore):
    async with sem:
        await downloadEpisodeInner(staffel, episode)


async def main():
    sem = asyncio.Semaphore(7)

    tasks = [
        asyncio.create_task(downloadEpisode(x, i, sem))
        for x in range(startStaffel, (endStaffel + 1))
        for i in range(startEpisode, (episodes + 1))
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for episode, result in zip(range(startEpisode, (episodes + 1)), results):
        if isinstance(result, Exception):
            print(f"E{episode}: exception occurred: {result}")


if __name__ == "__main__":
    asyncio.run(main())