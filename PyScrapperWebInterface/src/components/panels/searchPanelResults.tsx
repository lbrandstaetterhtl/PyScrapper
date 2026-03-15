import type { SearchResult } from "../models/types";
import DownloadRequestPanel from "./dowloadRequestPanel";
import { useState } from "react";


type Props = {
    searchResults: SearchResult[]
}



function SearchPanelResults(
    props: Props
)
{
    const  [selectedResult, setSelectedResult] = useState<SearchResult | null>(null)

    return (
        <>
            <div>
                <h2> Search Results</h2>

                <ul>
                    
                    {
                    props.searchResults.map((result, i) => (
                    
                        
                            <div 
                            key={result.identifier ?? i}
                            style={{
                                border: "1px pink",
                                padding: "10px",
                                marginBottom: "10px"
                            }}
                            >
                                <img
                                    src={result.thumbnail}
                                    alt={result.title}
                                    width={300}
                                    height={120}
                                />
                                <p>{result.title}</p>

                                <button onClick={() => setSelectedResult(result)}>
                                    Download
                                </button>
                            </div>
                            
                            
                            
                        )
                        
                    )
                    }

                    {selectedResult && (
                        <DownloadRequestPanel
                            result={selectedResult}
                            onClose={() => setSelectedResult(null)}
                        />
                    )}
                </ul>
                
            </div>
        </>
        

        
    )
}




export default SearchPanelResults