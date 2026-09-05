
import PythonModule.core as core
from PythonModule.core.network import browser
from PythonModule.core.network import Session


from . import youtube_models
from . import youtube_browser
from .. import models

# Python default imports
import urllib.parse, urllib.request, urllib.error
import json
import time



def getMediaInformation(
        request: models.ProviderResultRequest,
        retrys: int = 3,
) -> models.ProviderResult:

    core.general.Validate.general.validateGeneralType(
        argument_name="request", obj=request, objType=models.ProviderResultRequest, caller="[Youtube] getMediaInformation"
    )

    core.general.Validate.general.validateInt(
        argument_name="retrys", integer=retrys, caller="[Youtube] getMediaInformation"
    )

    core.general.Validate.special.validateHostPro(
        url=request.url,
        allowed_protocols_list=["https"],
        allowed_hostnames_list=["youtube.com", "www.youtube.com"],
        caller="[Youtube] getMediaInformation"
        )

    parsedUrl = urllib.parse.urlparse(request.url)
    query = urllib.parse.parse_qs(parsedUrl.query)

    resolvedUrl = request.url
    
    if query.get("list", [None])[0]:
        query.pop("list")

        resolvedUrl = urllib.parse.urlunparse(
            parsedUrl._replace(
                query=urllib.parse.urlencode(query, doseq=True)
            )
        )


    mediaType = request.preferred_type if request.preferred_type else "video"

    url, downloadType, fileEnding = _tryGetUsableUrls(
        watch_url=resolvedUrl,
        session=request.ses,
        preferred_type=request.preferred_type
        )

    if url:
        if downloadType == core.models.Download.DownloadType.HLS:

            return models.ProviderResult(
                    url=url,
                    download_type=downloadType,
                    file_ending="ts",
                    media_type="video",
                    mime_type=f"application/vnd.apple.mpegurl",
                    total_size=-1,
                    info=core.models.Download.Info(
                        url=resolvedUrl,
                        found_file="ts",
                        preferred_file=request.preferred_file,
                        preferred_type=request.preferred_type,
                        found_type="video"
                    )
            )


    

    return models.ProviderResult(
        url=resolvedUrl,
        download_type=core.models.Download.DownloadType.UMP,
        file_ending="webm",
        media_type=mediaType,
        mime_type=f"{mediaType}/webm",
        total_size=1,
        info=core.models.Download.Info(
            url=resolvedUrl,
            found_file="webm",
            preferred_file=request.preferred_file,
            preferred_type=request.preferred_type,
            found_type=mediaType
        )


    )
def _getVideoIdFromYoutubeUrl(url: str):
    parsedUrl = urllib.parse.urlparse(url)
    if not "youtube.com" in parsedUrl.hostname:
        raise core.models.errors.ArgumentError(
            argument="url",
            wanted_type="string -> youtube.com URL",
            caller="[Youtube] _getVideoIdFromYoutubeUrl"
        )


    query = urllib.parse.parse_qs(parsedUrl.query)
    videoId = query.get("v", [None])[0]
    if not videoId:
        raise core.models.errors.TaskFailedError(
            task="[Youtube] _getVideoIdFromYoutubeUrl",
            reason="Couldn't extract video ID from Youtube URL",
            caller="[Youtube] _tryGetUsableUrls",
            extraMessages=[
                "The value of query 'v' was None",
                f"Used url: {url}"
            ]
        )
    return videoId




def _tryGetUsableUrls(
        watch_url: str,
        session: Session.Session,
        preferred_type: str = ""
        ):
    videoId: str = _getVideoIdFromYoutubeUrl(watch_url)

    

    for method in youtube_models.GET_METHODS:
        print(f"[Youtube] Trying method '{method}'...")

        
        jsonData = _sendRequest(videoId, method, session)

        if jsonData is None:
            print(f"[Youtube] Couldn't get jsonData from player API with method {method}")
            continue
        


        playabilityStatus = next(core.general.DataSearch.iterValueFromJson(data=jsonData, value="playabilityStatus"), None)
    

        if playabilityStatus.get('status') == "LOGIN_REQUIRED":
            
            visitorData = jsonData.get('responseContext', {}).get('visitorData', "")
            print(visitorData)


            jsonData = _sendRequest(videoId, method, session, visitorData)
            
            if jsonData is None:
                print(f"[Youtube] Couldn't get jsonData from player API with method {method}")
                continue

            
            playabilityStatus = next(core.general.DataSearch.iterValueFromJson(data=jsonData, value="playabilityStatus"), None)

        if playabilityStatus.get('status') == "LOGIN_REQUIRED":
            continue

        streamingData = jsonData.get("streamingData")
        

        formats = (
            streamingData.get("formats", [])
            + streamingData.get("adaptiveFormats", [])
        )


        HLSManifest = streamingData.get("hlsManifestUrl", None)
        if HLSManifest:
            return [HLSManifest, core.models.Download.DownloadType.HLS, "ts"]


        bestAudioAndVideoCandidate = _extractVideoAudioFromFormats(formats)

        if bestAudioAndVideoCandidate:
            return [
                bestAudioAndVideoCandidate.get('url'),
                core.models.Download.DownloadType.FILE,
                bestAudioAndVideoCandidate.get('mimeType').split(";", 1)[0].strip()
                ]

    #Note for later: Add adaptive formats where video and audio is split. FileDispatcher can't handle split video and audio at the current time of writing
    raise core.models.errors.TaskFailedError(
        task="[Youtube] _tryGetUsableUrls",
        reason="Neither direct media with audio+video was found nor a hls manifest given",
        caller="[Youtube] getMediaInformation",
        extraMessages=[
            "Now listening given youtube response",
            streamingData
        ]
    )

        

        
            


def _extractVideoAudioFromFormats(formats: list):
    candidates = []

    for formatData in formats:
        print(formatData)
        url = formatData.get("url")
        mimeType = formatData.get("mimeType", "")

        if not url:
            continue

#RN only accept files that include video and audio at the same time
        if not mimeType.startswith("video/"):
            continue

        hasAudioCodec = any(
            codec in mimeType
            for codec in (
                "mp4a",
                "opus",
                "vorbis",
            )
        )

        if not hasAudioCodec:
            continue

        candidates.append(formatData)

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda f: (
            f.get("height", 0),
            f.get("fps", 0),
            f.get("bitrate", 0),
        )
    )






def _sendRequest(
        videoId: str,
        method: youtube_models.GetMediaMethod,
        session: Session.Session,
        visitor_data: str | None = None
):
   
    playerUrl = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
    
    payload = {
                "context" : youtube_models.CONTEXT_MAPPING.get(method),
                "videoId": videoId
            }
    
    body = json.dumps(payload).encode("utf-8")

    headers = youtube_models.HEADER_MAPPING.get(method)
    if visitor_data:
        headers["X-Goog-Visitor-Id"] = visitor_data

    req = urllib.request.Request(
        playerUrl,
        headers=headers,
        method="POST",
        data=body
    )


    try:
        with session.open(request=req) as response:
            jsonData = json.load(response)
            return jsonData


    except urllib.error.HTTPError as e:
        print("HTTP:", e.code)
        print(e.read().decode("utf-8", errors="replace"))
    return None