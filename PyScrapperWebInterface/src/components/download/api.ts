import { ServerAdressDownload } from "./models";
import type { DownloadRequest } from "./models";
import type { Authorization } from "../general";

import type { DownloadProgressResponse } from "./models";

export async function sendDownloadRequest(
    request: DownloadRequest,
    auth: Authorization
)
{
    try
    {
        const response = await fetch(ServerAdressDownload, 
            {
            method: "POST",
            headers: 
                {
                "Content-Type": "application/json",
                [auth.key_name] : auth.key_value
                
                },
            body: JSON.stringify(request)
            });

        const data = await response.json();
        console.log("Server response:", data);
        return data
    }


    catch (error)
    {
        console.error("An error occured:", error)
        return null
    }
}



export async function getDownloadProgress(
    url: string,
    auth: Authorization
): Promise<DownloadProgressResponse | null> 
{
    try {
        const response = await fetch(url, 
            {
            method: "GET",
            headers: 
            {
                [auth.key_name]: auth.key_value
            }
        })

        if (!response.ok) 
            {
            throw new Error(`HTTP ${response.status}`)
            }

        return await response.json()
    }
    catch (error) 
    {
        console.error("Failed to get download progress:", error)
        return null
    }
}





