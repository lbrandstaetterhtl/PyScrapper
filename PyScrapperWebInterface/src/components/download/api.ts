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

function formatApiError(value: unknown): string {
    if (typeof value === "string") return value

    if (Array.isArray(value)) {
        const messages = value
            .map((item) => {
                if (item && typeof item === "object") {
                    const error = item as {
                        msg?: unknown
                        message?: unknown
                        loc?: unknown
                    }

                    const message =
                        typeof error.msg === "string"
                            ? error.msg
                            : typeof error.message === "string"
                                ? error.message
                                : null

                    if (message) {
                        const location = Array.isArray(error.loc)
                            ? error.loc.map(String).join(".")
                            : ""

                        return location ? `${location}: ${message}` : message
                    }
                }

                return formatApiError(item)
            })
            .filter(Boolean)

        return messages.join("; ")
    }

    if (value && typeof value === "object") {
        const objectValue = value as Record<string, unknown>

        if ("detail" in objectValue) return formatApiError(objectValue.detail)
        if ("message" in objectValue) return formatApiError(objectValue.message)

        try {
            return JSON.stringify(value)
        } catch {
            return String(value)
        }
    }

    if (value == null) return ""
    return String(value)
}

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
            preferred_file: request.preferred_file || null,
            auto_convert: request.preferred_file ? request.auto_convert : false
        })
    })

    let data
    try {
        data = await response.json()
    } catch {
        data = null
    }

    if (!response.ok) {
        const message = formatApiError(data)

        throw new Error(
            message || `HTTP Error ${response.status}: ${response.statusText}`
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
        const message = formatApiError(data)
        throw new Error(message || `HTTP ${response.status}`)
    }

    return data as DownloadProgress
}
