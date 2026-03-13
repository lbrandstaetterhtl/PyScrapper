
VALIDARCHIVENAMES = [
    "archive",
    "archive.org",
    "www.archive.org",
    "internetarchive"
]

VALIDYOUTUBENAMES = [
    "youtube",
    "youtube.com",
    "www.youtube.com"
]

VALIDSUNONAMES = [
    "suno",
    "suno.com",
    "www.suno.com"
]

SUPPORTEDPROVIDERS = {
    'archive': VALIDARCHIVENAMES,
    'youtube': VALIDYOUTUBENAMES,
    'suno': VALIDSUNONAMES
}

SUPPORTEDARCHIVEFILES = [
    ".mp3",
    ".mp4",
    "mp3",
    "mp4"
]

SUPPORTEDYOUTUBEFILES = [
    ".mp3",
    ".mp4",
    "mp3",
    "mp4"
]

SUPPORTEDSUNOFILES = [
    ".mp3",
    ".mp4",
    "mp3",
    "mp4"
]

SUPPORTEDFILES = {
    "archive" : SUPPORTEDARCHIVEFILES,
    "youtube" : SUPPORTEDYOUTUBEFILES,
    "suno" : SUPPORTEDSUNOFILES
}

PROGRESSDICT = {
            "id": "",
            "status": "queued",
            "downloadProgress": 0,
            "errorMessage": "",
            "totalBytes" : 0,
            "downloadedBytes" : 0,
            "speed" : 0,
            "eta" : 0
        }

SUPPORTEDCOMMANDS = [
    "quit"
]