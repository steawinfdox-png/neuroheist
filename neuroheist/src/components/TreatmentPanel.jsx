import { apiUrl } from "../api";
import { useEffect, useState } from "react";
import "./TreatmentPanel.css";

const API_URL = apiUrl("/simulate");

const USE_MOCK = false; // set to false once the backend endpoint is running

const TREATMENTS = [
  {
    id: "3D-CRT",
    name: "3D-CRT",
    description: "Several beams shaped to match the tumor's 3D outline, given daily over several weeks.",
  },
  {
    id: "IMRT",
    name: "Intensity-modulated radiation therapy",
    description: "Varies the strength within each beam to fit the tumor closely and spare nearby tissue.",
  },
  {
    id: "Photon beams",
    name: "Proton therapy",
    description: "Protons release most of their energy at the tumor, sparing tissue behind it.",
  },
  {
    id: "SRS",
    name: "Stereotactic radiosurgery ",
    description: "A very precise, high dose aimed at a small tumor in 1–5 sessions. No incision despite the name.",
  },
  {
    id: "RT",
    name: "Radiotherapy",
    description: "Treats the entire brain, usually for multiple tumors, given daily over 1–3 weeks.",
  }
];

// Cosmetic: the backend doesn't report progress, so these just cycle on a timer
const LOADING_STEPS = [
  "Searching medical research…",
  "Summarizing findings…",
  "Predicting outcome…",
];

// Pretends to be the backend. The real response should have this same shape.
function fakeSimulate(treatment) {
  return new Promise((resolve) =>
    setTimeout(
      () =>
        resolve({
          reductionPercent: 38,
          summary: `Mock summary for ${treatment.name}. The real summary from the backend will appear here.`,
          sources: [{ title: "Example source (mock data)", url: "https://example.com" }],
        }),
      4000
    )
  );
}

export default function TreatmentPanel({ scanResult, onResult }) {
  const [selectedId, setSelectedId] = useState(null);
  const [status, setStatus] = useState("choosing"); // choosing | simulating | result | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [stepIndex, setStepIndex] = useState(0);

  const selected = TREATMENTS.find((t) => t.id === selectedId);

  // Advance the loading text every 2.5s while simulating
  useEffect(() => {
    if (status !== "simulating") return;
    const timer = setInterval(() => {
      setStepIndex((i) => Math.min(i + 1, LOADING_STEPS.length - 1));
    }, 2500);
    return () => clearInterval(timer); // stop the timer when simulating ends
  }, [status]);

  async function handleSimulate() {
    if (!selected) return;

    setStatus("simulating");
    setStepIndex(0);
    setError("");

    try {
      let data;

      if (USE_MOCK) {
        data = await fakeSimulate(selected);
      } else {
        const response = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ treatment: selected.name }),
        });
        if (!response.ok) {
          throw new Error(`The server responded with status ${response.status}.`);
        }
        data = await response.json();
        if(data.error){
          throw new Error(data.error);
        }
        if (data.maskUrl && data.maskUrl.startsWith("/")) {
          data.maskUrl = apiUrl(data.maskUrl);
        }
      }

      setResult(data);
      setStatus("result");
      onResult?.(data); // lets ResultsView pass reductionPercent to the 3D viewer later
    } catch (err) {
      setStatus("error");
      setError(
        err instanceof TypeError
          ? "Couldn't reach the server. Check that the backend is running, then try again."
          : err.message
      );
    }
  }

  function handleReset() {
    setStatus("choosing");
    setResult(null);
    onResult?.(null);
  }

  return (
    <div className="treatment">
      <h2>Treatment simulation</h2>

      {/* Choosing (also shown after an error so the user can retry) */}
      {(status === "choosing" || status === "error") && (
        <>
          <div className="treatment__options">
            {TREATMENTS.map((t) => (
              <button
                key={t.id}
                type="button"
                className={`treatment__option${t.id === selectedId ? " is-selected" : ""}`}
                aria-pressed={t.id === selectedId}
                onClick={() => setSelectedId(t.id)}
              >
                <span className="treatment__name">{t.name}</span>
                <span className="treatment__description">{t.description}</span>
              </button>
            ))}
          </div>

          {status === "error" && (
            <p className="treatment__error" role="alert">
              {error}
            </p>
          )}

          <button
            className="upload__button treatment__simulate"
            onClick={handleSimulate}
            disabled={!selected}
          >
            Simulate treatment
          </button>
        </>
      )}

      {/* Simulating */}
      {status === "simulating" && (
        <div className="treatment__loading" aria-live="polite">
          <div className="treatment__spinner" />
          <p>{LOADING_STEPS[stepIndex]}</p>
          <p className="treatment__muted">{selected.name}</p>
        </div>
      )}

      {/* Result */}
      {status === "result" && result && (
        <div className="treatment__result">
          <p className="treatment__muted">{selected.name}</p>
          <p className="treatment__reduction">−{Math.round(result.reductionPercent)}%</p>
          <p className="treatment__muted">predicted tumor volume reduction</p>

          <p className="treatment__summary">{result.summary}</p>

          {result.sources?.length > 0 && (
            <>
              <h3 className="treatment__label">Sources</h3>
              <ul className="treatment__sources">
                {result.sources.map((source) => (
                  <li key={source.url}>
                    <a href={source.url} target="_blank" rel="noopener noreferrer">
                      {source.title}
                    </a>
                  </li>
                ))}
              </ul>
            </>
          )}

          <button className="treatment__secondary" onClick={handleReset}>
            Try another treatment
          </button>
        </div>
      )}

      <p className="treatment__disclaimer">
        Illustrative estimate based on published research. Not medical advice.
      </p>
    </div>
  );
}
