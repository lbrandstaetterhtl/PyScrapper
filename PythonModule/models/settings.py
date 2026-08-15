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
    Dailymotion = enum.auto()





import PythonModule.providers as p

providerDownloadMapping: dict = {
    
}

PROVIDER_GETRESULTS_MAPPING: dict = {
    ProviderTypes.Default : p.Default.getMediaInformation,
    ProviderTypes.Soundcloud : p.Soundcloud.getMediaInformation,
    ProviderTypes.Bandcamp : p.Bandcamp.getMediaInformation,
    ProviderTypes.Wcoflix : p.wcoflix.getMediaInformation,
    ProviderTypes.Archive : p.Archive.getMediaInformation,
    ProviderTypes.Suno : p.Suno.getMediaInformation,
    ProviderTypes.Newgrounds : p.Newgrounds.getMediaInformation,
    ProviderTypes.Youtube : p.Youtube.getMediaInformation,

}

PROVIDER_SEARCH_MAPPING: dict = {
    ProviderTypes.Soundcloud : p.Soundcloud.search,
    ProviderTypes.Bandcamp : p.Bandcamp.search,
    ProviderTypes.Archive : p.Archive.search,
    ProviderTypes.Newgrounds : p.Newgrounds.search,
    ProviderTypes.Youtube : p.Youtube.search
}
    



VALIDDAILYMOTIONNAMES = [
    "dailymotion",
    "dailymotion.com",
    "www.dailymotion.com"
]

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
    ProviderTypes.Dailymotion : VALIDDAILYMOTIONNAMES
}


        

SUPPORTEDCOMMANDS = [
    "quit"
]