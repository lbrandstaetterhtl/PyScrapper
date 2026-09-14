import { useEffect, useRef, useState } from "react"
import type { DownloadProgress, DownloadResult, StreamResult } from "./models"
import { DownloadResultPanelType } from "./models"
import type { DownloadPanelType } from "./models"
import { getDownloadProgress } from "./api"
import type { Authorization } from "../general"
import { buildUserHeaders } from "../general"
import Hls from "hls.js"

type DownloadResultPanelProps = {
    history: DownloadResult[]
    auth: Authorization
    updateDownloadHistory: React.Dispatch<React.SetStateAction<DownloadResult[]>>
}

const TERMINAL_PROGRESS_STATES = new Set(["finished", "error", "failed", "complete"])

function DownloadResultPanel({ history, auth, updateDownloadHistory }: DownloadResultPanelProps) {
    const [curResultPanel, updateResultPanel] = useState<DownloadPanelType>(DownloadResultPanelType.SHOW_ALL)
    const [curResult, updateResult] = useState<DownloadResult | null>(null)
    const pollIntervals = useRef<Map<string, number>>(new Map())

    useEffect(() => {
        return () => {
            for (const interval of pollIntervals.current.values()) {
                window.clearInterval(interval)
            }
            pollIntervals.current.clear()
        }
    }, [])

    function isTerminal(status: string) {
        return TERMINAL_PROGRESS_STATES.has(status.toLowerCase())
    }

    function applyProgress(taskId: string, contextId: string, progress: DownloadProgress, active: boolean) {
        updateResult(prev => {
            if (!prev || prev.task_id !== taskId) return prev
            return {
                ...prev,
                streams: prev.streams.map(stream =>
                    stream.context_id === contextId
                        ? { ...stream, download_progress: progress, progress_active: active }
                        : stream
                )
            }
        })

        updateDownloadHistory(prev => prev.map(result =>
            result.task_id !== taskId
                ? result
                : {
                    ...result,
                    streams: result.streams.map(stream =>
                        stream.context_id === contextId
                            ? { ...stream, download_progress: progress, progress_active: active }
                            : stream
                    )
                }
        ))
    }

    async function pollProgress(taskId: string, stream: StreamResult) {
        try {
            const progress = await getDownloadProgress(stream.progress_url, auth)
            const terminal = isTerminal(progress.status)
            applyProgress(taskId, stream.context_id, progress, !terminal)

            if (terminal) {
                const interval = pollIntervals.current.get(stream.context_id)
                if (interval !== undefined) window.clearInterval(interval)
                pollIntervals.current.delete(stream.context_id)
            }
        } catch (err) {
            const failedProgress: DownloadProgress = {
                ...stream.download_progress,
                status: "error",
                error_message: err instanceof Error ? err.message : "Failed to read download progress"
            }
            applyProgress(taskId, stream.context_id, failedProgress, false)

            const interval = pollIntervals.current.get(stream.context_id)
            if (interval !== undefined) window.clearInterval(interval)
            pollIntervals.current.delete(stream.context_id)
        }
    }

    function startProgressPolling(taskId: string, stream: StreamResult) {
        if (!stream.progress_url || pollIntervals.current.has(stream.context_id)) return

        applyProgress(taskId, stream.context_id, stream.download_progress, true)
        void pollProgress(taskId, stream)

        const interval = window.setInterval(() => {
            void pollProgress(taskId, stream)
        }, 1000)

        pollIntervals.current.set(stream.context_id, interval)
    }

    function removeFromHistory(result: DownloadResult) {
        for (const stream of result.streams) {
            const interval = pollIntervals.current.get(stream.context_id)
            if (interval !== undefined) window.clearInterval(interval)
            pollIntervals.current.delete(stream.context_id)
        }
        updateDownloadHistory(prevHistory => prevHistory.filter(entry => entry.task_id !== result.task_id))
    }

    function selectResult(result: DownloadResult) {
        updateResult(result)
        updateResultPanel(DownloadResultPanelType.SHOW_ONE)
    }

    function startDownload(taskId: string, stream: StreamResult) {
        if (!stream.download_url) return

        const link = document.createElement("a")
        link.href = stream.download_url
        link.download = stream.title || ""
        document.body.appendChild(link)
        link.click()
        link.remove()

        // Progress is intentionally queried only after the user actually clicks Download.
        startProgressPolling(taskId, stream)
    }

    return (
        <div className="history-view">
            {curResultPanel === DownloadResultPanelType.SHOW_ALL && (
                <div>
                    <div className="section-toolbar">
                        <div>
                            <p className="eyebrow">TASK ARCHIVE</p>
                            <h2>Results & History</h2>
                            <p className="panel-description">{history.length} request{history.length === 1 ? "" : "s"} stored in the current session.</p>
                        </div>
                        <span className="terminal-badge">jobs[]</span>
                    </div>

                    {history.length === 0 && (
                        <div className="empty-state">
                            <span className="empty-icon">&gt;_</span>
                            <h3>No download history</h3>
                            <p>Resolved requests will appear here.</p>
                        </div>
                    )}

                    <div className="history-list">
                        {history.map((result, index) => (
                            <article className="history-card" key={result.task_id}>
                                <div className="history-number">{String(index + 1).padStart(2, "0")}</div>
                                <div className="history-main">
                                    <span className="field-label">{result.title}</span>
                                    <code>{result.task_id}</code>
                                    <div className="history-meta">
                                        <span>{result.streams.length} resource{result.streams.length === 1 ? "" : "s"}</span>
                                        <span>{result.download_request.provider}</span>
                                        <span>{result.download_request.download_strategie}</span>
                                        {result.download_request.preferred_type && <span>{result.download_request.preferred_type}</span>}
                                        {result.download_request.preferred_file && <span>{result.download_request.preferred_file}</span>}
                                    </div>
                                </div>
                                <div className="history-actions">
                                    <button className="button button-primary" onClick={() => selectResult(result)}>Select</button>
                                    <button className="button button-danger" onClick={() => removeFromHistory(result)}>Delete</button>
                                </div>
                            </article>
                        ))}
                    </div>
                </div>
            )}

            {curResultPanel === DownloadResultPanelType.SHOW_ONE && curResult && (
                <div className="download-detail">
                    <div className="section-toolbar">
                        <div>
                            <p className="eyebrow">TASK INSPECTOR</p>
                            <h2>{curResult.title}</h2>
                            <p className="url-text">{curResult.task_id}</p>
                        </div>
                        <button className="button button-secondary" onClick={() => updateResultPanel(DownloadResultPanelType.SHOW_ALL)}>Back</button>
                    </div>

                    <div className="stream-list">
                        {curResult.streams.map((stream, index) => (
                            <article className="stream-card" key={stream.context_id}>
                                <div className="stream-card-header">
                                    <div>
                                        <span className="result-index">RESOURCE {String(index + 1).padStart(2, "0")}</span>
                                        <h3>{stream.title}</h3>
                                        <p className="url-text">{stream.media_type}</p>
                                    </div>
                                    <span className={`status-badge status-${stream.download_progress.status.toLowerCase()}`}>
                                        <span className="status-dot" /> {stream.download_progress.status}
                                    </span>
                                </div>

                                {stream.download_url && (
                                    <div className="stream-url-row">
                                        <span className="field-label">DOWNLOAD URL</span>
                                        <p className="url-text">{stream.download_url}</p>
                                        <button
                                            className="button button-primary"
                                            onClick={() => startDownload(curResult.task_id, stream)}
                                            disabled={stream.progress_active}
                                        >
                                            {stream.progress_active ? "Downloading..." : "Start Download"}
                                        </button>
                                    </div>
                                )}

                                <div className="progress-block">
                                    <div className="progress-heading">
                                        <span>Progress</span>
                                        <strong>{stream.download_progress.progress.toFixed(2)}%</strong>
                                    </div>
                                    <progress value={stream.download_progress.progress} max={100} />
                                </div>

                                <div className="stats-grid">
                                    <div className="stat-card">
                                        <span>Downloaded</span>
                                        <strong>{stream.download_progress.downloaded_bytes}</strong>
                                        <small>Bytes</small>
                                    </div>
                                    <div className="stat-card">
                                        <span>Speed</span>
                                        <strong>{stream.download_progress.speed.toFixed(2)}</strong>
                                        <small>MiB/s</small>
                                    </div>
                                    <div className="stat-card">
                                        <span>ETA</span>
                                        <strong>{stream.download_progress.eta !== null ? stream.download_progress.eta : "--"}</strong>
                                        <small>{stream.download_progress.eta !== null ? "seconds" : "unknown"}</small>
                                    </div>
                                    <div className="stat-card">
                                        <span>Stream</span>
                                        <strong>{stream.stream_type || "local"}</strong>
                                        <small>{stream.file_extension || "type"}</small>
                                    </div>
                                </div>

                                {stream.download_progress.error_message && (
                                    <div className="error-box">
                                        <strong>Error</strong>
                                        <span>{stream.download_progress.error_message}</span>
                                    </div>
                                )}

                                {stream.watch_url && (
                                    <div className="media-section">
                                        <div className="media-section-heading">
                                            <div>
                                                <span className="field-label">WATCH URL</span>
                                                <p className="url-text">{stream.watch_url}</p>
                                                {stream.stream_type === "file" && stream.watch_audio_url && (
                                                    <p className="url-text">Separate audio: {stream.watch_audio_url}</p>
                                                )}
                                            </div>
                                            <span className="terminal-badge">{stream.stream_type}</span>
                                        </div>
                                        <MediaPlayer stream={stream} auth={auth} />
                                    </div>
                                )}
                            </article>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

type MediaPlayerProp = { stream: StreamResult; auth: Authorization }

function MediaPlayer({ stream, auth }: MediaPlayerProp) {
    const audioRef = useRef<HTMLAudioElement>(null)
    const videoRef = useRef<HTMLVideoElement>(null)
    const separateAudioRef = useRef<HTMLAudioElement>(null)

    // UMP is exposed as application/vnd.yt-ump in the DownloadResponse context,
    // while the current watch endpoint serves it as audio/webm. Treat it as audio
    // so YouTube Music gets an <audio> element instead of a video element.
    const isUmpAudio = stream.media_type.toLowerCase() === "application/vnd.yt-ump"
    const isAudio = isUmpAudio || stream.media_type.startsWith("audio/") || ["mp3", "m4a", "aac", "flac", "wav", "ogg", "opus"].includes(stream.file_extension)
    const isVideo = !isUmpAudio && (stream.media_type.startsWith("video/") || ["mp4", "mkv", "webm", "mov", "m4v", "avi", "wmv", "mpg", "mpeg", "ts"].includes(stream.file_extension))
    const useSeparateFileAudio = stream.stream_type === "file" && isVideo && Boolean(stream.watch_audio_url)

    useEffect(() => {
        const media = isAudio ? audioRef.current : videoRef.current
        if (!media) return

        let objectUrl: string | null = null
        let cancelled = false
        const controller = new AbortController()

        media.pause()
        media.removeAttribute("src")
        media.load()

        if (stream.stream_type === "file") {
            // <audio>/<video> cannot attach X-User-Key/Auth headers to their own
            // network requests. Fetch the protected watch URL ourselves with the
            // user headers and give the media element a local Blob URL instead.
            void (async () => {
                try {
                    const response = await fetch(stream.watch_url, {
                        method: "GET",
                        headers: buildUserHeaders(auth),
                        signal: controller.signal
                    })

                    if (!response.ok) {
                        let detail = `HTTP ${response.status}`
                        try {
                            const body = await response.json()
                            detail = body?.detail ?? body?.message ?? detail
                        } catch {
                            // The watch route normally returns media, not JSON.
                        }
                        throw new Error(detail)
                    }

                    const blob = await response.blob()
                    if (cancelled) return

                    objectUrl = URL.createObjectURL(blob)
                    media.src = objectUrl
                    media.load()
                } catch (error) {
                    if (!controller.signal.aborted) {
                        console.error("File playback failed:", error)
                    }
                }
            })()

            return () => {
                cancelled = true
                controller.abort()
                media.pause()
                media.removeAttribute("src")
                media.load()
                if (objectUrl) URL.revokeObjectURL(objectUrl)
            }
        }

        if (stream.stream_type === "hls") {
            if (Hls.isSupported()) {
                const hls = new Hls({
                    xhrSetup: (xhr) => {
                        if (auth.user_key) {
                            xhr.setRequestHeader("X-User-Key", auth.user_key)
                        }
                        if (auth.identifier) {
                            xhr.setRequestHeader("Auth", auth.identifier)
                        }
                    }
                })
                hls.attachMedia(media)
                hls.on(Hls.Events.MEDIA_ATTACHED, () => hls.loadSource(stream.watch_url))
                hls.on(Hls.Events.ERROR, (_, data) => {
                    if (data.fatal) console.error("Fatal HLS error:", data.type, data.details)
                })

                return () => {
                    hls.destroy()
                    media.pause()
                    media.removeAttribute("src")
                    media.load()
                }
            }

            if (media.canPlayType("application/vnd.apple.mpegurl")) {
                // Native HLS cannot add the custom API headers. This path is kept
                // for platforms where the endpoint does not require those headers.
                media.src = stream.watch_url
            }
        }
    }, [stream.watch_url, stream.stream_type, isAudio, auth.user_key, auth.identifier])

    useEffect(() => {
        if (!useSeparateFileAudio) return

        const video = videoRef.current
        const audio = separateAudioRef.current
        if (!video || !audio) return

        audio.src = stream.watch_audio_url
        audio.preload = "auto"

        const syncHard = () => {
            if (Number.isFinite(video.currentTime)) audio.currentTime = video.currentTime
        }
        const play = () => {
            syncHard()
            audio.playbackRate = video.playbackRate
            void audio.play().catch(err => console.warn("Separate audio playback failed:", err))
        }
        const pause = () => audio.pause()
        const timeUpdate = () => {
            if (Math.abs(audio.currentTime - video.currentTime) > 0.25) syncHard()
        }
        const rateChange = () => { audio.playbackRate = video.playbackRate }
        const volumeChange = () => {
            audio.volume = video.volume
            audio.muted = video.muted
        }

        video.addEventListener("play", play)
        video.addEventListener("pause", pause)
        video.addEventListener("seeking", syncHard)
        video.addEventListener("seeked", syncHard)
        video.addEventListener("timeupdate", timeUpdate)
        video.addEventListener("ratechange", rateChange)
        video.addEventListener("volumechange", volumeChange)
        video.addEventListener("ended", pause)
        volumeChange()

        return () => {
            video.removeEventListener("play", play)
            video.removeEventListener("pause", pause)
            video.removeEventListener("seeking", syncHard)
            video.removeEventListener("seeked", syncHard)
            video.removeEventListener("timeupdate", timeUpdate)
            video.removeEventListener("ratechange", rateChange)
            video.removeEventListener("volumechange", volumeChange)
            video.removeEventListener("ended", pause)
            audio.pause()
            audio.removeAttribute("src")
            audio.load()
        }
    }, [stream.watch_audio_url, useSeparateFileAudio])

    if (isAudio) {
        return <audio ref={audioRef} className="media-player audio-player" controls />
    }

    if (isVideo) {
        return (
            <>
                <video ref={videoRef} className="media-player video-player" controls />
                {useSeparateFileAudio && <audio ref={separateAudioRef} style={{ display: "none" }} />}
            </>
        )
    }

    return <p className="unsupported-media">Unsupported media type: {stream.media_type}</p>
}

export default DownloadResultPanel
