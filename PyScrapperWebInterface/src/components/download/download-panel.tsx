import type { Authorization } from "../general"
import { DownloadStrategie, ProvidersDownload, type DownloadRequest, type ProviderDownload } from "./models"
import type { DownloadResult, ServerResultDownload, StreamResult } from "./models"


import { sendDownloadRequest } from "./api"


type DownloadProps = {
    auth: Authorization
    request: DownloadRequest
    updateDownloadRequest: React.Dispatch<React.SetStateAction<DownloadRequest>>
    updateDownloadHistory: React.Dispatch<React.SetStateAction<DownloadResult[]>>
    onFinishedDownload: () => void
}

function DownloadPanel(
    {
    auth,
    request,
    updateDownloadRequest,
    updateDownloadHistory,
    onFinishedDownload
} : DownloadProps
)
{
    async function sendDownload()
    {
        const server_result: ServerResultDownload = await sendDownloadRequest(request, auth)
        if (server_result.detail !== undefined) 
            {
                console.log("An error occured: ", server_result.detail)
                return
            }

        const streams : StreamResult[] = []
        for (const stream of server_result.streams)
        {
            const stream_result: StreamResult = {
                task_id: stream.task_id,
                download_url: stream.download_url,
                watch_url: stream.watch_url,
                stream_type: stream.stream_type,
                media_type : stream.media_type,
                download_progress : {
                    status: "queued",
                    progress: 0,
                    downloaded_bytes: 0,
                    speed: 0,
                    eta: null
                }
            }
            streams.push(stream_result)
        }
        const result: DownloadResult = {
            task_id : server_result.task_id,
            download_progress :"/api" + server_result.download_progress,
            streams : streams,
            download_request : request,
            info: server_result.info ?? ""
        }

        updateDownloadHistory((oldHistory) => [
            ...oldHistory,
            result
        ])

        updateDownloadRequest(prev => ({
            ...prev,
            download_strategie: DownloadStrategie.Stream,
            download_path: "",
            urls: [],
            filenames: [],
            extra_headers: {},
            provider: ProvidersDownload.Youtube_Music

        }))

        onFinishedDownload()
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
                        onChange={(e) =>
                            updateDownloadRequest({
                                ...request,
                                provider: e.target.value as ProviderDownload
                            })
                        }
                    >
                        {Object.entries(ProvidersDownload).map(([key, value]) => (
                            <option key={value} value={value}>
                                {key}
                            </option>
                        ))}
                    </select>
                </label>

                <label className="field-group field-wide">
                    <span className="field-label">Media URL</span>
                    <input
                        type="text"
                        placeholder="https://www.youtube.com/watch?v=a3H7-7g4dbo"
                        value={request.urls[0] ?? ""}
                        onChange={(e) =>
                            updateDownloadRequest({
                                ...request,
                                urls: [e.target.value]
                            })
                        }
                    />
                </label>

                <label className="field-group">
                    <span className="field-label">Filename</span>
                    <input
                        type="text"
                        placeholder="myvideo"
                        value={request.filenames[0] ?? ""}
                        onChange={(e) =>
                            updateDownloadRequest({
                                ...request,
                                filenames: [e.target.value]
                            })
                        }
                    />
                </label>

                <label className="field-group">
                    <span className="field-label">Download Strategy</span>
                    <select
                        value={request.download_strategie}
                        onChange={(e) =>
                            updateDownloadRequest({
                                ...request,
                                download_strategie: e.target.value as DownloadStrategie
                            })
                        }
                    >
                        {Object.entries(DownloadStrategie).map(([key, value]) => (
                            <option key={value} value={value}>
                                {key}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            {request.download_strategie === "local" && (
                <div className="conditional-panel">
                    <div className="conditional-marker">LOCAL</div>
                    <label className="field-group field-wide">
                        <span className="field-label">Download Path</span>
                        <input
                            value={request.download_path} 
                            placeholder="/home/user/Downloads"
                            onChange={(e) =>
                                updateDownloadRequest(
                                    {
                                        ...request,
                                        download_path: e.target.value
                                    }
                                )
                            }/>
                        <span className="field-hint">The file will be written to this server-side directory.</span>
                    </label>
                </div>
            )}

            <div className="panel-actions">
                <button className="button button-primary button-large" onClick={sendDownload}>
                    <span className="button-prompt">$</span> Download
                </button>
            </div>
        </div>
    )
}

export default DownloadPanel
