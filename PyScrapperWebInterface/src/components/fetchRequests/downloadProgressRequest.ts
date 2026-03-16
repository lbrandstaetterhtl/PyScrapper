
async function sendProgressRequest(
    serverAdress: string
)
{
    try 
    {
        const response = await fetch(serverAdress, 
            {
            method: "GET",
            headers: 
                {
                "Content-Type": "application/json"
                },
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

export default sendProgressRequest