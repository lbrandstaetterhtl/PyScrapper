# Core imports
from ...network.progress import updateDownloadProgress
from ...models import Download

# Own imports

#Python default imports 
from dataclasses import dataclass
import urllib.parse
import asyncio


async def downloadAndYieldUMP(
        session,
        start_url: str,
        extra_headers: dict,
        download_progress: Download.DownloadProgress,
        max_len: int
):
    download_progress.total_bytes = max_len

    nextChunkUrl = start_url


    while True:
        with session.open(url=nextChunkUrl, headers=extra_headers) as response:
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


#This functioins made by AI
async def downloadAndYieldUMPRange(
    session,
    start_url: str,
    extra_headers: dict,
    max_len: int,
    media_start: int = 0,
    media_end: int | None = None,
):
    media_position = 0

    async for chunk in downloadAndYieldUMPSimple(
        session=session,
        start_url=start_url,
        extra_headers=extra_headers,
        max_len=max_len,
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
        max_len: int
):


    nextChunkUrl = start_url


    while True:
        with session.open(url=nextChunkUrl, headers=extra_headers) as response:
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