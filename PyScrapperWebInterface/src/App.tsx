import SearchPanel from "./components/panels/searchPanel"
import SearchPanelResults from "./components/panels/searchPanelResults";
import DownloadRequestPanel from "./components/panels/dowloadRequestPanel";
import DownloadProgressPanel from "./components/panels/downloadProgressPanel";
import type { SearchResult } from "./components/models/types";
import { useState} from "react"

function App() {
  const [results, setResults] = useState<any[] | null>(null)
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>()
  const [activePanel, setActivePanel] = useState<"results" | "request" | "progress">("results")
  const [downloadProgress, setDownloadProgress] = useState<any | null>(null)

  function handleCloseProgressPanel(){
    setActivePanel("results")
    setDownloadProgress(null)
  }

  function handleCloseRequestPanel(){
    setActivePanel("results")
    setSelectedResult(null)
  }
  function handleStartDownload(response :any){
    setActivePanel("progress")
    setDownloadProgress(response)

  }

  function handleSelectResults(result: SearchResult){
    setSelectedResult(result)
    setActivePanel("request")
  }

  return (
    <>
      <div>
        <h1>PyScrapper Web GUI</h1>
        <p>Mein erstes React Interface läuft. :D</p>
        
        <SearchPanel ifResults={(newResult) =>{
          setResults(newResult)
          setActivePanel("results")
        }


        }
        
        />


        {results && activePanel === "results" &&(
          <SearchPanelResults
           searchResults={results}
           saveResult={handleSelectResults}
           
           />
        )}

        {selectedResult && activePanel === "request"&&(
          <DownloadRequestPanel
          result={selectedResult}
          onClose={handleCloseRequestPanel}
          onStartDownload={handleStartDownload}
          />
        )}

        {downloadProgress && activePanel === "progress" &&(
          <DownloadProgressPanel
            responseForDownload={downloadProgress}
            onClose={handleCloseProgressPanel}

          />
        )}
        

        
        

      </div>
    </>    
      
    
  );
}

export default App;