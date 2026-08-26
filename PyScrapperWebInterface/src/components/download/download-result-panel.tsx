import { useRef ,useEffect, useState } from "react"
import type { DownloadProgress, DownloadResult, StreamResult } from "./models"

import { DownloadResultPanelType } from "./models"
import type { DownloadPanelType } from "./models"

import { getDownloadProgress } from "./api"

import type { Authorization } from "../general"

import Hls from "hls.js"

type DownloadResultPanelProps = {
    history : DownloadResult[]
    auth: Authorization
    updateDownloadHistory: React.Dispatch<React.SetStateAction<DownloadResult[]>>
}

function DownloadResultPanel(
    {
        history,
        auth,
        updateDownloadHistory
    } : DownloadResultPanelProps
)
{
    const [curResultPanel, updateResultPanel] = useState<DownloadPanelType>(DownloadResultPanelType.SHOW_ALL)
    const [curResult, updateResult] = useState<DownloadResult | null>(null)

    async function updateProgress(progressUrl: string) {
        const server_response = await getDownloadProgress(
            progressUrl,
            auth
        )

        if (server_response === undefined || server_response === null) {
            return false
        }

        let allFinished = true

        for (const server_stream of server_response.streams) {
            const id = server_stream.stream_id

            const newProgress: DownloadProgress = {
                status: server_stream.download_progress.status,
                progress: server_stream.download_progress.progress,
                eta: server_stream.download_progress.eta,
                speed: server_stream.download_progress.speed,
                downloaded_bytes: server_stream.download_progress.downloaded_bytes,
                error_message: server_stream.download_progress.error_message
            }

            if (
                newProgress.status !== "complete" && newProgress.status !== "error"
            ) {
                allFinished = false
            }

            updateResult(prev => {
                if (!prev) {
                    return prev
                }

                return {
                    ...prev,
                    streams: prev.streams.map(stream =>
                        stream.task_id === id
                            ? {
                                ...stream,
                                download_progress: newProgress
                            }
                            : stream
                    )
                }
            })
        }

        return allFinished
    }

    useEffect(() => {
        if (!curResult) {
            return
        }

        if (curResultPanel !== DownloadResultPanelType.SHOW_ONE) {
            return
        }

        const alreadyFinished = curResult.streams.every(
            stream =>
                stream.download_progress.status === "complete" ||
                stream.download_progress.status === "error"
        )

        if (alreadyFinished) {
            return
        }

        const progressUrl = curResult.download_progress

        const interval = setInterval(async () => {
            const done = await updateProgress(progressUrl)

            if (done === true) {
                clearInterval(interval)
            }
        }, 1000)

        return () => clearInterval(interval)
    }, [curResult?.task_id, curResultPanel])

    function removeFromHistory(result: DownloadResult)
    {
        updateDownloadHistory(prevHistory => 
            prevHistory.filter(entry => entry !== result))
    }

    function selectResult(result: DownloadResult)
    {
        updateResult(result)
        updateResultPanel(DownloadResultPanelType.SHOW_ONE)
    }

    function startDownload(stream: StreamResult) {
        const link = document.createElement("a")
        link.href = stream.download_url
        link.download = ""

        document.body.appendChild(link)
        link.click()
        link.remove()
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
                            <p>Completed requests will appear here.</p>
                        </div>
                    )}

                    <div className="history-list">
                        {history.map((result, index) => (
                            <article className="history-card" key={`${result.task_id}-${index}`}>
                                <div className="history-number">{String(index + 1).padStart(2, "0")}</div>
                                <div className="history-main">
                                    <span className="field-label">TASK ID</span>
                                    <code>{result.task_id}</code>
                                    <div className="history-meta">
                                        <span>{result.streams.length} stream{result.streams.length === 1 ? "" : "s"}</span>
                                        <span>{result.download_request.provider}</span>
                                        <span>{result.download_request.download_strategie}</span>
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

            {curResultPanel === DownloadResultPanelType.SHOW_ONE && (
                <div className="download-detail">
                    <div className="section-toolbar">
                        <div>
                            <p className="eyebrow">TASK INSPECTOR</p>
                            <h2>Download details</h2>
                            <p className="url-text">{curResult?.download_progress}</p>
                        </div>
                        <button className="button button-secondary" onClick={() => updateResultPanel(DownloadResultPanelType.SHOW_ALL)}>Back</button>
                    </div>

                    <div className="stream-list">
                        {curResult?.streams.map((stream, index) => (
                            <article className="stream-card" key={`${stream.task_id}-${index}`}>
                                <div className="stream-card-header">
                                    <div>
                                        <span className="result-index">STREAM {String(index + 1).padStart(2, "0")}</span>
                                        <h3>{stream.media_type}</h3>
                                    </div>
                                    <span className={`status-badge status-${stream.download_progress.status.toLowerCase()}`}>
                                        <span className="status-dot" /> {stream.download_progress.status}
                                    </span>
                                </div>

                                <div className="stream-url-row">
                                    <span className="field-label">DOWNLOAD URL</span>
                                    <p className="url-text">{stream.download_url}</p>
                                    <button className="button button-primary" onClick={() => startDownload(stream)}>
                                        Start Download
                                    </button>
                                </div>

                                <div className="progress-block">
                                    <div className="progress-heading">
                                        <span>Progress</span>
                                        <strong>{stream.download_progress.progress.toFixed(2)}%</strong>
                                    </div>
                                    <progress
                                        value={stream.download_progress.progress}
                                        max={100}
                                    />
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
                                        <strong>{stream.stream_type}</strong>
                                        <small>type</small>
                                    </div>
                                </div>

                                {stream.download_progress.error_message && (
                                    <div className="error-box">
                                        <strong>Error</strong>
                                        <span>{stream.download_progress.error_message}</span>
                                    </div>
                                )}

                                <div className="media-section">
                                    <div className="media-section-heading">
                                        <div>
                                            <span className="field-label">WATCH URL</span>
                                            <p className="url-text">{stream.watch_url}</p>
                                        </div>
                                        <span className="terminal-badge">{stream.stream_type}</span>
                                    </div>

                                    <MediaPlayer stream={stream} />
                                </div>
                            </article>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

type MediaPlayerProp = {
    stream: StreamResult
}

function MediaPlayer(
    {
        stream
    }: MediaPlayerProp
) {
    const audioRef = useRef<HTMLAudioElement>(null)
    const videoRef = useRef<HTMLVideoElement>(null)
 
    useEffect(() => {
    const media =
    stream.media_type.startsWith("audio/")
        ? audioRef.current
        : videoRef.current

    if (!media)
        return

    media.pause()
    media.removeAttribute("src")
    media.load()

    if (stream.stream_type === "file")
    {
        media.src = stream.watch_url
        return
    }

    if (stream.stream_type === "hls")
    {
        if (Hls.isSupported())
        {
            const hls = new Hls()

            hls.attachMedia(media)

            hls.on(Hls.Events.MEDIA_ATTACHED, () => {
                hls.loadSource(stream.watch_url)
            })

            hls.on(Hls.Events.MANIFEST_PARSED, () => {
                console.log("HLS manifest parsed")
            })

            hls.on(Hls.Events.ERROR, (_, data) => {
                console.error("HLS Error:", data)

                if (data.fatal)
                {
                    console.error(
                        "Fatal HLS error:",
                        data.type,
                        data.details
                    )
                }
            })

            return () => {
                hls.destroy()

                media.pause()
                media.removeAttribute("src")
                media.load()
            }
        }

        if (media.canPlayType("application/vnd.apple.mpegurl"))
        {
            media.src = stream.watch_url
        }
    }

}, [
    stream.watch_url,
    stream.stream_type
])

    if (stream.media_type.startsWith("audio/"))
    {
        return (
            <audio
                ref={audioRef}
                className="media-player audio-player"
                controls
            />
        )
    }
   
    if (stream.media_type.startsWith("video/"))
    {
        return (
            <video
                ref={videoRef}
                className="media-player video-player"
                controls
            />
        )
    }

    return (
        <p className="unsupported-media">
            Unsupported media type: {stream.media_type}
        </p>
    )
}

export default DownloadResultPanel
