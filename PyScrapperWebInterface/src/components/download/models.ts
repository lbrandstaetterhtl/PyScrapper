export const ServerAdressDownload = "/api/download/video-audio"

export const ProvidersDownload = {
    Youtube: "youtube",
    Bandcamp: "bandcamp",
    Newgrounds: "newgrounds",
    Archive: "archive",
    Soundcloud: "soundcloud",
    Default: "default",
    Wcoflix: "wcoflix",
    Suno: "suno",
    Youtube_Music: "youtubemusic"
} as const

export type ProviderDownload = typeof ProvidersDownload[keyof typeof ProvidersDownload]

export const DownloadStrategie = {
    Stream: "stream",
    Local: "local"
} as const

export type DownloadStrategie = typeof DownloadStrategie[keyof typeof DownloadStrategie]

export const PreferredTypes = {
    Auto: "",
    Video: "video",
    Audio: "audio"
} as const

export const PreferredFiles = [
    "", "mp4", "mkv", "webm", "mov", "m4v", "avi", "wmv", "mpg", "mpeg", "ts",
    "mp3", "m4a", "aac", "flac", "wav", "ogg", "opus"
] as const

export type DownloadRequest = {
    provider: ProviderDownload;
    urls: string[];
    filenames: string[];
    download_strategie: DownloadStrategie;
    preferred_type: string | null;
    preferred_file: string | null;
    auto_convert: boolean;
    extra_headers: Record<string, string>;
    download_path: string;
}

export type DownloadProgress = {
    status: string;
    progress: number;
    downloaded_bytes: number;
    speed: number;
    eta: number | null;
    error_message?: string | null;
}

export type ResourceContext = {
    context_id: string;
    media_info: {
        mime_type: string | null;
        file_extension: string | null;
        total_size: number | null;
    };
    output: {
        full_filename: string | null;
        download_path: string | null;
        out_file?: string | null;
    };
}

export type ServerResource = {
    context: ResourceContext;
    progress_url: string;
    download_url: string;
    watch_url: string;
    stream_type: string;
    watch_audio_url: string;
}

export type ServerResultDownload = {
    task_id: string;
    resources: ServerResource[];
    detail?: string;
}

export type StreamResult = {
    context_id: string;
    title: string;
    download_url: string;
    watch_url: string;
    watch_audio_url: string;
    progress_url: string;
    stream_type: string;
    media_type: string;
    file_extension: string;
    download_progress: DownloadProgress;
    progress_active: boolean;
}

export type DownloadResult = {
    task_id: string;
    title: string;
    streams: StreamResult[];
    download_request: DownloadRequest;
}

export const DownloadResultPanelType = {
    SHOW_ALL: "ALL",
    SHOW_ONE: "ONE",
} as const

export type DownloadPanelType = typeof DownloadResultPanelType[keyof typeof DownloadResultPanelType]
