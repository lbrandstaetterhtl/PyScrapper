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