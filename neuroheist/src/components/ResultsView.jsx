import { useState } from "react";
import BrainViewer from "./BrainViewer";
import LayerControls from "./LayerControls";
import TreatmentPanel from "./TreatmentPanel";
import "./ResultsView.css";

export default function ResultsView({ result, file, onNewScan, onCompare }) {
  // Holds { reductionPercent, summary, sources } after a treatment is simulated
  const [treatmentResult, setTreatmentResult] = useState(null);

  // Visibility + opacity for each 3D layer (controlled from the Layers panel)
  const [layers, setLayers] = useState({
    brain: { visible: true, opacity: 1 },
    tumor: { visible: true, opacity: 0.85 },
  });

  return (
    <div className="results">
      <header className="results__header">
        <h1>Scan results</h1>

        <div className="results__header-actions">
          <button
            className="upload__button"
            onClick={onCompare}
          >
            Compare Treatments
          </button>

          <button
            className="upload__button"
            onClick={onNewScan}
          >
            New scan
          </button>
        </div>
      </header>

      <div className="results__grid">
        {/* Left column: layer toggles + opacity sliders */}
        <aside className="glass results__controls">
          <LayerControls
            layers={layers}
            onChange={setLayers}
            hasTumor={Boolean(result?.maskUrl)}
          />
        </aside>

        {/* Center column: the 3D viewer */}
        <div className="glass results__viewer">
          {/* reductionPercent isn't used by the viewer yet; it's for the shrink slider later */}
          <BrainViewer
            file={file}
            maskUrl={
              treatmentResult?.maskUrl ||
              result?.maskUrl
            }
            reductionPercent={treatmentResult?.reductionPercent}
            brainOpacity={layers.brain.visible ? layers.brain.opacity : 0}
            tumorOpacity={layers.tumor.visible ? layers.tumor.opacity : 0}
          />
        </div>

        {/* Right column: stats on top, treatment simulation below */}
        <div className="results__side">
          <section className="glass results__stats">
            <h2>Findings</h2>
            {/* Temporary: shows the raw backend data so you can see its shape */}
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </section>

          <section className="glass results__chat">
            <TreatmentPanel scanResult={result} onResult={setTreatmentResult} />
          </section>
        </div>
      </div>
    </div>
  );
}