import { SERVER_BASE_ADRESS } from "../general";


export const ServerAdressSearch = SERVER_BASE_ADRESS + "/search"

export type SearchRequest = {
    provider: string;
    search: string;
    top: Number;
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

} as const

export type ProvidersSearch= typeof ProvidersSearch[keyof typeof ProvidersSearch]

export type SearchResult = {
    url: string;
    thumbnail: string;
    title: string;
    provider: ProvidersSearch;
}



