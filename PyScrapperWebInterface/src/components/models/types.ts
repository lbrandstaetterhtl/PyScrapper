import type { Provider } from "./config"

export type SearchPanelPropertys = {
    provider: string;
    search: string;
    top: number;
}






export type downloadRequestResponse = {
    id: string;
    message: string;
}

export type downloadProgressResponse = {
    id: string;
    status: string;
    downloadProgress: number;
    errorMessage: string;
    totalBytes: number;
    downloadedBytes: number;
    speed: number;
    eta: number;
}


export type SearchResult = {
    identifier? : string;
    url : string;
    thumbnail: string;
    title: string;
    provider: Provider;
}

export type downloadRequest = {
    provider: Provider;
    url: string;
    mediatype: string;
    filename: string;
    download_path?: string;
}




