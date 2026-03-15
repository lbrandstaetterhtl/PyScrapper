import SearchPanel from "./components/panels/searchPanel"
import SearchPanelResults from "./components/panels/searchPanelResults";
import { useState} from "react"

function App() {
  const [results, setResults] = useState<any[]>([])
  return (
    <>
      <div>
        <h1>PyScrapper Web GUI</h1>
        <p>Mein erstes React Interface läuft. :D</p>
        
        <SearchPanel ifResults={setResults}/>

        <SearchPanelResults searchResults={results}/>

        
        

      </div>
    </>    
      
    
  );
}

export default App;