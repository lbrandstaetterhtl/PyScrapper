import type { Authorization } from "../general"
import {
    DownloadStrategie,
    PreferredFiles,
    PreferredTypes,
    ProvidersDownload,
    type DownloadRequest,
    type DownloadResult,
    type ProviderDownload,
    type ServerResultDownload,
    type StreamResult
} from "./models"
import { useState } from "react"
import { apiUrl, sendDownloadRequest } from "./api"

type DownloadProps = {
    auth: Authorization
    request: DownloadRequest
    updateDownloadRequest: React.Dispatch<React.SetStateAction<DownloadRequest>>
    updateDownloadHistory: React.Dispatch<React.SetStateAction<DownloadResult[]>>
    onFinishedDownload: () => void
}

function DownloadPanel({
    auth,
    request,
    updateDownloadRequest,
    updateDownloadHistory,
    onFinishedDownload
}: DownloadProps) {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    async function sendDownload() {
        setLoading(true)
        setError(null)

        try {
            const serverResult: ServerResultDownload = await sendDownloadRequest(request, auth)
            const requestTitle = request.filenames[0]?.trim() || request.urls[0] || "Untitled"

            const streams: StreamResult[] = serverResult.resources.map((resource) => ({
                context_id: resource.context.context_id,
                title: resource.context.output.full_filename || requestTitle,
                download_url: apiUrl(resource.download_url),
                watch_url: apiUrl(resource.watch_url),
                watch_audio_url: apiUrl(resource.watch_audio_url),
                progress_url: apiUrl(resource.progress_url),
                stream_type: resource.stream_type,
                media_type: resource.context.media_info.mime_type || "application/octet-stream",
                file_extension: resource.context.media_info.file_extension || "",
                progress_active: false,
                download_progress: {
                    status: "queued",
                    progress: 0,
                    downloaded_bytes: 0,
                    speed: 0,
                    eta: null,
                    error_message: null
                }
            }))

            const result: DownloadResult = {
                task_id: serverResult.task_id,
                title: requestTitle,
                streams,
                download_request: { ...request }
            }

            updateDownloadHistory(oldHistory => [...oldHistory, result])

            updateDownloadRequest(prev => ({
                ...prev,
                download_strategie: DownloadStrategie.Stream,
                download_path: "",
                urls: [],
                filenames: [],
                preferred_type: null,
                preferred_file: null,
                auto_convert: false,
                extra_headers: {},
                provider: ProvidersDownload.Youtube_Music
            }))

            onFinishedDownload()
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown download error")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="panel-card download-panel">
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">DOWNLOAD REQUEST</p>
                    <h2>Create request</h2>
                    <p className="panel-description">Resolve a media URL through a provider and hand it to the current download pipeline.</p>
                </div>
                <span className="terminal-badge">download.request()</span>
            </div>

            <div className="form-grid download-form-grid">
                <label className="field-group">
                    <span className="field-label">Provider</span>
                    <select
                        value={request.provider}
                        onChange={(e) => updateDownloadRequest({ ...request, provider: e.target.value as ProviderDownload })}
                    >
                        {Object.entries(ProvidersDownload).map(([key, value]) => (
                            <option key={value} value={value}>{key}</option>
                        ))}
                    </select>
                </label>

                <label className="field-group field-wide">
                    <span className="field-label">Media URL</span>
                    <input
                        type="text"
                        placeholder="https://www.youtube.com/watch?v=a3H7-7g4dbo"
                        value={request.urls[0] ?? ""}
                        onChange={(e) => updateDownloadRequest({ ...request, urls: [e.target.value] })}
                    />
                </label>

                <label className="field-group">
                    <span className="field-label">Filename / Title</span>
                    <input
                        type="text"
                        placeholder="myvideo"
                        value={request.filenames[0] ?? ""}
                        onChange={(e) => updateDownloadRequest({ ...request, filenames: [e.target.value] })}
                    />
                </label>

                <label className="field-group">
                    <span className="field-label">Download Strategy</span>
                    <select
                        value={request.download_strategie}
                        onChange={(e) => updateDownloadRequest({ ...request, download_strategie: e.target.value as DownloadStrategie })}
                    >
                        {Object.entries(DownloadStrategie).map(([key, value]) => (
                            <option key={value} value={value}>{key}</option>
                        ))}
                    </select>
                </label>

                <label className="field-group">
                    <span className="field-label">Preferred Type</span>
                    <select
                        value={request.preferred_type ?? ""}
                        onChange={(e) => updateDownloadRequest({ ...request, preferred_type: e.target.value || null })}
                    >
                        <option value={PreferredTypes.Auto}>Auto</option>
                        <option value={PreferredTypes.Video}>Video</option>
                        <option value={PreferredTypes.Audio}>Audio</option>
                    </select>
                    <span className="field-hint">Video means normal video media, not video-only.</span>
                </label>

                <label className="field-group">
                    <span className="field-label">Preferred File</span>
                    <select
                        value={request.preferred_file ?? ""}
                        onChange={(e) => {
                            const preferredFile = e.target.value || null
                            updateDownloadRequest({
                                ...request,
                                preferred_file: preferredFile,
                                auto_convert: preferredFile ? request.auto_convert : false
                            })
                        }}
                    >
                        {PreferredFiles.map((extension) => (
                            <option key={extension || "auto"} value={extension}>
                                {extension ? extension.toUpperCase() : "Auto"}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            {request.preferred_file && (
                <div className="conditional-panel auto-convert-panel">
                    <div className="conditional-marker">CONVERT</div>
                    <label className="toggle-field">
                        <input
                            type="checkbox"
                            checked={request.auto_convert}
                            onChange={(e) => updateDownloadRequest({
                                ...request,
                                auto_convert: e.target.checked
                            })}
                        />
                        <span className="toggle-copy">
                            <strong>Auto Convert</strong>
                            <span>Convert the resolved media to the selected preferred file format when needed.</span>
                        </span>
                    </label>
                </div>
            )}

            {request.download_strategie === "local" && (
                <div className="conditional-panel">
                    <div className="conditional-marker">LOCAL</div>
                    <label className="field-group field-wide">
                        <span className="field-label">Download Path</span>
                        <input
                            value={request.download_path}
                            placeholder="/home/user/Downloads"
                            onChange={(e) => updateDownloadRequest({ ...request, download_path: e.target.value })}
                        />
                        <span className="field-hint">The file will be written to this server-side directory.</span>
                    </label>
                </div>
            )}

            {error && (
                <div className="error-box">
                    <strong>Resolve failed</strong>
                    <span>{error}</span>
                </div>
            )}

            <div className="panel-actions">
                <button className="button button-primary button-large" onClick={sendDownload} disabled={loading}>
                    {loading ? <><span className="spinner" />Resolving...</> : <><span className="button-prompt">$</span>Resolve</>}
                </button>
            </div>
        </div>
    )
}

export default DownloadPanel
