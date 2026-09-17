FFMPEG_FORMAT_MAPPING = {
    # Video / container
    "mp4": "mp4",
    "m4v": "mp4",
    "mkv": "matroska",
    "webm": "webm",
    "mov": "mov",
    "avi": "avi",
    "wmv": "asf",
    "mpg": "mpeg",
    "mpeg": "mpeg",
    "ts": "mpegts",

    # Audio
    "mp3": "mp3",
    "m4a": "mp4",
    "aac": "adts",
    "flac": "flac",
    "wav": "wav",
    "ogg": "ogg",
    "opus": "opus",
}


FFMPEG_OUTPUT_ARGS_MAPPING = {
    # Video / container
    "mp4": [],
    "m4v": [],
    "mkv": [],
    "webm": [],
    "mov": [],
    "avi": [],
    "wmv": [],
    "mpg": [],
    "mpeg": [],
    "ts": [],

    # Audio only
    "mp3": [
        "-vn",
    ],

    "m4a": [
        "-vn",
    ],

    "aac": [
        "-vn",
    ],

    "flac": [
        "-vn",
    ],

    "wav": [
        "-vn",
    ],

    "ogg": [
        "-vn",
    ],

    "opus": [
        "-vn",
    ],
}