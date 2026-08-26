import { ServerAdressDownload } from "./models";
import type { DownloadRequest } from "./models";
import type { Authorization } from "../general";

import type { DownloadProgressResponse } from "./models";

export async function sendDownloadRequest(
    request: DownloadRequest,
    auth: Authorization
)
{
    if (!auth.key_name) {
    throw new Error("Authorization header name is empty")
    }

    if (!auth.key_value) {
        throw new Error("Authorization key is empty")
    }
    
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

    
    let data

    try {
        data = await response.json()
    } catch {
        data = null
    }

    if (!response.ok) {
        throw new Error(
            data?.detail ??
            data?.message ??
            `HTTP Error ${response.status}: ${response.statusText}`
        )
    }
    console.log("Server response:", data);
    return data
   
}



export async function getDownloadProgress(
    url: string,
    auth: Authorization
): Promise<DownloadProgressResponse | null> 
{
    if (!auth.key_name) {
        throw new Error("Authorization header name is empty")
    }

    if (!auth.key_value) {
        throw new Error("Authorization key is empty")
    }
        
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





