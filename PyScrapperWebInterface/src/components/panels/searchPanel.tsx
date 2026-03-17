import { useState, } from "react";
import type { SearchPanelPropertys, SearchResult } from "../models/types";

import sendServerRequest from "../fetchRequests/searchRequest";
import "../../designs/searchPanel.css"
import { providers, } from "../models/config";





type Props = {
    ifResults: (results: SearchResult[]) => void;
    
}




function SearchPanel(props: Props)
{
//mit setSerachData kann man dann die Values von searchData was aus SearchPanelPropertys besteht ändern
    const [searchData, setSearchData] = useState<SearchPanelPropertys>
    ({
        provider: providers[0] ?? "",
        search: "",
        top: 5
    })

    async function handleClick() {
        const data = await handleSearch(searchData)
        if (!data){
            return
        }
        const resultWithProvider = data.results.map((result: any) => ({
            ...result,
            provider: data.provider
        })
        )
        props.ifResults(resultWithProvider)
    }

    return (
        <div className="searchPanel">
            <div className="searchPanel-searchOptions">
                <h1>PyScrapper - Finder</h1>
                <p>Provider</p>
                <select
                    onChange={(e) => 
                        setSearchData({
                            ...searchData,
                            provider: e.target.value
                        })
                    }
                >
                    {providers.map((provider, i) =>(
                        <option value={provider} key={provider ?? i}>
                            {provider}
                        </option>
                    ))}

                </select>
                <p>Searchquery</p>
                <input
                type="text"
                placeholder="...Expedition 33"
                value={searchData.search}
                onChange={(e) =>
                    setSearchData
                    ({
                        ...searchData,
                        search: e.target.value
                    })
                }
                />
                <p>Results</p>
                <input
/*Mit type sagen wir hier das nur Zahlen erlaubt sind und wir bekommen dadurch pfeile womit man hoch und runter setzen kann */                
                type="number" 
                max="25"
                min="1"
                value={searchData.top}
                onChange={(e) =>
                    {
                    const value = Number(e.target.value);
                    if (!isNaN(value) && value >=1) 
                        {
                        setSearchData
                        ({
                            ...searchData,
                            top: value
                        })
                        }
                        else
                            {
                                setSearchData
                                ({
                                    ...searchData,
                                    top: 1
                                })
                            }
                    } 
                    
                } 
                />
                
                
            </div>
            <div className="searchPanel-buttons">
                <button onClick={handleClick}>
                    Start Search
                </button>
            </div>
        
                
            
        </div>
    )
}


async function handleSearch(
    searchData: SearchPanelPropertys
) 
{
    const data = await sendServerRequest(searchData)
    console.log(data)
    return data
}


export default SearchPanel

