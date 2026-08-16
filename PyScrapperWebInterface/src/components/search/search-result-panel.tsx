import type { SearchResult } from "./models"
import type { DownloadRequest } from "../download/models"


type Results = {
    results: SearchResult[]
    updateResults : React.Dispatch<React.SetStateAction<SearchResult[]>>
    updateDownloadRequest : React.Dispatch<React.SetStateAction<DownloadRequest>>
    onSearchResultFinished: () => void
    onResultReset: () => void
}

function SearchResultPanel({results,updateResults, updateDownloadRequest,  onSearchResultFinished, onResultReset} : Results)
{
    function chooseDownload(result: any)
    {
        updateDownloadRequest(prev => ({
            ...prev,
            provider: result.provider,
            urls: [result.url],
            filenames: [""],
            download_path: "",
            download_strategie: "stream",
            extra_headers: {}
        }))
            
        onSearchResultFinished()
    }
    
    function resetResults()
    {
        updateResults([])
        onResultReset()
    }

    return (
        <div className="results-view">
            <div className="section-toolbar">
                <div>
                    <p className="eyebrow">SEARCH OUTPUT</p>
                    <h2>Search results</h2>
                    <p className="panel-description">{results.length} result{results.length === 1 ? "" : "s"} currently loaded.</p>
                </div>
                <button className="button button-secondary" onClick={resetResults}>Reset Results</button>
            </div>

            {(!Array.isArray(results) || results.length === 0) && (
                <div className="empty-state">
                    <span className="empty-icon">&gt;_</span>
                    <h3>No results yet</h3>
                    <p>Run a search to populate this workspace.</p>
                </div>
            )}

            <div className="result-grid">
                {results.map((result, index) =>
                    <article className="result-card" key={`${result.url}-${index}`}>
                        <div className="result-image-wrap">
                            <img
                                src={result.thumbnail}
                                alt={result.title}
                            />
                            <span className="provider-badge">{result.provider}</span>
                        </div>

                        <div className="result-content">
                            <span className="result-index">RESULT {String(index + 1).padStart(2, "0")}</span>
                            <h3>{result.title}</h3>
                            <p className="url-text" title={result.url}>{result.url}</p>

                            <button className="button button-primary" onClick={() => chooseDownload(result)}>
                                Use for Request
                            </button>
                        </div>
                    </article>
                )}
            </div>
        </div>
    )
}

export default SearchResultPanel
