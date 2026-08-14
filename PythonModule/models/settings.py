import enum

import PythonModule.core as core



class ProviderTypes(enum.Enum):
    Default = enum.auto()
    ERROR = enum.auto()
    Youtube = enum.auto()
    Bandcamp = enum.auto()
    Archive = enum.auto()
    Suno = enum.auto()
    Soundcloud = enum.auto()
    Wcoflix = enum.auto()
    Aniworld = enum.auto()
    Newgrounds = enum.auto()





import PythonModule.providers as p

providerDownloadMapping: dict = {
    
}

PROVIDER_GETRESULTS_MAPPING: dict = {
    ProviderTypes.Default : p.Default.getMediaInformation,
    ProviderTypes.Soundcloud : p.Soundcloud.getMediaInformation,
    ProviderTypes.Bandcamp : p.Bandcamp.getMediaInformation
}

PROVIDER_SEARCH_MAPPING: dict = {
    ProviderTypes.Soundcloud : p.Soundcloud.search,
    ProviderTypes.Bandcamp : p.Bandcamp.search
}
    





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

VALIDWCOFLIXNAMES = [
    "wcoflix",
    "wcoflix.tv",
    "www.wcoflix.tv"
]

VALIDNEWGROUNDSNAMES = [
    "newgrounds",
    "newgrounds.com",
    "www.newgrounds.com"
]

SUPPORTEDPROVIDERS = {
    ProviderTypes.Archive: VALIDARCHIVENAMES,
    ProviderTypes.Bandcamp : VALIDBANDCAMPNAMES,
    ProviderTypes.Youtube: VALIDYOUTUBENAMES,
    ProviderTypes.Suno: VALIDSUNONAMES,
    ProviderTypes.Default : VALIDDEFAULTNAMES,
    ProviderTypes.Soundcloud : VALIDSOUNDCLOUDNAMES,
    ProviderTypes.Wcoflix : VALIDWCOFLIXNAMES,
    ProviderTypes.Newgrounds : VALIDNEWGROUNDSNAMES,
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
            "downloadedSegments" : 0,
            "convertProgress" : core.models.Convert.CONVERT_PROGRESS_DICT.copy(),
        }

SUPPORTEDCOMMANDS = [
    "quit"
]