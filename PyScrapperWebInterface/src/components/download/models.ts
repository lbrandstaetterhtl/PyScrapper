
export const ServerAdressDownload = "/api/download/video-audio/"



export const ProvidersDownload = {
    Youtube: "youtube",
    Bandcamp: "bandcamp",
    Newgrounds: "newgrounds",
    Archive: "archive",
    Soundcloud: "soundcloud",
    Default : "default",
    Wcoflix : "wcoflix",
    Suno : "suno",
    Youtube_Music : "youtubemusic"
    
} as const

export type ProviderDownload =
    typeof ProvidersDownload[keyof typeof ProvidersDownload]

export const DownloadStrategie = {
    Stream: "stream",
    Local: "local"
} as const

export type DownloadStrategie = typeof DownloadStrategie[keyof typeof DownloadStrategie]




export type DownloadRequest = {
    provider: ProviderDownload;
    urls: string[];
    filenames: string[];
    download_strategie: DownloadStrategie;
    extra_headers : {}
    download_path: string;
}

export type DownloadProgress = {
    status: string;
    progress: number;
    downloaded_bytes: number;
    speed: number;
    eta: number | null;
    error_message? : string | null;
}

export type StreamResult = {
task_id: string;

download_url: string;

watch_url: string;

stream_type: string;
media_type: string;

download_progress : DownloadProgress

}

export type DownloadResult = {
    task_id: string;
    download_progress: string;
    streams : StreamResult[]
    info: string;

    download_request: DownloadRequest;
}

export type ServerResultDownload = {
    task_id: string;
    download_progress: string;
    streams: StreamResult[]
    info?: string;
    detail?: string;

}




export const DownloadResultPanelType = {
    SHOW_ALL: "ALL",
    SHOW_ONE: "ONE",
} as const

export type DownloadPanelType =
    typeof DownloadResultPanelType[keyof typeof DownloadResultPanelType]



export type DownloadProgressResponse = {
    task_id: string;
    streams: {
        stream_id: string;
        download_progress: DownloadProgress;
    }[];
}