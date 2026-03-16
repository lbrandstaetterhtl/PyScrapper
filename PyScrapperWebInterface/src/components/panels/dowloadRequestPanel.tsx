import { useState } from "react"
import type { downloadRequest, SearchResult } from "../models/types"
import sendDownloadRequest from "../fetchRequests/downloadRequest"

type Props = {
    result: SearchResult
    onClose: () => void
    onStartDownload: (response: any) => void
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

        const response = await sendDownloadRequest(request)

        props.onStartDownload(response)
    }
    
    return (
        <div style={{border:"1px solid white", padding:"10px"}}>
            <div 
                key={props.result.identifier ?? "Test"}
                style={{
                    border: "4px",
                    borderColor: "pink",
                    padding: "10px",
                    marginBottom: "10px",
                    
                }}
                >
                    <img
                        src={props.result.thumbnail}
                        alt={props.result.title}
                        width={300}
                        height={120}
                    />
                <p>{props.result.title}</p>
            </div>
              


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