import { useState } from "react"
import type { Authorization } from "../general"


type AuthPanelProps = {
    auth: Authorization
    updateAuth: React.Dispatch<React.SetStateAction<Authorization>>
}

function AuthPanel({ auth, updateAuth }: AuthPanelProps)
{

    const [showPassword, updateShowPassword] = useState<boolean>(false)

    function showHidePassword()
    {
        if (showPassword)
        {
            updateShowPassword(false)
        }
        else
        {
            updateShowPassword(true)
        }
    }

    return (
        <div className="panel-card auth-panel">
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">ACCESS CONTROL</p>
                    <h2>Authorization</h2>
                    <p className="panel-description">Configure the credentials sent with requests to your PyScrapper API.</p>
                </div>
                <span className="terminal-badge">auth.config</span>
            </div>

            <div className="form-grid">
                <label className="field-group">
                    <span className="field-label">Key Name</span>
                    <input
                        type="text"
                        placeholder="Admin-Key"
                        value={auth.key_name}
                        onChange={(e) =>
                            updateAuth
                            ({
                                ...auth,
                                key_name: e.target.value
                            })
                        }/>
                    <span className="field-hint">Header name used for authentication</span>
                </label>

                <label className="field-group">
                    <span className="field-label">Key Value</span>
                    <div className="password-field">
                        <input
                            type={showPassword ? "text" : "password"}
                            placeholder="Key1234!"
                            value={auth.key_value}
                            onChange={(e) =>
                                updateAuth({
                                    ...auth,
                                    key_value: e.target.value
                                })
                            }
                        />

                        <button
                            type="button"
                            className="password-toggle"
                            onClick={showHidePassword}
                        >
                            {showPassword ? "Hide" : "Show"}
                        </button>
                    </div>
                    <span className="field-hint">Value attached to API requests</span>
                </label>
            </div>
        </div>
    )
}

export default AuthPanel
