from PythonModule.models.processorModels import ProviderTypes


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
VALIDBANDCAMPNAMES = [
    "bandcamp",
    "band-camp",
    "bandcamp.com",
    "www.bandcamp.cp,"
]

VALIDDEFAULTNAMES = [
    "default",
    "general"
]

VALIDSOUNDCLOUDNAMES = [
    "soundcloud",
    "soundcloud.com",
    "www.soundcloud.com",
    "sound-cloud"
]

SUPPORTEDPROVIDERS = {
    ProviderTypes.Archive: VALIDARCHIVENAMES,
    ProviderTypes.Bandcamp : VALIDBANDCAMPNAMES,
    ProviderTypes.Youtube: VALIDYOUTUBENAMES,
    ProviderTypes.Suno: VALIDSUNONAMES,
    ProviderTypes.Default : VALIDDEFAULTNAMES,
    ProviderTypes.Soundcloud : VALIDSOUNDCLOUDNAMES
}

SUPPORTEDARCHIVEFILES = [
    ".mp3",
    ".mp4",
    "mp3",
    "mp4",
    ".wav",
    "wav",
    ".mkv",
    "mkv"
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
SUPPORTEDBANDCAMPFILES = [
    ".mp3",
    "mp3"
]

SUPPORTEDFILES = {
    "archive" : SUPPORTEDARCHIVEFILES,
    "bandcamp" : SUPPORTEDBANDCAMPFILES,
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
            "eta" : 0,
            "totalSegments" : 0,
            "downloadedSegments" : 0
        }

SUPPORTEDCOMMANDS = [
    "quit"
]