export const SERVER_BASE_ADRESS = "http://127.0.0.1:8000"

export type Authorization = {
    key_name : string;
    key_value: string;
}


export const Panel = {
    AUTHORIZATION: "AUTHORIZATION",
    SEARCH: "SEARCH",
    SEARCH_RESULT : "SEARCH_RESULT",
    DOWNLOAD : "DOWNLOAD",
    DOWNLOAD_RESULT : "DOWNLOAD_RESULT"
} as const

export type Panel = typeof Panel[keyof typeof Panel]