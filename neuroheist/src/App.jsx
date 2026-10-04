import { useState } from "react";
import ScanUpload from "./components/ScanUpload";
import ResultsView from "./components/ResultsView";
import "./App.css";

function App() {
  // null = no scan analyzed yet (show upload); anything else = show results
  const [result, setResult] = useState(null);
  const [file, setFile] = useState(null);

  return (
    <div className="app">
      {result === null ? (
        <div className="glass panel">
          <h1 className = "title">Brain scan analysis</h1>
          <p className="subtitle">
            Upload an MRI scan to detect and visualize tumor regions in 3D.
          </p>
          {/* When the upload finishes, save both the backend data and the file */}
          <ScanUpload
            onResult={(data, uploadedFile) => {
              setResult(data);
              setFile(uploadedFile);
            }}
          />
        </div>
      ) : (
        <ResultsView
          result={result}
          file={file}
          onNewScan={() => {
            setResult(null);
            setFile(null);
          }}
        />
      )}
    </div>
  );
}

export default App;