import type { downloadRequest } from "../models/types"

const SERVERADRESS = "http://127.0.0.1:8000/download"

async function sendDownloadRequest(downloadRequest: downloadRequest) 
{
    try{
        const response = await fetch(SERVERADRESS, 
            {
            method: "POST",
            headers: 
                {
                "Content-Type": "application/json"
                },
            body: JSON.stringify(downloadRequest)
            });

            console.log("Sucessful download request", response)

        const data = await response.json()
        console.log("successfull download request", data)
        return data


    }
    catch (error){
        console.log("Failed download request", error)
        
    }
}

export default sendDownloadRequest