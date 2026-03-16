import { useState, useEffect } from "react"
import type { downloadRequestResponse, downloadProgressResponse } from "../models/types"
import sendProgressRequest from "../fetchRequests/downloadProgressRequest"




type Props = {
    responseForDownload: downloadRequestResponse
    onClose: () => void
}

function DownloadProgressPanel(
    props: Props
    
)
    
{

    const [progress, updateProgress] = useState<downloadProgressResponse>(
        {id: props.responseForDownload.id,
        status: "queued",
        downloadProgress: 0,
        errorMessage: "",
        totalBytes: 0,
        downloadedBytes: 0,
        speed: 0,
        eta: 0,}
    )
    const serverAdress = "http://127.0.0.1:8000/download/progress/" + props.responseForDownload.id

    async function getDownloadProgress(){
        

        const response: downloadProgressResponse = await sendProgressRequest(serverAdress)
        

        updateProgress(response)

        if (response.status === "complete") {
            props.onClose()
            return true
        }
        return false
        
    }

    useEffect(function () {
        const interval = setInterval(async () => {

            const done = await getDownloadProgress()

            if (done === true) {
                
                clearInterval(interval)
            }
        }, 500)
//Cleanup function if this panel is closed too soon
        
        return () => clearInterval(interval)
        
    }, [])

    return (
        <>
            <div>
                <p>Download Progress</p>
                <p>{progress.downloadedBytes}/{progress.totalBytes}</p>
                <progress value={progress.downloadProgress} max={100}></progress>
                <button onClick={props.onClose}>Close</button>
                
            </div>
        </>
    )
}



export default DownloadProgressPanel