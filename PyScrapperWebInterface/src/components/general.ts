export type Authorization = {
    /** Header used for administrative bootstrap requests such as login/register/get user. */
    key_name: string;
    /** ADMIN_KEY value from the server .env. */
    key_value: string;
    username: string;
    password: string;
    /** Identifier returned by /login or /register. This is sent as the Auth header. */
    identifier: string;
    /** ApiKey returned by /get/user/{identifier}. This is sent as X-User-Key. */
    user_key: string;
}

export function buildUserHeaders(auth: Authorization): Record<string, string> {
    if (!auth.identifier.trim()) {
        throw new Error("You are not logged in. Login or register first.")
    }
    if (!auth.user_key.trim()) {
        throw new Error("User key is missing. Login again so the user profile can be loaded.")
    }

    return {
        "X-User-Key": auth.user_key.trim(),
        "Auth": auth.identifier.trim()
    }
}

export const Panel = {
    AUTHORIZATION: "AUTHORIZATION",
    SEARCH: "SEARCH",
    SEARCH_RESULT: "SEARCH_RESULT",
    DOWNLOAD: "DOWNLOAD",
    DOWNLOAD_RESULT: "DOWNLOAD_RESULT"
} as const

export type Panel = typeof Panel[keyof typeof Panel]
