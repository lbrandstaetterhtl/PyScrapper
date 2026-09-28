import type { Authorization } from "../general"

export type AuthServerResponse = {
    message: string
    identifier: string
    user_key: string
}

type LoginResponse = {
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

function validateCredentials(auth: Authorization) {
    if (!auth.username.trim()) throw new Error("Username is empty")
    if (!auth.password) throw new Error("Password is empty")
}

function validateAdminCredentials(auth: Authorization) {
    if (!auth.key_name.trim()) throw new Error("Admin key header name is empty")
    if (!auth.key_value.trim()) throw new Error("Admin key is required to register a user")
}

async function ensureOk(response: Response) {
    const data = await readJson(response)

    if (!response.ok) {
        throw new Error(
            data?.detail ??
            data?.message ??
            `HTTP Error ${response.status}: ${response.statusText}`
        )
    }

    return data
}

async function loadUserKey(identifier: string): Promise<string> {
    // The server login endpoint intentionally returns only the identifier.
    // Afterwards we load the user's ApiKey from /get/user/{identifier}.
    const response = await fetch(`/api/get/user/${encodeURIComponent(identifier)}`, {
        method: "GET",
        headers: {
            "Auth": identifier
        }
    })

    const data = await ensureOk(response) as UserResponse | null

    if (!data?.ApiKey) {
        throw new Error("User response did not contain an ApiKey")
    }

    return data.ApiKey
}

async function finishAuthentication(data: LoginResponse | null): Promise<AuthServerResponse> {
    if (!data?.identifier) {
        throw new Error("Authentication response did not contain an identifier")
    }

    const userKey = await loadUserKey(data.identifier)

    return {
        message: data.message,
        identifier: data.identifier,
        user_key: userKey
    }
}

export async function login(auth: Authorization): Promise<AuthServerResponse> {
    validateCredentials(auth)

    const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username: auth.username,
            password: auth.password
        })
    })

    const data = await ensureOk(response) as LoginResponse | null
    return finishAuthentication(data)
}

export async function register(auth: Authorization): Promise<AuthServerResponse> {
    validateCredentials(auth)
    validateAdminCredentials(auth)

    const response = await fetch("/api/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            [auth.key_name.trim()]: auth.key_value.trim()
        },
        body: JSON.stringify({
            username: auth.username,
            password: auth.password,
            apikey: auth.key_value
        })
    })

    const data = await ensureOk(response) as LoginResponse | null
    return finishAuthentication(data)
}
