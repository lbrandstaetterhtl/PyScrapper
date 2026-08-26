import { useState } from "react"

import type { Authorization } from "./components/general"

import { Panel } from "./components/general"
import type { Panel as PanelType } from "./components/general"

import type { SearchResult } from "./components/search/models"
import { type DownloadResult, ProvidersDownload, type DownloadRequest } from "./components/download/models"

import AuthPanel from "./components/authorization/auth-panel"
import SearchPanel from "./components/search/search-panel"
import SearchResultPanel from "./components/search/search-result-panel"
import DownloadPanel from "./components/download/download-panel"
import DownloadResultPanel from "./components/download/download-result-panel"

import "./components/general.css"
import "./components/authorization/auth-design.css"
import "./components/search/search-design.css"
import "./components/download/download-panel.css"


function App() {
    const [auth, updateAuth] = useState<Authorization>({
        key_name: "X-Admin-Key",
        key_value: ""
    })

    const [searchResults, updateSearchResults] = useState<SearchResult[]>([])

    const [curPanel, setPanel] =useState<PanelType>(Panel.AUTHORIZATION)

    const [downloadHistory, updateDownloadResult] = useState<DownloadResult[]>([])

    const [curDownloadRequest, updateDownloadRequest] = useState<DownloadRequest>({
        provider: ProvidersDownload.Youtube_Music,
        download_strategie: "stream",
        urls: [],
        filenames: [],
        download_path: "",
        extra_headers: {}

    })

    return (
        <div className="app-shell">
            <aside className="sidebar">
                <div className="brand">
                    <div className="brand-mark">&gt;_</div>
                    <div>
                        <div className="brand-name"><span>Py</span>Scrapper</div>
                        <div className="brand-subtitle">media control interface</div>
                    </div>
                </div>

                <nav className="sidebar-nav" aria-label="Main navigation">
                    <button
                        className={`nav-button ${curPanel === Panel.AUTHORIZATION ? "active" : ""}`}
                        onClick={() => setPanel(Panel.AUTHORIZATION)}
                    >
                        <span className="nav-index">01</span>
                        <span>Authorize</span>
                    </button>

                    <button
                        className={`nav-button ${curPanel === Panel.SEARCH ? "active" : ""}`}
                        onClick={() => setPanel(Panel.SEARCH)}
                    >
                        <span className="nav-index">02</span>
                        <span>Search</span>
                    </button>

                    <button
                        className={`nav-button ${curPanel === Panel.SEARCH_RESULT ? "active" : ""}`}
                        onClick={() => setPanel(Panel.SEARCH_RESULT)}
                    >
                        <span className="nav-index">03</span>
                        <span>Search Results</span>
                    </button>

                    <button
                        className={`nav-button ${curPanel === Panel.DOWNLOAD ? "active" : ""}`}
                        onClick={() => setPanel(Panel.DOWNLOAD)}
                    >
                        <span className="nav-index">04</span>
                        <span>Request</span>
                    </button>

                    <button
                        className={`nav-button ${curPanel === Panel.DOWNLOAD_RESULT ? "active" : ""}`}
                        onClick={() => setPanel(Panel.DOWNLOAD_RESULT)}
                    >
                        <span className="nav-index">05</span>
                        <span>Results & History</span>
                    </button>
                </nav>

                <div className="sidebar-footer">
                    <span className="status-dot" />
                    <span>PyScrapper Web</span>
                </div>
            </aside>

            <main className="main-content">
                <header className="topbar">
                    <div>
                        <p className="eyebrow">PYTHON MEDIA TOOLKIT</p>
                        <h1>{curPanel.replaceAll("_", " ")}</h1>
                    </div>
                    <div className="topbar-chip">
                        <span className="status-dot" /> Server
                    </div>
                </header>

                <section className="workspace">
                    {curPanel === Panel.AUTHORIZATION && (
                        <AuthPanel
                            auth={auth}
                            updateAuth={updateAuth}
                        />
                    )}

                    {curPanel === Panel.SEARCH &&(
                        <SearchPanel
                            auth={auth}
                            updateResults={updateSearchResults}
                            onSearchFinished={() => setPanel(Panel.SEARCH_RESULT)}
                        />
                    )}

                    {curPanel === Panel.SEARCH_RESULT && (
                        <SearchResultPanel
                            results={searchResults}
                            updateResults={updateSearchResults}
                            updateDownloadRequest={updateDownloadRequest}
                            onSearchResultFinished={() => setPanel(Panel.DOWNLOAD)}
                            onResultReset={() => setPanel(Panel.SEARCH)}
                        />
                    )}
                    {curPanel === Panel.DOWNLOAD && (
                        <DownloadPanel
                            auth={auth}
                            request={curDownloadRequest}
                            updateDownloadRequest={updateDownloadRequest}
                            updateDownloadHistory={updateDownloadResult}
                            onFinishedDownload={() => setPanel(Panel.DOWNLOAD_RESULT)}
                        />
                    )}

                    {curPanel === Panel.DOWNLOAD_RESULT && (
                        <DownloadResultPanel
                            history={downloadHistory}
                            auth={auth}
                            updateDownloadHistory={updateDownloadResult}
                        />
                    )}
                </section>
            </main>
        </div>
    )
}

export default App
