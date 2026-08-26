import type { SearchRequest } from "./models"
import type { Authorization } from "../general"
import { ServerAdressSearch } from "./models";



async function sendSearchRequest(
    request: SearchRequest,
    auth: Authorization
)
{

    if (!auth.key_name) {
    throw new Error("Authorization header name is empty")
    }

    if (!auth.key_value) {
        throw new Error("Authorization key is empty")
    }
    
    const response = await fetch(ServerAdressSearch, 
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

export default sendSearchRequest