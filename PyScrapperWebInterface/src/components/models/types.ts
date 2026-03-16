export type SearchPanelPropertys = {
    provider: string;
    search: string;
    top: number;
}



export type saveResults = {
    ifResults: (results: SearchResult[]) => void;
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
    provider: string;
}

export type downloadRequest = {
    provider: string;
    url: string;
    mediatype: string;
    filename: string;
    download_path?: string;
}




