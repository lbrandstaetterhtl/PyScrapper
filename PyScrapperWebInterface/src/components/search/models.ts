


export const ServerAdressSearch = "/api/search"

export type SearchRequest = {
    provider: string;
    search: string;
    top: number;
    filters: {
        tags: string[]
    }
}



export const ProvidersSearch = {
    Youtube : "youtube",
    Bandcamp : "bandcamp",
    Newgrounds : "newgrounds",
    Archive : "archive",
    Soundcloud : "soundcloud",
    Suno : "suno",
    Youtube_Music : "youtubemusic"

} as const

export type ProvidersSearch= typeof ProvidersSearch[keyof typeof ProvidersSearch]

export type SearchResult = {
    url: string;
    thumbnail: string;
    title: string;
    provider: ProvidersSearch;
}



