import PythonModule.core as core
import os
import re
import urllib.request, urllib.error

def download(
        url: str,
        session: core.request.Session.Session,
        outFile: str
):
    
    html = core.general.Html.getHtml(
        session,
        url
    )


    hosts:dict = getHosts(html)

    if "Filemoon" in hosts.keys():
        FilemoonDownload(
            session,
            redirectURL= hosts.get("Filemoon", None),
            outFile=outFile
        )
        

    


def getHosts(
        html: str
) -> dict:
    hostPattern = r'(<a class="watchEpisode".*?</a>)'
    namePattern = r'<h4>(.*?)</h4>'
    redirectPattern = r'href="(.*?)"'
    matches = re.findall(hostPattern, html, re.DOTALL)
    hosts = {}

    for match in matches:

        host: str = core.searchBlocks(
            pattern=namePattern,
            searchBlock=match
        )
        redirect: str = core.searchBlocks(
            pattern=redirectPattern,
            searchBlock=match
        )
        if host and redirect:
            hosts[host] = redirect
    
    return hosts





def FilemoonDownload(
        session: core.request.Session.Session,
        redirectURL: str,
        outFile: str

): 
    if not redirectURL:
        raise ValueError("VOEDownload: Didn't get redirect url...")
    url = "https://aniworld.to" + redirectURL
    htmlRequest = urllib.request.Request(
        url,
        method="GET"
    )

    try:
        with session.open(request=htmlRequest) as response:
            videoUrl = response.geturl()
            
        print("starting browser")
        m3u8Url = filemoonBrowser(
            videoUrl
        )
        if not m3u8Url:
            raise ValueError("FilemoonDownload: Didn't find a m3u8 url")
        if "master" in m3u8Url:

            masterRequest = urllib.request.Request(
                m3u8Url,
                method="GET"
            )
            with session.open(request=masterRequest) as response:
                masterFile = response.read().decode("utf-8")
                print(masterFile)

            m3u8Url = core.findBestQualityMasterM3U8(
                manifestUrls=masterFile,
            )
        FilemoonDownloadToFile(
            indexUrl=m3u8Url,
            session=session,
            outFile=outFile
        )
        


    except Exception as e:
        raise e
    
def FilemoonDownloadToFile(
        indexUrl: str,
        session: core.request.Session.Session,
        outFile: str
):
    request = urllib.request.Request(
        indexUrl,
        method="GET"
    )
    try:
        with session.open(request=request) as response:
            indexFile = response.read().decode("utf-8")
    
    except Exception as e:
        raise e
    
    pattern = r'(https://.*?)#'
    matches = re.findall(pattern, indexFile, re.DOTALL)
    segment = 0
    try:
        with open(outFile, 'ab') as f:
            for match in matches:
                segment += 1
                
                request = urllib.request.Request(
                    match,
                    method="GET"
                )
                with session.open(request=request, timeout=60) as response:
                    data = response.read()
                    print(f"Segment {segment}: {len(data)} bytes")
                    f.write(data)
                
    except Exception as e:
        raise e
    
