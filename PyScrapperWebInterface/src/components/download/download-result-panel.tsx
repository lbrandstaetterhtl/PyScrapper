import { useEffect, useRef, useState } from "react"
import type { DownloadProgress, DownloadResult, StreamResult } from "./models"
import { DownloadResultPanelType } from "./models"
import type { DownloadPanelType } from "./models"
import { getDownloadProgress } from "./api"
import type { Authorization } from "../general"
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

        media.pause()
        media.removeAttribute("src")
        media.load()

        if (stream.stream_type === "file") {
            // Do NOT fetch the whole media into a Blob. A fetch() without a Range
            // header makes the server send the complete file first, so large video
            // appears to "load forever" before playback can start. Giving the URL
            // directly to <video>/<audio> lets the browser issue its own byte-range
            // requests (206) and start playback while the file is still loading.
            media.src = stream.watch_url
            media.preload = "metadata"
            media.load()

            return () => {
                media.pause()
                media.removeAttribute("src")
                media.load()
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

        // The video element is the master clock. The separate audio element only
        // follows it. Small clock drift is corrected gently with playbackRate;
        // hard seeks are reserved for real seeks / large desyncs because assigning
        // currentTime repeatedly can trigger new Range requests and audible gaps.
        const HARD_SYNC_THRESHOLD = 0.9
        const SOFT_SYNC_THRESHOLD = 0.06
        const MAX_RATE_CORRECTION = 0.04
        const SYNC_INTERVAL_MS = 200

        let disposed = false
        let videoIsBuffering = false
        let videoIsSeeking = false

        audio.preload = "auto"
        audio.src = stream.watch_audio_url
        audio.load()

        // Keep pitch stable while playbackRate is nudged for A/V clock drift.
        audio.preservesPitch = true

        const copyVolume = () => {
            audio.volume = video.volume
            audio.muted = video.muted
        }

        const resetRate = () => {
            audio.playbackRate = video.playbackRate
        }

        const canSeekAudio = () => (
            audio.readyState >= audio.HAVE_METADATA &&
            Number.isFinite(video.currentTime)
        )

        const hardSync = () => {
            if (!canSeekAudio()) return

            const target = video.currentTime
            if (Math.abs(audio.currentTime - target) < 0.015) return

            try {
                audio.currentTime = target
            } catch (error) {
                console.warn("Could not seek separate audio for A/V sync:", error)
            }
        }

        const shouldAudioBePlaying = () => (
            !disposed &&
            !video.paused &&
            !video.ended &&
            !videoIsBuffering &&
            !videoIsSeeking &&
            video.readyState >= video.HAVE_FUTURE_DATA
        )

        const startAudio = async (forceSync = false) => {
            if (disposed || !shouldAudioBePlaying()) return

            if (forceSync || Math.abs(audio.currentTime - video.currentTime) > HARD_SYNC_THRESHOLD) {
                hardSync()
            }

            resetRate()

            try {
                await audio.play()
            } catch (error) {
                // play() can briefly reject while metadata/buffer is still arriving.
                // loadeddata/canplay/playing will retry without spamming the player.
                if (!disposed && shouldAudioBePlaying()) {
                    console.debug("Separate audio is not ready yet:", error)
                }
            }
        }

        const pauseAudio = () => {
            audio.pause()
            resetRate()
        }

        const onVideoPlay = () => {
            videoIsBuffering = video.readyState < video.HAVE_FUTURE_DATA
            void startAudio(true)
        }

        const onVideoPause = () => {
            // A normal user pause and an ended video should stop the slave immediately.
            pauseAudio()
        }

        const onVideoWaiting = () => {
            videoIsBuffering = true
            pauseAudio()
        }

        const onVideoPlaying = () => {
            videoIsBuffering = false
            void startAudio(true)
        }

        const onVideoSeeking = () => {
            videoIsSeeking = true
            pauseAudio()
        }

        const onVideoSeeked = () => {
            videoIsSeeking = false
            hardSync()
            void startAudio(false)
        }

        const onVideoRateChange = () => {
            resetRate()
        }

        const onAudioMetadata = () => {
            hardSync()
            void startAudio(false)
        }

        const onAudioCanPlay = () => {
            void startAudio(false)
        }

        const correctDrift = () => {
            if (!shouldAudioBePlaying() || audio.paused || audio.seeking || video.seeking) {
                return
            }

            const drift = audio.currentTime - video.currentTime
            const absDrift = Math.abs(drift)

            if (!Number.isFinite(drift)) return

            if (absDrift > HARD_SYNC_THRESHOLD) {
                // Something genuinely got out of sync (e.g. a delayed start).
                // One seek is cheaper and cleaner than trying to catch up for seconds.
                hardSync()
                resetRate()
                return
            }

            if (absDrift <= SOFT_SYNC_THRESHOLD) {
                resetRate()
                return
            }

            // Audio ahead -> slightly slower. Audio behind -> slightly faster.
            // Scale with the error but cap the correction so it stays inaudible.
            const correction = Math.max(
                -MAX_RATE_CORRECTION,
                Math.min(MAX_RATE_CORRECTION, drift * 0.08)
            )
            audio.playbackRate = video.playbackRate * (1 - correction)
        }

        video.addEventListener("play", onVideoPlay)
        video.addEventListener("pause", onVideoPause)
        video.addEventListener("waiting", onVideoWaiting)
        video.addEventListener("stalled", onVideoWaiting)
        video.addEventListener("playing", onVideoPlaying)
        video.addEventListener("seeking", onVideoSeeking)
        video.addEventListener("seeked", onVideoSeeked)
        video.addEventListener("ratechange", onVideoRateChange)
        video.addEventListener("volumechange", copyVolume)
        video.addEventListener("ended", pauseAudio)

        audio.addEventListener("loadedmetadata", onAudioMetadata)
        audio.addEventListener("canplay", onAudioCanPlay)

        const syncTimer = window.setInterval(correctDrift, SYNC_INTERVAL_MS)

        copyVolume()
        resetRate()

        return () => {
            disposed = true
            window.clearInterval(syncTimer)

            video.removeEventListener("play", onVideoPlay)
            video.removeEventListener("pause", onVideoPause)
            video.removeEventListener("waiting", onVideoWaiting)
            video.removeEventListener("stalled", onVideoWaiting)
            video.removeEventListener("playing", onVideoPlaying)
            video.removeEventListener("seeking", onVideoSeeking)
            video.removeEventListener("seeked", onVideoSeeked)
            video.removeEventListener("ratechange", onVideoRateChange)
            video.removeEventListener("volumechange", copyVolume)
            video.removeEventListener("ended", pauseAudio)

            audio.removeEventListener("loadedmetadata", onAudioMetadata)
            audio.removeEventListener("canplay", onAudioCanPlay)

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
