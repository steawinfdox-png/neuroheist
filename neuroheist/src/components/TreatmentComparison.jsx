
import { useEffect, useState } from "react";
import BrainViewer from "./BrainViewer";
import "./TreatmentComparison.css";

const API_URL = "http://localhost:8000";

function TreatmentComparison({ file, onBack }) {
  const [masks, setMasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchMasks() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(`${API_URL}/treatment-masks`);
        const data = await response.json();

        if (!response.ok) {
          throw new Error("Couldn't retrieve treatment masks.");
        }

        setMasks(
          data.masks.map((mask) => ({
            ...mask,
            maskUrl: `${API_URL}${mask.maskUrl}`,
          }))
        );
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchMasks();
  }, []);

  return (
    <div className="treatment-comparison">
      <header className="treatment-comparison__header">
        <button onClick={onBack}>
          Back to Results
        </button>

        <h1>Treatment Comparison</h1>
        <p>Compare your simulated treatment outcomes in 3D.</p>
      </header>

      {loading ? (
        <p>Loading treatment simulations...</p>
      ) : error ? (
        <p>{error}</p>
      ) : masks.length === 0 ? (
        <div className="treatment-comparison__empty">
          <h2>You haven't simulated anything yet!</h2>
          <p>Run a treatment simulation to see its 3D visualization here.</p>
        </div>
      ) : (
        <div className="treatment-comparison__grid">
          {masks.map((mask) => (
            <div
              className="glass treatment-comparison__card"
              key={mask.filename}
            >
              <h2>{mask.treatment}</h2>

              <BrainViewer
                file={file}
                maskUrl={mask.maskUrl}
                brainOpacity={1}
                tumorOpacity={0.85}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TreatmentComparison;
