
import { useState } from "react";
import ScanUpload from "./components/ScanUpload";
import ResultsView from "./components/ResultsView";
import TreatmentComparison from "./components/TreatmentComparison";
import "./App.css";

function App() {
  const [result, setResult] = useState(null);
  const [file, setFile] = useState(null);
  const [showComparison, setShowComparison] = useState(false);

  return (
    <div className="app">
      {result === null ? (
        <div className="glass panel">
          <h1>Brain scan analysis</h1>
          <p className="subtitle">
            Upload an MRI scan to detect and visualize tumor regions in 3D.
          </p>

          <ScanUpload
            onResult={(data, uploadedFile) => {
              setResult(data);
              setFile(uploadedFile);
            }}
          />
        </div>
      ) : showComparison ? (
        <TreatmentComparison
          file={file}
          onBack={() => setShowComparison(false)}
        />
      ) : (
        <ResultsView
          result={result}
          file={file}
          onCompare={() => setShowComparison(true)}
          onNewScan={() => {
            setResult(null);
            setFile(null);
            setShowComparison(false);
          }}
        />
      )}
    </div>
  );
}

export default App;
