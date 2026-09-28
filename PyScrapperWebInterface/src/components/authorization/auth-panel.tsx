import { useState } from "react"
import type { Authorization } from "../general"
import { login, register } from "./api"

type AuthPanelProps = {
    auth: Authorization
    updateAuth: React.Dispatch<React.SetStateAction<Authorization>>
}

function AuthPanel({ auth, updateAuth }: AuthPanelProps) {
    const [showClientKey, setShowClientKey] = useState(false)
    const [showPassword, setShowPassword] = useState(false)
    const [registerMode, setRegisterMode] = useState(false)
    const [loadingAction, setLoadingAction] = useState<"login" | "register" | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [message, setMessage] = useState<string | null>(null)

    async function authenticate(action: "login" | "register") {
        setLoadingAction(action)
        setError(null)
        setMessage(null)

        try {
            const response = action === "login"
                ? await login(auth)
                : await register(auth)

            updateAuth(prev => ({
                ...prev,
                identifier: response.identifier,
                user_key: response.user_key
            }))

            setMessage(`${response.message} · user key loaded`)
        } catch (err) {
            updateAuth(prev => ({ ...prev, identifier: "", user_key: "" }))
            setError(err instanceof Error ? err.message : "Unknown authentication error")
        } finally {
            setLoadingAction(null)
        }
    }

    return (
        <div className="panel-card auth-panel">
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">ACCESS CONTROL</p>
                    <h2>Authorization</h2>
                    <p className="panel-description">
                        Login with your username and password. Administrative credentials are only needed when creating a new user.
                    </p>
                </div>
                <span className="terminal-badge">auth.config</span>
            </div>

            <div className="form-grid">
                <label className="field-group">
                    <span className="field-label">Username</span>
                    <input
                        type="text"
                        autoComplete="username"
                        placeholder="username"
                        value={auth.username}
                        onChange={(e) => updateAuth({ ...auth, username: e.target.value, identifier: "", user_key: "" })}
                    />
                </label>

                <label className="field-group">
                    <span className="field-label">Password</span>
                    <div className="password-field">
                        <input
                            type={showPassword ? "text" : "password"}
                            autoComplete="current-password"
                            placeholder="password"
                            value={auth.password}
                            onChange={(e) => updateAuth({ ...auth, password: e.target.value, identifier: "", user_key: "" })}
                        />
                        <button type="button" className="password-toggle" onClick={() => setShowPassword(v => !v)}>
                            {showPassword ? "Hide" : "Show"}
                        </button>
                    </div>
                </label>
            </div>

            {registerMode && (
                <div className="conditional-panel">
                    <div className="conditional-marker">ADMIN</div>
                    <div className="form-grid field-wide">
                        <label className="field-group">
                            <span className="field-label">Admin Key Header</span>
                            <input
                                type="text"
                                placeholder="e.g. X-Admin-Key"
                                value={auth.key_name}
                                onChange={(e) => updateAuth({ ...auth, key_name: e.target.value, identifier: "", user_key: "" })}
                            />
                            <span className="field-hint">Only sent when creating a new user.</span>
                        </label>

                        <label className="field-group">
                            <span className="field-label">Admin Key</span>
                            <div className="password-field">
                                <input
                                    type={showClientKey ? "text" : "password"}
                                    placeholder="e.g. AdminKey1234!"
                                    value={auth.key_value}
                                    onChange={(e) => updateAuth({ ...auth, key_value: e.target.value, identifier: "", user_key: "" })}
                                />
                                <button type="button" className="password-toggle" onClick={() => setShowClientKey(v => !v)}>
                                    {showClientKey ? "Hide" : "Show"}
                                </button>
                            </div>
                            <span className="field-hint">Required only for registration.</span>
                        </label>
                    </div>
                </div>
            )}

            {auth.identifier && auth.user_key && (
                <div className="conditional-panel">
                    <div className="conditional-marker">AUTH</div>
                    <div className="field-group field-wide">
                        <span className="field-label">User Identifier / Auth Header</span>
                        <code className="url-text">{auth.identifier}</code>
                        <span className="field-hint">X-User-Key was returned by login/registration</span>
                    </div>
                </div>
            )}

            {error && (
                <div className="error-box">
                    <strong>Authentication failed</strong>
                    <span>{error}</span>
                </div>
            )}

            {message && !error && (
                <div className="conditional-panel">
                    <div className="conditional-marker">OK</div>
                    <span>{message}</span>
                </div>
            )}

            <div className="panel-actions">
                <button
                    className="button button-primary"
                    onClick={() => authenticate("login")}
                    disabled={loadingAction !== null}
                >
                    {loadingAction === "login" ? <span className="spinner" /> : <><span className="button-prompt">$</span> Login</>}
                </button>
                {registerMode ? (
                    <>
                        <button
                            className="button button-secondary"
                            onClick={() => authenticate("register")}
                            disabled={loadingAction !== null}
                        >
                            {loadingAction === "register" ? <span className="spinner" /> : "Create User"}
                        </button>
                        <button
                            className="button button-secondary"
                            onClick={() => {
                                setRegisterMode(false)
                                setError(null)
                                setMessage(null)
                            }}
                            disabled={loadingAction !== null}
                        >
                            Cancel
                        </button>
                    </>
                ) : (
                    <button
                        className="button button-secondary"
                        onClick={() => {
                            setRegisterMode(true)
                            setError(null)
                            setMessage(null)
                        }}
                        disabled={loadingAction !== null}
                    >
                        Register
                    </button>
                )}
            </div>
        </div>
    )
}

export default AuthPanel
