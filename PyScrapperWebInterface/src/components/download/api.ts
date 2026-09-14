import { ServerAdressDownload } from "./models"
import type { DownloadProgress, DownloadRequest, ServerResultDownload } from "./models"
import type { Authorization } from "../general"
import { buildUserHeaders } from "../general"

function apiUrl(url: string): string {
    if (!url) return ""
    if (/^https?:\/\//i.test(url)) return url
    if (url.startsWith("/api/")) return url
    return `/api${url.startsWith("/") ? url : `/${url}`}`
}

export { apiUrl }

export async function sendDownloadRequest(
    request: DownloadRequest,
    auth: Authorization
): Promise<ServerResultDownload> {
    const response = await fetch(ServerAdressDownload, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...buildUserHeaders(auth)
        },
        body: JSON.stringify({
            ...request,
            preferred_type: request.preferred_type || null,
            preferred_file: request.preferred_file || null
        })
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

    return data as ServerResultDownload
}

export async function getDownloadProgress(
    url: string,
    auth: Authorization
): Promise<DownloadProgress> {
    const response = await fetch(apiUrl(url), {
        method: "GET",
        headers: buildUserHeaders(auth)
    })

    let data
    try {
        data = await response.json()
    } catch {
        data = null
    }

    if (!response.ok) {
        throw new Error(data?.detail ?? `HTTP ${response.status}`)
    }

    return data as DownloadProgress
}
