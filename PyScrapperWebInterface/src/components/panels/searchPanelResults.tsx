import type { SearchResult } from "../models/types";




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
            <div>
                <h2> Search Results</h2>

                <ul>
                    
                    {
                    props.searchResults.map((result, i) => (
                    
                        
                            <div 
                            key={result.identifier ?? i}
                            style={{
                                border: "4px",
                                borderColor: "pink",
                                padding: "10px",
                                marginBottom: "10px",
                                
                            }}
                            >
                                <img
                                    src={result.thumbnail}
                                    alt={result.title}
                                    width={300}
                                    height={120}
                                />
                                <p>{result.title}</p>

                                <button onClick={() => handleSetResults(result)}>
                                    Select
        
                                </button>
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