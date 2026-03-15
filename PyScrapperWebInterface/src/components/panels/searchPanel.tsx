import { useState } from "react";
import type { SearchPanelPropertys, saveResults } from "../models/types";
import sendServerRequest from "../fetchRequests/searchRequest";









function SearchPanel(props: saveResults)
{
//mit setSerachData kann man dann die Values von searchData was aus SearchPanelPropertys besteht ändern
    const [searchData, setSearchData] = useState<SearchPanelPropertys>
    ({
        provider: "",
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
        <div>
            <div>
                <p>Provider</p>
                <input
                    type="text"
                    placeholder="...bandcamp"
/*value wird dann vom jetztigen State des providers im Textfeld den eingetippsten provider anzeigen */
                    value={searchData.provider}
/*onChange ist ein Event wenn das Textfeld geändert wird dann wrid setsearchData aufgerufen und wir ändern den Provider */
                    onChange={(e) =>
                        setSearchData
                        ({
/*...searchData kopiert uns den aktuellen Status von searchData und dann überschrieben wir provider */
                            ...searchData,
                            provider: e.target.value
                        })
                    }
                />
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
                max="10"
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
            <div>
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

