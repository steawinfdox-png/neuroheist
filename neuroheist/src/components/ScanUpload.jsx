import { apiUrl } from "../api";
import { useRef, useState } from "react";

/*
  ScanUpload — pick or drag in an MRI scan, validate it, and send it to the backend.

  Usage in App.jsx:
    import ScanUpload from "./components/ScanUpload";
    <ScanUpload onResult={(data) => console.log("Backend returned:", data)} />

  No styles included: every element has a className so you can style it yourself.
*/

// ---- Config: change these to match your backend ----
const API_URL = apiUrl("/upload");
const FIELD_NAME = "file"; // must match the field name the backend reads
const ACCEPTED_EXTENSIONS = [".nii", ".nii.gz"];
const MAX_SIZE_MB = 200;
const USE_MOCK = false; // set to false once the backend endpoint is running

function hasValidExtension(name) {
  const lower = name.toLowerCase();
  // endsWith handles double extensions like ".nii.gz"
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Pretends to be the backend so you can build the flow before it's ready
function fakeUpload() {
  return new Promise((resolve) =>
    setTimeout(
      () =>
        resolve({
          message: "Mock result",
          regions: [],
          maskUrl: "/fake_tumor_mask.nii.gz", 
        }),
      2000
    )
  );
}

export default function ScanUpload({ onResult }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | uploading | done | error
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  const isUploading = status === "uploading";

  // Shared by the file picker and drag-and-drop
  function selectFile(candidate) {
    if (!candidate) return;

    if (!hasValidExtension(candidate.name)) {
      setFile(null);
      setError(`Unsupported file type. Upload a ${ACCEPTED_EXTENSIONS.join(" or ")} scan.`);
      return;
    }
    if (candidate.size > MAX_SIZE_MB * 1024 * 1024) {
      setFile(null);
      setError(`File is too large. The limit is ${MAX_SIZE_MB} MB.`);
      return;
    }

    setFile(candidate);
    setError("");
    setStatus("idle");
  }

  function handleInputChange(event) {
    selectFile(event.target.files[0]);
    event.target.value = ""; // lets you re-pick the same file after an error
  }

  function openPicker() {
    if (!isUploading) inputRef.current.click();
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openPicker();
    }
  }

  function handleDragOver(event) {
    event.preventDefault(); // without this, the drop event never fires
    if (!isUploading) setIsDragging(true);
  }

  function handleDragLeave() {
    setIsDragging(false);
  }

  function handleDrop(event) {
    event.preventDefault(); // stops the browser from opening the file
    setIsDragging(false);
    if (!isUploading) selectFile(event.dataTransfer.files[0]);
  }

  async function handleUpload() {
    if (!file || isUploading) return;

    setStatus("uploading");
    setError("");

    try {
      let result;

      if (USE_MOCK) {
        result = await fakeUpload();
      } else {
        const formData = new FormData();
        formData.append(FIELD_NAME, file);

        // Don't set Content-Type: the browser adds the correct multipart header
        const response = await fetch(API_URL, { method: "POST", body: formData });
        const responseText = await response.text();
        let responseData;
        try {
          responseData = JSON.parse(responseText);
        } catch {
          throw new Error(`The server returned an invalid response (status ${response.status}).`);
        }
        if (!response.ok || responseData.error) {
          throw new Error(responseData.error || `The server rejected the upload (status ${response.status}).`);
        }
        result = responseData;
        result.maskUrl = apiUrl(result.tumor_mask);
      }

      setStatus("done");
      onResult?.(result, file);
    } catch (err) {
      setStatus("error");
      // A network failure can have several causes, including a sleeping backend.
      setError(
        err instanceof TypeError
          ? "Couldn't reach the server. Check that the backend is running, then try again."
          : err.message
      );
    }
  }

  return (
    <div className="upload">
      <div
        className={`upload__dropzone${isDragging ? " is-dragging" : ""}${isUploading ? " is-disabled" : ""}`}
        role="button"
        tabIndex={0}
        aria-disabled={isUploading}
        onClick={openPicker}
        onKeyDown={handleKeyDown}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <p className="upload__prompt">
          {isDragging ? "Drop the scan here" : "Drag an MRI scan here, or click to choose a file"}
        </p>
        <p className="upload__hint">Accepted: {ACCEPTED_EXTENSIONS.join(", ")} up to {MAX_SIZE_MB} MB. Use a 4D MRI with four channels; tumor masks are not scans.</p>
      </div>

      <input className = "upload__input"
        ref={inputRef}
        type="file"
        accept=".nii,.gz"
        onChange={handleInputChange}
        hidden
      />

      {file && (
        <p className="upload__file">
          {file.name} ({formatSize(file.size)})
        </p>
      )}

      {error && (
        <p className="upload__error" role="alert">
          {error}
        </p>
      )}

      <button 
        className="upload__button"
        onClick={handleUpload}
        disabled={!file || isUploading}
      >
        {isUploading ? "Analyzing scan…" : "Analyze scan"}
      </button>

      {status === "done" && <p className="upload__success">Scan analyzed.</p>}
    </div>
  );
}
