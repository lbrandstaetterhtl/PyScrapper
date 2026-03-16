import { useState } from "react"
import type { downloadRequest, SearchResult } from "../models/types"
import  { MEDIATYPES }  from "../models/config"
import sendDownloadRequest from "../fetchRequests/downloadRequest"

import "../../designs/downloadRequestPanel.css"

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
        <div className="downloadRequestPanel">

            <div className="downloadRequestPanel-shell">

                <div className="downloadRequestPanel-header">
                    <p>{(props.result.provider).toUpperCase()} - {props.result.title}</p>
                    <img
                        src={props.result.thumbnail}
                        alt={props.result.title}
                        
                    />


                </div>
                    
                <div className="downloadRequestPanel-downloadOptions">
                    <h3>Download Options</h3>
                <select onChange={function(e) {
                    setMediatype(e.target.value)
                }}
                >

                {MEDIATYPES[props.result.provider].map((mediatype: string, i) => 
                (
                    <option key={mediatype ?? i} value={mediatype}>
                        {mediatype}
                    </option>
                )
                    
                    
                )}

                </select>

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

                </div>
                
            </div>
              


            

            
            <div className="downloadRequestPanel-buttons">
                <button onClick={handleDownload}>
                    Start Download
                </button>

                <button onClick={props.onClose}>
                    Cancel
                </button>

            </div>
            

        </div>
    )
}

export default DownloadRequestPanel