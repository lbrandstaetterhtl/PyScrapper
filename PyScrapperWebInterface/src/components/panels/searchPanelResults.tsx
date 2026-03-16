import type { SearchResult } from "../models/types";
import "../../designs/searchResultsPanel.css"



type Props = {
    searchResults: SearchResult[]
    saveResult: (result: any) => void
}



function SearchPanelResults(
    props: Props
)
{


    

    function handleSetResults(result:any){
       
        props.saveResult(result)



    }

    return (
        <>
            <div className="searchResultsPanel">
                
                    <h1> Search Results</h1>

                    <ul>
                        
                        {
                        props.searchResults.map((result, i) => (
                        
                            
                                <div className="searchResultsPanel-result"
                                key={result.identifier ?? i}
                                
                                >
                                    
                                    <img
                                        src={result.thumbnail}
                                        alt={result.title}
                                        width={300}
                                        height={120}
                                    />
                                    <p>{result.title}</p>
                                    

                                    <div className="searchResultsPanel-buttons">
                                        <button onClick={() => handleSetResults(result)}>
                                            Select
                
                                        </button>
                                    </div>
                                </div>
                            
                            
                                
                                
                            )
                            
                        )
                        }

                        
                    </ul>
                
            </div>
        </>
        

        
    )
}




export default SearchPanelResults