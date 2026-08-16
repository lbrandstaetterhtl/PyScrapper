import { useState } from "react"

import type { SearchRequest, SearchResult } from "./models"
import { ProvidersSearch } from "./models"
import type { Authorization } from "../general"

import sendSearchRequest from "./api"


type AuthProp = {
    auth: Authorization,
    updateResults : React.Dispatch<React.SetStateAction<SearchResult[]>>
    onSearchFinished: () => void
}

function SearchPanel({auth, updateResults, onSearchFinished} : AuthProp )
{
    const [request, updateSearchRequest] = useState<SearchRequest>({
        search: "",
        provider: "youtube",
        top: 5,
        filters: {
            tags: [
                "track"
            ]
        }
    })

    async function startSearch() {
        const searchResult = await sendSearchRequest(request, auth)

        const results: SearchResult[] = []

        for (const result of searchResult.results) {
            const item: SearchResult = {
                url: result.url,
                thumbnail: result.thumbnail,
                title: result.title,
                provider: searchResult.provider
            }

            results.push(item)
        }

        updateResults(results)
        onSearchFinished()
    }
    
    return (
        <div className="panel-card search-panel">
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">DISCOVERY</p>
                    <h2>Search media</h2>
                    <p className="panel-description">Search a provider and pass a result directly into your existing download request flow.</p>
                </div>
                <span className="terminal-badge">provider.search()</span>
            </div>

            <div className="form-grid search-form-grid">
                <label className="field-group">
                    <span className="field-label">Provider</span>
                    <select
                        value={request.provider}
                        onChange={(e) =>
                            updateSearchRequest({
                                ...request,
                                provider: e.target.value
                            })
                        }
                    >
                        {Object.entries(ProvidersSearch).map(([key, value]) => (
                            <option key={value} value={value}>
                                {key}
                            </option>
                        ))}
                    </select>
                </label>

                <label className="field-group field-grow">
                    <span className="field-label">Search Query</span>
                    <input
                        type="text"
                        placeholder="Cute dog videos"
                        value={request.search}
                        onChange={(e) =>
                            updateSearchRequest({
                                ...request,
                                search: e.target.value
                            })
                        }
                    />
                </label>

                <label className="field-group compact-field">
                    <span className="field-label">Results</span>
                    <input
                        type="number"
                        min="1"
                        max="10"
                        value={request.top}
                        onChange={(e) =>{
                            const num = Number(e.target.value)
                            if (isNaN! && num > 0)
                            {
                                updateSearchRequest(
                                    {
                                        ...request,
                                        top: num
                                    }
                                )
                            }
                            else {
                                updateSearchRequest(
                                    {
                                        ...request,
                                        top: 1
                                    }
                                )
                            }
                        }}
                    />
                </label>
            </div>

            <div className="panel-actions">
                <button className="button button-primary" onClick={startSearch}>
                    <span className="button-prompt">$</span> Start Search
                </button>
            </div>
        </div>
    )
}

export default SearchPanel
