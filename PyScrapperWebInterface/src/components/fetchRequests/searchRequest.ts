import type { SearchPanelPropertys } from "../models/types";

const serverAdress = "http://127.0.0.1:8000/search"


async function sendServerRequest(
    searchData: SearchPanelPropertys,

) {
    try 
    {
        const response = await fetch(serverAdress, 
            {
            method: "POST",
            headers: 
                {
                "Content-Type": "application/json"
                },
            body: JSON.stringify(searchData)
            });

        const data = await response.json();
        console.log("Server response:", data);
        return data


    } 
    catch (error) 
        {
        console.error("Request failed:", error);
        return null
        }
}

export default sendServerRequest