import type { SearchRequest } from "./models"
import type { Authorization } from "../general"
import { buildUserHeaders } from "../general"
import { ServerAdressSearch } from "./models"

async function sendSearchRequest(request: SearchRequest, auth: Authorization) {
    const response = await fetch(ServerAdressSearch, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...buildUserHeaders(auth)
        },
        body: JSON.stringify(request)
    })

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

    return data
}

export default sendSearchRequest
