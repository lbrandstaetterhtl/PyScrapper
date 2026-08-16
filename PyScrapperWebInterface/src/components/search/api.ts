import type { SearchRequest } from "./models"
import type { Authorization } from "../general"
import { ServerAdressSearch } from "./models";



async function sendSearchRequest(
    request: SearchRequest,
    auth: Authorization
)
{
    try
    {
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

export default sendSearchRequest