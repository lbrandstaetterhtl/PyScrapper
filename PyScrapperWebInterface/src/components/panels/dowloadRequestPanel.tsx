import { useState } from "react"
import type { downloadRequest, SearchResult } from "../models/types"
import sendDownloadRequest from "../fetchRequests/downloadRequest"

type Props = {
    result: SearchResult
    onClose: () => void
}

function DownloadRequestPanel(props: Props)
{

    const [filename, setFilename] = useState(props.result.title)
    const [mediatype, setMediatype] = useState("mp3")
    const [outPath, setOutPath] = useState("")

    async function handleDownload()
    {
        const request: downloadRequest = {
            provider: props.result.provider,
            url: props.result.url,
            mediatype: mediatype,
            filename: filename,
            download_path: outPath
        }

        await sendDownloadRequest(request)

        props.onClose()
    }

    return (
        <div style={{border:"1px solid white", padding:"10px"}}>

            <h3>Download Options</h3>

            <p>Mediatype</p>
            <input 
                value={mediatype}
                onChange={(e) => setMediatype(e.target.value)}
            />

            <p>Filename</p>
            <input
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
            />

            <p>OutPath</p>
            <input
                value={outPath}
                onChange={(e)=> setOutPath(e.target.value)}
            />

            <button onClick={handleDownload}>
                Start Download
            </button>

            <button onClick={props.onClose}>
                Cancel
            </button>

        </div>
    )
}

export default DownloadRequestPanel