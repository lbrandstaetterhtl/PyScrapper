
import PythonModule.core as core
from PythonModule.core.network import browser
from PythonModule.core.network import Session


from . import youtube_models
from . import youtube_browser
from .. import models

# Python default imports
import urllib.parse, urllib.request, urllib.error
import json
from dataclasses import dataclass, field

@dataclass
class YoutubeResult:
    container: str

    download_type : core.models.Download.DownloadType

    video_url: str
    mime_type: str 

    audio_url: str = ""

    extra_headers : dict = field(default_factory=dict)


@dataclass
class BestCandidate:
    url: str = ""

    container: str = ""
    codec: str = ""

    prio: int = -1


    


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


    result: YoutubeResult = _tryGetUsableUrls(
        watch_url=resolvedUrl,
        request=request
        )

    print(result)

    

    return models.makeProviderResult(
        found_media_list=[
            models.FoundMedia(
                extension=result.container,
                url=result.video_url,
                stream_type=result.download_type,
                media_type=result.mime_type.split("/")[0],
                mime_type=result.mime_type,
                extra_headers=result.extra_headers,
                audio_url=result.audio_url,
    

            )
        ],
        request=request
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
        request: models.ProviderResultRequest
        ):
    videoId: str = _getVideoIdFromYoutubeUrl(watch_url)

    

    for method in youtube_models.GET_METHODS:
        print(f"[Youtube] Trying method '{method}'...")

        
        jsonData = _sendRequest(videoId, method, request.ses)

        if jsonData is None:
            print(f"[Youtube] Couldn't get jsonData from player API with method {method}")
            continue
        


        playabilityStatus = next(core.general.DataSearch.iterValueFromJson(data=jsonData, value="playabilityStatus"), None)
    

        if playabilityStatus.get('status') == "LOGIN_REQUIRED":
            
            visitorData = jsonData.get('responseContext', {}).get('visitorData', "")
            print(visitorData)


            jsonData = _sendRequest(videoId, method, request.ses, visitorData)
            
            if jsonData is None:
                print(f"[Youtube] Couldn't get jsonData from player API with method {method}")
                continue

            
            playabilityStatus = next(core.general.DataSearch.iterValueFromJson(data=jsonData, value="playabilityStatus"), None)

        if playabilityStatus.get('status') == "LOGIN_REQUIRED":
            continue

        streamingData = jsonData.get("streamingData", {})
        

        formats = (
            streamingData.get("formats", [])
            + streamingData.get("adaptiveFormats", [])
        )

        with open("youtube_formats.txt", "w", encoding="utf-8") as f:
            for format in formats:
                f.write(f"{format}\n\n")

        
        result = _extractSeperatedVideoAudioFromFormats(formats=formats, preferred_type=request.preferred_type, preferred_file=request.preferred_file)
        if result:
            result.extra_headers = youtube_models.HEADER_MAPPING.get(method)
            return result
        
        HLSManifestUrl = streamingData.get("hlsManifestUrl", None)
        if HLSManifestUrl:
            return YoutubeResult(
                container="mp4",
                download_type=core.models.Download.DownloadType.HLS,
                video_url=HLSManifestUrl,
                mime_type="video/mp4",
                extra_headers=youtube_models.HEADER_MAPPING.get(method)
            )

        


        bestAudioAndVideoCandidate = _extractVideoAudioFromFormats(formats)

        if bestAudioAndVideoCandidate:
            return YoutubeResult(
                container="mp4",
                video_url=bestAudioAndVideoCandidate.get("url"),
                download_type=core.models.Download.DownloadType.FILE,
                mime_type=bestAudioAndVideoCandidate.get('mimeType').split(";", 1)[0].strip(),
                extra_headers=youtube_models.HEADER_MAPPING.get(method)

            )
            

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

        
def _extractSeperatedVideoAudioFromFormats(
        formats: list,
        preferred_type: str,
        preferred_file : str
        ):

    bestVideoCandidate = BestCandidate()
    bestAudioCandidate = BestCandidate()
    
    for formatData in formats:
        mime = formatData.get("mimeType")
        if not mime:
            continue

        url = formatData.get("url")
        if not url:
            continue

        codec = _getCodec(mime_type=mime)
        mime = mime.split(";")[0]

        urlType = mime.split("/")[0]
        container = mime.split("/")[1]

        
        if not codec:
            continue


        if urlType == "video" and preferred_type != "audio":
            videoPrio = _getVideoScore(
                width=int(formatData.get("width", -1)),
                height=int(formatData.get("height", -1)),
                fps=int(formatData.get("fps", -1)),
                bitrate=int(formatData.get("bitrate", -1)),
                codec=codec
            )
            if container == preferred_file:
                videoPrio += 1000

            if videoPrio > bestVideoCandidate.prio:
                bestVideoCandidate = BestCandidate(
                    url=url,
                    prio=videoPrio,
                    container=container,
                    codec=codec
                    )

            
        elif urlType == "audio":
            audioPrio = _getAudioScore(
                bitrate=int(formatData.get("bitrate", -1)),
                samplerate=int(formatData.get("audioSampleRate", -1)),
                channels=int(formatData.get("audioChannels", 1)),
                codec=codec
            )
        
            if container == preferred_file:
                audioPrio += 1000

            if audioPrio > bestAudioCandidate.prio:
                bestAudioCandidate = BestCandidate(
                    url=url,
                    prio=audioPrio,
                    container=container,
                    codec=codec
                )
                
            
        else: continue

        if preferred_type == "video":
            if not bestVideoCandidate:
                return None
            if not bestAudioCandidate:
                print("[providers] Youtube._extractseperatedVideoAudioFromFormats: Found Video but didn't find audio")

        if preferred_type == "audio":
            if not bestAudioCandidate:
                return None

    return YoutubeResult(
        video_url=bestVideoCandidate.url if preferred_type != "audio" else bestAudioCandidate.url,
        container=bestVideoCandidate.container if preferred_type != "audio" else bestAudioCandidate.container,
        download_type=core.models.Download.DownloadType.FILE,
        audio_url=bestAudioCandidate.url if preferred_type != "audio" else "",
        mime_type=f"video/{bestVideoCandidate.container}" if preferred_type != "audio" else f"audio/{bestAudioCandidate.container}"
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






def _getVideoScore(
        width: int,
        height: int,
        bitrate: int,
        fps: int,
        codec: str,
        ) -> float:

    pixels = width * height

    resolution_score = pixels / (1920 * 1080) * 100
    bitrate_score = bitrate / 1_000_000 * 10
    fps_score = fps / 60 * 20

    codec_factor = youtube_models.VIDEO_CODEC_FACTOR.get(codec, 1.0)

    return (
        resolution_score
        + bitrate_score * codec_factor
        + fps_score
    )





def _getCodec(mime_type: str) -> str | None:
    if 'codecs="' not in mime_type:
        return None

    codec = mime_type.split('codecs="', 1)[1].split('"', 1)[0]

    if codec.startswith("av01"):
        return "av1"

    if codec.startswith("avc1"):
        return "h264"

    if codec.startswith("vp9"):
        return "vp9"

    if codec.startswith("mp4a"):
        return "aac"

    if codec.startswith("opus"):
        return "opus"

    if codec.startswith("vorbis"):
        return "vorbis"

    return codec






def _getAudioScore(
        bitrate: int,
        samplerate: int,
        channels: int,
        codec: str,
        ) -> float:

    bitrate_score = bitrate / 1000
    samplerate_score = samplerate / 1000 * 0.1
    channel_score = channels * 2

    codec_factor = youtube_models.AUDIO_CODEC_FACTOR.get(codec, 1.0)

    return (
        bitrate_score * codec_factor
        + samplerate_score
        + channel_score
    )