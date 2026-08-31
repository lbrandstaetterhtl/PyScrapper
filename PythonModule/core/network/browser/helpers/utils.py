from ....models import Download



def removeByteRangeParams(url: str) -> str:
    import urllib.parse

    parsed = urllib.parse.urlsplit(url)

    params_to_remove = {
        "bytestart",
        "byteend",
        "bytes",
    }

    filtered_query_parts = []

    for part in parsed.query.split("&"):
        if not part:
            continue

        key = part.split("=", 1)[0]
        key = urllib.parse.unquote_plus(key).lower()

        if key in params_to_remove:
            continue

        filtered_query_parts.append(part)

    return urllib.parse.urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        "&".join(filtered_query_parts),
        parsed.fragment,
    ))



def getRequestBody(request):
        try:
            return request.post_data
        except UnicodeDecodeError:
            try:
                return request.post_data_buffer
            except Exception:
                return None
        except Exception:
            return None



def guessDownloadType(
            url: str,
            content_type: str
    ) -> Download.DownloadType:

        searchString = f"{url.lower()} {content_type.lower()}"

        for keyword, downloadType in Download.DOWNLOAD_TYPE_MAPPING.items():
            if keyword in searchString:
                return downloadType

        return Download.DownloadType.UNKNOWN


def isMediaResponse(
        url: str,
        content_type: str,
        resource_type: str
) -> bool:
    lower = url.lower()
    
    if(
        resource_type == "media"

        or content_type.startswith("video/")
        or content_type.startswith("audio/")
        or "application/vnd.apple.mpegurl" in content_type
        or "application/x-mpegurl" in content_type
        or "application/dash+xml" in content_type

        or "getvid" in lower
        or ".m3u8" in lower
        or ".mpd" in lower
        or ".mp3" in lower
        or ".mkv" in lower
        or ".mp4" in lower
        or ".webm" in lower
        or ".flv" in lower
        or "videoplayback" in lower
        or ".m4a" in lower
        or "mime_type=video" in lower
        or "mime_type=audio" in lower
    ):
          return True

    return False