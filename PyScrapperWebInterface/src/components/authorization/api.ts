import type { Authorization } from "../general"

export type AuthServerResponse = {
    message: string
    identifier: string
}

type UserResponse = {
    Identifier: string
    Username: string
    CreatedAt: string
    ApiKey: string
}

async function readJson(response: Response) {
    try {
        return await response.json()
    } catch {
        return null
    }
}

function validateAuthInput(auth: Authorization) {
    if (!auth.key_name.trim()) throw new Error("Admin key header name is empty")
    if (!auth.key_value.trim()) throw new Error("Admin key is empty")
    if (!auth.username.trim()) throw new Error("Username is empty")
    if (!auth.password) throw new Error("Password is empty")
}

function adminHeaders(auth: Authorization): Record<string, string> {
    if (!auth.key_name.trim()) throw new Error("Admin key header name is empty")
    if (!auth.key_value.trim()) throw new Error("Admin key is empty")

    return {
        [auth.key_name.trim()]: auth.key_value.trim()
    }
}

async function sendAuthRequest(
    endpoint: "/login" | "/register",
    auth: Authorization
): Promise<AuthServerResponse> {
    validateAuthInput(auth)

    const body = endpoint === "/register"
        ? {
            username: auth.username,
            password: auth.password,
            // The current server RegisterRequest still expects `apikey`.
            // The actual X-User-Key used afterwards is fetched from /get/user.
            apikey: auth.key_value
        }
        : {
            username: auth.username,
            password: auth.password
        }

    const response = await fetch(`/api${endpoint}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...adminHeaders(auth)
        },
        body: JSON.stringify(body)
    })

    const data = await readJson(response)

    if (!response.ok) {
        throw new Error(
            data?.detail ??
            data?.message ??
            `HTTP Error ${response.status}: ${response.statusText}`
        )
    }

    if (!data?.identifier) {
        throw new Error("Authentication response did not contain an identifier")
    }

    return data as AuthServerResponse
}

export async function getUserKey(auth: Authorization, identifier: string): Promise<string> {
    if (!identifier.trim()) throw new Error("Missing user identifier")

    const response = await fetch(`/api/get/user/${encodeURIComponent(identifier)}`, {
        method: "GET",
        headers: {
            ...adminHeaders(auth),
            "Auth": identifier
        }
    })

    const data = await readJson(response) as UserResponse | null

    if (!response.ok) {
        throw new Error(
            (data as any)?.detail ??
            (data as any)?.message ??
            `Failed to load user key: HTTP ${response.status}`
        )
    }

    if (!data?.ApiKey?.trim()) {
        throw new Error("/get/user response did not contain ApiKey")
    }

    return data.ApiKey.trim()
}

export function login(auth: Authorization) {
    return sendAuthRequest("/login", auth)
}

export function register(auth: Authorization) {
    return sendAuthRequest("/register", auth)
}
