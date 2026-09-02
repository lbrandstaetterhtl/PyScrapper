# Core imports
import re

import re

from ...network.progress import updateDownloadProgress
from ...models import Download

# Own imports
from . import byte

#Python default imports 
from dataclasses import dataclass
import urllib.parse
import asyncio
import urllib.request


async def downloadAndYieldUMP(
        session,
        start_url: str,
        extra_headers: dict,
        download_progress: Download.DownloadProgress,
        max_len: int,
        post_body: bytes | None = None
):
    download_progress.total_bytes = max_len

    nextChunkUrl = start_url

    


    while True:
        req = urllib.request.Request(
                url=nextChunkUrl,
                headers=extra_headers,
                data=post_body,
            )
        
        with session.open(request=req) as response:
            print(f"[CORE] UMP: opened url {nextChunkUrl}")
            data = await asyncio.to_thread(
                response.read
            )

            parts = _parseUMP(data)

            media_data = _extractMediaData(parts)
            updateDownloadProgress(
                download_progress=download_progress,downloaded_bytes=len(media_data), caller="[CORE] UMP.downloadAndYieldUMP"
            )
            yield media_data

            size = _getSize(parts)

            if size is None:
                print("[CORE] UMP: No media part in response, assuming end of stream")
                break

            parsed = urllib.parse.urlparse(nextChunkUrl)
            query = urllib.parse.parse_qs(parsed.query)


            current_end = int(
            query["range"][0].split("-", 1)[1]
        )

            next_start = current_end + 1
            next_end = min(
                next_start + size - 1,
                max_len - 1
            )

       
            if next_start >= max_len:
                break

            query["range"] = [f"{next_start}-{next_end}"]
            
        
            new_query = urllib.parse.urlencode(query, doseq=True)

            nextChunkUrl = urllib.parse.urlunparse(
                parsed._replace(query=new_query)
            )


#This functions made by AI
async def downloadAndYieldUMPRange(
    session,
    start_url: str,
    extra_headers: dict,
    max_len: int,
    media_start: int = 0,
    media_end: int | None = None,
    post_body: bytes | None = None
):
    media_position = 0

    async for chunk in downloadAndYieldUMPSimple(
        session=session,
        start_url=start_url,
        extra_headers=extra_headers,
        max_len=max_len,
        post_body=post_body
    ):
        chunk_start = media_position
        chunk_end = media_position + len(chunk)

        media_position = chunk_end

        # kompletter Chunk liegt vor dem gewünschten Bereich
        if chunk_end <= media_start:
            continue

        # Start liegt innerhalb dieses Chunks
        offset = max(0, media_start - chunk_start)

        data = chunk[offset:]

        if media_end is not None:
            remaining = media_end - max(chunk_start, media_start) + 1

            if remaining <= 0:
                break

            if len(data) > remaining:
                data = data[:remaining]

        if data:
            yield data

        if media_end is not None and media_position > media_end:
            break


async def downloadAndYieldSABRSimple(
    session,
    start_url: str,
    extra_headers: dict,
    post_body: bytes,
    download_progress,
):
    req = urllib.request.Request(
        url=start_url,
        headers=extra_headers,
        data=post_body,
        method="POST",
    )

    with session.open(request=req) as response:
        data = await asyncio.to_thread(response.read)

    parts = _parseUMP(data)

    chunks = extractUMPChunks(parts)

    # erstmal nur debug / später gezielte Stream-Auswahl
    for chunk_id, chunk in chunks.items():
        print(
            "[SABR]",
            chunk_id,
            len(chunk),
            chunk[:16].hex(" ")
        )

            
async def downloadAndYieldUMPSimple(
        session,
        start_url: str,
        extra_headers: dict,
        max_len: int,
        post_body: bytes | None = None
):
    import urllib.request


    nextChunkUrl = start_url

    


    while True:
        req = urllib.request.Request(
                url=nextChunkUrl,
                headers=extra_headers,
                data=post_body,
                method="POST"
            )
        with session.open(request=req) as response:
            print(f"[CORE] UMP: opened url {nextChunkUrl}")
            data = await asyncio.to_thread(
                response.read
            )

            parts = _parseUMP(data)

            media_data = _extractMediaData(parts)
            yield media_data

            size = _getSize(parts)


            if size is None:
                print("[CORE] UMP: No media part in response, assuming end of stream")
                break

            parsed = urllib.parse.urlparse(nextChunkUrl)
            query = urllib.parse.parse_qs(parsed.query)


            current_end = int(
            query["range"][0].split("-", 1)[1]
        )

            next_start = current_end + 1
            next_end = min(
                next_start + size - 1,
                max_len - 1
            )

       
            if next_start >= max_len:
                break

            query["range"] = [f"{next_start}-{next_end}"]
            
        
            new_query = urllib.parse.urlencode(query, doseq=True)

            nextChunkUrl = urllib.parse.urlunparse(
                parsed._replace(query=new_query)
            )
            


def downloadToFileUMP(
    out_file: str,
    session,
    start_url: str,
    extra_headers: dict,
    download_progress: Download.DownloadProgress,
    max_len: int
):
    nextChunkUrl = start_url

    download_progress.total_bytes = max_len

    with open(out_file, "wb") as f:
        while True:
            with session.open(url=nextChunkUrl, headers=extra_headers) as response:
                print(f"[CORE] UMP: opened url {nextChunkUrl}")
                data = response.read()

            parts = _parseUMP(data)

            media_data = _extractMediaData(parts)
            f.write(media_data)

            updateDownloadProgress(
                download_progress=download_progress,downloaded_bytes=len(media_data), caller="[CORE] UMP.downloadToFileUMP"
            )
            size: int = _getSize(parts)
            if size is None:
                print("[CORE] UMP: No media part in response, assuming end of stream")
                break
            print(f"[CORE] UMP: size of file: {size}")

            parsed = urllib.parse.urlparse(nextChunkUrl)
            query = urllib.parse.parse_qs(parsed.query)



            current_end = int(
                query["range"][0].split("-", 1)[1]
            )

            next_start = current_end + 1
            next_end = min(
                next_start + size - 1,
                max_len - 1
            )

            if next_start >= max_len:
                break

            query["range"] = [f"{next_start}-{next_end}"]
            
        
            new_query = urllib.parse.urlencode(query, doseq=True)

            nextChunkUrl = urllib.parse.urlunparse(
                parsed._replace(query=new_query)
            )

            




@dataclass
class UMPChunk:
    start : int
    content_length : int
    data: bytes
    itag: int | None = None
    lmt: int | None = None


@dataclass
class UMPPart:
    part_type: int
    payload: bytes



def _readUMPVarInt(data: bytes, pos: int) -> tuple[int, int]:
    if pos >= len(data):
        raise ValueError("Unexpected EOF while reading UMP varint")

    first = data[pos]

    if first < 0x80:
        byte_length = 1
    elif first < 0xC0:
        byte_length = 2
    elif first < 0xE0:
        byte_length = 3
    elif first < 0xF0:
        byte_length = 4
    else:
        byte_length = 5

    if pos + byte_length > len(data):
        raise ValueError("Unexpected EOF inside UMP varint")

    if byte_length == 1:
        value = first

    elif byte_length == 2:
        b1 = data[pos]
        b2 = data[pos + 1]

        value = (b1 & 0x3F) + 64 * b2

    elif byte_length == 3:
        b1 = data[pos]
        b2 = data[pos + 1]
        b3 = data[pos + 2]

        value = (
            (b1 & 0x1F)
            + 32 * (
                b2
                + 256 * b3
            )
        )

    elif byte_length == 4:
        b1 = data[pos]
        b2 = data[pos + 1]
        b3 = data[pos + 2]
        b4 = data[pos + 3]

        value = (
            (b1 & 0x0F)
            + 16 * (
                b2
                + 256 * (
                    b3
                    + 256 * b4
                )
            )
        )

    else:
        # 0xF0+ marks a 5-byte integer.
        # Remaining 4 bytes contain the uint32 little-endian.
        value = int.from_bytes(
            data[pos + 1:pos + 5],
            byteorder="little",
            signed=False
        )

    return value, pos + byte_length

def extractUMPChunks(parts):
    chunks: dict[int, bytearray] = {}

    for part in parts:
        if part.part_type != 0x15:
            continue

        if not part.payload:
            continue

        chunk_id = part.payload[0]
        media_data = part.payload[1:]

        if chunk_id not in chunks:
            chunks[chunk_id] = bytearray()

        chunks[chunk_id].extend(media_data)

    return {
        chunk_id: bytes(data)
        for chunk_id, data in chunks.items()
    }

def inspectUMP(data: bytes):
    import re
    parts = _parseUMP(data)

    for i, part in enumerate(parts):
        payload = part.payload

        print(
            f"[{i:02}] "
            f"type={part.part_type:#04x} "
            f"size={len(payload):6}"
        )

        # Stream-/Metadatenparts: hier sind Strings interessant
        if part.part_type == 0x2A:
            strings = re.findall(rb"[\x20-\x7e]{4,}", payload)

            for value in strings:
                print("     TEXT:", value.decode("ascii", errors="replace"))

        # Media data
        elif part.part_type == 0x15:
            if not payload:
                continue

            stream_id = payload[0]
            media = payload[1:]

            print(f"     id={stream_id}")
            print(f"     first={media[:16].hex(' ')}")

            if media.startswith(b"\x1a\x45\xdf\xa3"):
                print("     >>> WEBM HEADER")

            elif b"ftyp" in media[:64]:
                print("     >>> MP4 HEADER")

            elif b"moof" in media[:64]:
                print("     >>> MP4 FRAGMENT")

            elif b"mdat" in media[:64]:
                print("     >>> MP4 MEDIA DATA")

        elif part.part_type == 0x16:
            print(
                "     id=",
                payload[0] if payload else None
            )

def _parseUMP(data: bytes) -> list[UMPPart]:
    parts = []
    pos = 0

    while pos < len(data):

        part_type, pos = _readUMPVarInt(data, pos)
        part_size, pos = _readUMPVarInt(data, pos)

        payload_start = pos
        payload_end = pos + part_size

        if payload_end > len(data):
            raise ValueError(
                f"UMP part exceeds response: "
                f"type={part_type:#x}, "
                f"size={part_size}, "
                f"pos={pos}, "
                f"remaining={len(data) - pos}"
            )

        payload = data[payload_start:payload_end]

        parts.append(
            UMPPart(
                part_type=part_type,
                payload=payload
            )
        )

        pos = payload_end

    return parts


def _getSize(parts:list[UMPPart]) -> int:

    for i, part in enumerate(parts):
        print(
            f"[{i}] "
            f"type={part.part_type} "
            f"hex={part.part_type:#x} "
            f"size={len(part.payload)} "
            f"start={part.payload[:16].hex(' ')}"
        )
        
        if part.part_type != 0x15:
            continue

        if len(part.payload) < 1:
            continue

        return len(part.payload) + 1




def _extractMediaData(parts: list[UMPPart]) -> bytes:
    media_data = bytearray()

    for part in parts:
        if part.part_type != 0x15:
            continue

        if len(part.payload) <= 1:
            continue

        media_data.extend(part.payload[1:])

    return bytes(media_data)




def detectMediaChunk(data: bytes) -> str | None:
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "audio"

    if data.startswith(b"\x1f\x43\xb6\x75"):
        return "audio"

    if b"ftyp" in data[:64]:
        return "video"

    if b"moof" in data[:64]:
        return "video"

    return None

def _parse_proto(data: bytes):
    fields = []
    pos = 0

    while pos < len(data):
        key, pos = byte._read_varint(data, pos)

        number = key >> 3
        wire = key & 7

        if wire == 0:
            value, pos = byte._read_varint(data, pos)
            fields.append([number, wire, value])

        elif wire == 2:
            size, pos = byte._read_varint(data, pos)
            value = data[pos:pos + size]
            pos += size

            fields.append([number, wire, value])

        elif wire == 1:
            value = data[pos:pos + 8]
            pos += 8
            fields.append([number, wire, value])

        elif wire == 5:
            value = data[pos:pos + 4]
            pos += 4
            fields.append([number, wire, value])

        else:
            raise ValueError(f"Unsupported protobuf wire type {wire}")

    return fields


def _encode_proto(fields):
    out = bytearray()

    for number, wire, value in fields:
        out += byte._write_varint((number << 3) | wire)

        if wire == 0:
            out += byte._write_varint(value)

        elif wire == 2:
            out += byte._write_varint(len(value))
            out += value

        elif wire in (1, 5):
            out += value

    return bytes(out)


def patch_sabr_request(
    body: bytes,
    *,
    playback_ms: int | None = None,

    # Vermuteter Buffer-/Segment-State
    ranges: dict[int, dict] | None = None,
) -> bytes:
    """
    Experimental SABR request patcher.

    ranges example:

    {
        251: {
            "start_ms": 0,
            "duration_ms": 30000,
            "first_segment": 1,
            "last_segment": 3,
        },

        136: {
            "start_ms": 18000,
            "duration_ms": 24000,
            "first_segment": 4,
            "last_segment": 7,
        },
    }
    """

    fields = _parse_proto(body)

    for field in fields:

        # ----------------------------------------------------
        # TOP LEVEL FIELD 1
        # Playback / ABR state
        # ----------------------------------------------------
        if field[0] == 1 and field[1] == 2:
            state = _parse_proto(field[2])

            if playback_ms is not None:
                for sub in state:

                    # experimentell beobachtet:
                    # field 29 ~ playback position
                    if sub[0] == 29 and sub[1] == 0:
                        print(
                            "[SABR PATCH] playback field 29:",
                            sub[2],
                            "->",
                            playback_ms
                        )

                        sub[2] = playback_ms

                    # field 36 folgt field 29 mit +20
                    elif sub[0] == 36 and sub[1] == 0:
                        print(
                            "[SABR PATCH] playback field 36:",
                            sub[2],
                            "->",
                            playback_ms + 20
                        )

                        sub[2] = playback_ms + 20

            field[2] = _encode_proto(state)

        # ----------------------------------------------------
        # TOP LEVEL FIELD 3
        # vermutlich bereits vorhandene Media-/Buffer-Ranges
        # ----------------------------------------------------
        elif (
            field[0] == 3
            and field[1] == 2
            and ranges is not None
        ):
            try:
                range_state = _parse_proto(field[2])
            except Exception:
                continue

            itag = None

            # Inner field 1 scheint wiederum die
            # Representation-Beschreibung zu enthalten.
            for sub in range_state:
                if sub[0] != 1 or sub[1] != 2:
                    continue

                try:
                    representation = _parse_proto(sub[2])
                except Exception:
                    continue

                for rep_field in representation:

                    # representation.field1 = itag
                    if rep_field[0] == 1 and rep_field[1] == 0:
                        itag = rep_field[2]
                        break

                if itag is not None:
                    break

            if itag is None:
                continue

            if itag not in ranges:
                continue

            patch = ranges[itag]

            print(
                f"[SABR PATCH] Found range for itag {itag}"
            )

            for sub in range_state:

                if sub[1] != 0:
                    continue

                # field 2:
                # observed start of buffered range
                if (
                    sub[0] == 2
                    and "start_ms" in patch
                ):
                    print(
                        f"    start_ms: {sub[2]} "
                        f"-> {patch['start_ms']}"
                    )

                    sub[2] = patch["start_ms"]

                # field 3:
                # observed duration / covered range
                elif (
                    sub[0] == 3
                    and "duration_ms" in patch
                ):
                    print(
                        f"    duration_ms: {sub[2]} "
                        f"-> {patch['duration_ms']}"
                    )

                    sub[2] = patch["duration_ms"]

                # field 4:
                # observed first segment-ish value
                elif (
                    sub[0] == 4
                    and "first_segment" in patch
                ):
                    print(
                        f"    first_segment: {sub[2]} "
                        f"-> {patch['first_segment']}"
                    )

                    sub[2] = patch["first_segment"]

                # field 5:
                # observed last segment-ish value
                elif (
                    sub[0] == 5
                    and "last_segment" in patch
                ):
                    print(
                        f"    last_segment: {sub[2]} "
                        f"-> {patch['last_segment']}"
                    )

                    sub[2] = patch["last_segment"]

            field[2] = _encode_proto(range_state)

    return _encode_proto(fields)


def downloadToFileSABR(
    out_file: str,
    session,
    start_url: str,
    extra_headers: dict,
    post_body: bytes,
    download_progress: Download.DownloadProgress,
):
    import urllib.request
    import urllib.parse

    req = urllib.request.Request(
        url=start_url,
        headers=extra_headers,
        data=post_body,
        method="POST",
    )

    positions = [
        15000,
        30000,
        45000,
        60000,
        75000,
        90000,
        115000
    ]
    with open(f"videoplayback1", "wb") as f:
        with session.open(request=req) as response:
            data = response.read()
            f.write(data)
    index = 1
    for pos in positions:
        index += 1
        

        body2 = patch_sabr_request(
            post_body,
            playback_ms=15000,

            ranges={
                251: {
                    "start_ms": 0,
                    "duration_ms": 20000,
                    "first_segment": 1,
                    "last_segment": 2,
                },

                134: {
                    "start_ms": 0,
                    "duration_ms": 18000,
                    "first_segment": 1,
                    "last_segment": 3,
                },
            }
        )

        req2 = urllib.request.Request(
            url=start_url,
            headers=extra_headers,
            data=body2,
            method="POST"
        )

        with open(f"videoplayback{index}", "wb") as f:
            with session.open(request=req2) as response:
                data = response.read()
                f.write(data)

        

STREAM_PROTECTION_STATUS_PART = 58


def getStreamProtectionStatus(
    data: bytes,
) -> int | None:
    parts = _parseUMP(data)

    for part in parts:
        if part.part_type != STREAM_PROTECTION_STATUS_PART:
            continue

        fields = _parse_proto(part.payload)

        for fieldNumber, wireType, value in fields:
            if fieldNumber == 1 and wireType == 0:
                return int(value)

    return None

import re

_POT_PATTERN = re.compile(
    r"([?&]pot=)[^&]*"
)


def replacePoToken(
    url: str,
    token: str,
) -> str:
    encodedToken = urllib.parse.quote(
        token,
        safe="-_",
    )

    replacement = rf"\g<1>{encodedToken}"

    result, replacementCount = _POT_PATTERN.subn(
        replacement,
        url,
        count=1,
    )

    if replacementCount == 1:
        return result

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}pot={encodedToken}"