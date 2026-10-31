# NeuroHeist / NeuroLens

NeuroLens is an open-source MRI visualization demo: upload a NIfTI scan, run local tumor segmentation, inspect the mask in the existing viewer, and explore an educational scenario grounded in retrieved research. The repository and existing deployment URLs retain the NeuroHeist name.

The project is published under the [MIT license](LICENSE). It is an educational prototype, not a diagnostic tool or a patient-specific treatment predictor.

## Live demo for RowdyLaunch

[Open the tested NeuroLens demo](https://arrangement-dim-electron-college.trycloudflare.com).

Download the [four-channel sample MRI](https://raw.githubusercontent.com/steawinfdox-png/neuroheist/main/samples/BRATS_457.nii.gz), upload it, and explore the scan and mask. The smaller [3D compatibility sample](https://raw.githubusercontent.com/steawinfdox-png/neuroheist/main/samples/BRATS_457_3D.nii.gz) also works. Select **Stereotactic radiosurgery** for the verified research example. Use **Enter fullscreen** to enlarge the viewer and controls; use **Exit fullscreen** or Escape to return.

This temporary HTTPS link reaches the app running on the presenting Mac. Keep that Mac plugged in, lid open, and its launcher running through review. A tunnel restart changes the link. The Gemma API itself remains local.

## Models and research workflow

- **MRI segmentation:** the existing MONAI `SegResNet` BraTS model runs locally with PyTorch. Its architecture and checkpoint are unchanged by this Mac setup.
- **Research interpretation:** **Google Gemma 4 E4B**, selected as **`gemma4:e4b`**, runs locally through **Ollama 0.40.13**. Gemma extracts quantitative evidence from research excerpts, then selects a supported observation for the visualization. It is central to this workflow, rather than an unrelated chat interface.
- **Research retrieval:** Tavily remains the preferred search service when `TAVILY_API_KEY` is configured. Otherwise, the backend retrieves public PubMed abstracts through NCBI EUtils without an API key. Retrieval requires internet access; inference runs on this Mac. The result identifies its retrieval provider and source links.

No Groq or Gemini API key is needed for the local workflow. The compatibility function in `backend/gemini_call.py` now calls local Gemma; its historical filename is preserved.

The backend checks exact source quotes and reported percentages, or a pair of baseline and follow-up tumor volumes in the same units. For paired volumes, Python calculates the relative change. It allows zero and refuses to invent a percentage when suitable quantitative tumor-volume evidence is missing. A reported study observation is not a prediction for the uploaded scan, and the geometric mask transformation is illustrative. Some treatment queries will correctly return an insufficient-evidence error.

## Run locally on a Mac

Use an Apple Silicon Mac with sufficient free memory and disk space for the model download. This setup uses Node.js 24, Python 3.12, and Ollama 0.40.13. Install them from their official sources: [Node.js](https://nodejs.org/), [Python](https://www.python.org/downloads/macos/), and [Ollama](https://ollama.com/download/mac). See [Ollama's macOS instructions](https://docs.ollama.com/macos).

Clone the repository and install both sets of frontend dependencies:

```bash
git clone https://github.com/steawinfdox-png/neuroheist.git
cd neuroheist
npm ci
npm ci --prefix neuroheist
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

The example settings select the local model and loopback API. Add a Tavily key only if you want that optional search provider. Keep `.env` and model weights out of Git.

In a separate Terminal, start the local model server. If the Ollama app is already running, use its existing server instead of starting a second one.

```bash
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_NO_CLOUD=1 ollama serve
```

Back in the repository Terminal, download the exact model and start the combined website/API:

```bash
ollama pull gemma4:e4b
./scripts/start_local.sh
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Keep the model server and app running. The startup script builds the frontend with a same-origin API URL and serves it with FastAPI. It supports macOS `shasum` and Linux `sha256sum` for checkpoint verification.

When `backend/brats_mri_segmentation.pth` is absent and `MODEL_URL` is unset, the script downloads the [MONAI BraTS checkpoint](https://github.com/Project-MONAI/model-zoo/blob/dev/models/brats_mri_segmentation/large_files.yml) and verifies its SHA-256 digest. A custom checkpoint must match `backend/model.py`. Model weights are not committed.

### Sample scans and verification

Prefer the supplied four-channel scan [`samples/BRATS_457.nii.gz`](samples/BRATS_457.nii.gz), which matches the four-modality input expected by the [original MONAI model](https://github.com/Project-MONAI/model-zoo/blob/dev/models/brats_mri_segmentation/configs/metadata.json). The compatibility sample [`samples/BRATS_457_3D.nii.gz`](samples/BRATS_457_3D.nii.gz) is also accepted; a single volume is copied into all four input channels, and those predictions have not been clinically validated.

The local inference shape is `64,128,128` by default. The existing lower-memory hosted configuration defaults to `32,64,64`.

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:11434/api/tags
curl --fail -F file=@samples/BRATS_457.nii.gz http://127.0.0.1:8000/upload
curl --fail -H 'Content-Type: application/json' \
  -d '{"treatment":"bevacizumab"}' http://127.0.0.1:8000/simulate
```

Upload a sample before requesting a scenario. Confirm the upload returns a `tumor_mask` URL and that the viewer loads the scan and mask. The research endpoint may return an evidence error for a query; a successful health check does not prove research retrieval or model inference works. For a supported scenario, verify the response identifies the local model and contains research sources. Never substitute a made-up outcome to pass a demo.

The existing API routes remain `/health`, `/upload`, `/tumor-mask/{filename}`, and `/simulate`. Successful simulation responses retain `treatment`, `reductionPercent`, `summary`, and `maskUrl`, and add model/source metadata. Model values are parsed as validated JSON rather than by extracting the first number from arbitrary text.

### Edit the UI locally

Keep the backend running, then start Vite from another Terminal:

```bash
cd neuroheist
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1
```

Edit `neuroheist/src` from the repository root and open [http://127.0.0.1:5173](http://127.0.0.1:5173). The public combined app uses the last production build. From the repository root, run `VITE_API_BASE_URL=/ npm --prefix neuroheist run build` after UI changes, then refresh the public app. This preserves the running backend, tunnel, and public URL.

## Temporary public hosting from this Mac

Install [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) and, while the app is running, start a quick tunnel:

```bash
cloudflared tunnel --protocol http2 --url http://127.0.0.1:8000
```

Share the HTTPS `trycloudflare.com` URL printed by that command. Check its `/health` endpoint and test a sample upload through the public site. The model server stays bound to loopback; only the combined app is tunneled.

Keep the Mac plugged in, its lid open, and all server/tunnel processes running throughout review. In another Terminal, prevent idle sleep:

```bash
caffeinate -i
```

The quick-tunnel URL changes after a restart and stops working when the tunnel, app, or Mac stops. This is temporary Mac hosting. The existing domain and earlier deployment have **not** been migrated to this Mac, and credentials/configuration from the earlier Linux machine are not needed for a quick tunnel.

## Verified work and remaining submission steps

Verified on this Apple M5 Pro Mac with 48 GB memory on October 31, 2026:

- Both supplied 3D and four-channel scans segmented successfully; masks preserve input dimensions and alignment and contain nonzero labels.
- The public link passed a four-channel upload, a real local Gemma scenario with a cited PubMed source, and mask download. The scenario mask has fewer labeled voxels than the original.
- `gemma4:e4b` runs through the MLX runner with Ollama reporting **100% GPU**. Installed model digest: `eb2177adf7646d15faead94fdad6d3e170dc8015653418a3b7d5d52a6380be5b`.
- The public browser demo visibly rendered the scan and tumor mask. Layer controls, fullscreen entry, Escape exit, and the exit button passed.
- The frontend production build and lint completed. Existing nonblocking bundle-size and unused-prop warnings remain.
- Mac-compatible model-checksum verification, a settings example, and secret/runtime ignore rules are included. The obsolete `transfer` handoff file was removed.
- [CONTRIBUTING.md](CONTRIBUTING.md) provides a finished beginner lab. Its paths and commands were checked; an outside-newcomer pilot has not been completed.

The presenting Mac also has Start, Stop, Edit UI, and Update Demo `.command` launchers in the setup chat's outputs folder. Start manages Ollama, the app, the public HTTP/2 tunnel, and idle-sleep prevention. Run Start from a normal Mac Terminal: the Codex execution sandbox cannot access Metal, even though the normal Terminal session can. Use the generic setup instructions above on another computer.

Before submitting, fill in the registered team identities and LinkedIn links, recheck the public URL, and have each teammate submit under the same team name before **4:00 PM Central on October 31, 2026**. Keep the repository public through judging and the Mac online. A short recording is a useful backup; no recording is claimed here.

Next UI work can use Vite at port 5173 with the backend still running. Run the Update Demo launcher, or the production-build command above, to publish frontend changes without restarting the tunnel. Refresh the public page to load the new build. A full demo-launcher restart changes the temporary URL, so update submission links if you restart it.

## RowdyLaunch submission and contributions

Target tracks under the [RowdyLaunch guide](https://rowdylaunch.vercel.app/guide):

- **MLH Best Open-Source AI Project (Gemma 4)**: the local Gemma research workflow.
- **OSPO at UT San Antonio Open Source Education**: the reusable [first-contribution lab](CONTRIBUTING.md) for non-CS and health-science students. Its success measures are tutorial completion and a first useful PR; no pilot results are claimed.
- **Best Overall**: automatic consideration for every submission.

NeuroLens does not claim a truck-driver use case for the Life Behind the Wheel track.

This setup reuses the existing MRI model, viewer, and backend. Work added for the current Mac setup includes Mac-compatible startup, replacement of the cloud LLM stages with local Gemma 4, keyless PubMed retrieval alongside optional Tavily, validated JSON handling, source-grounded evidence checks, fullscreen controls, and a beginner contribution lab. Credit the original work through repository history and identify today's changes clearly in the submission.

The NeuroLens team and original repository contributors built the project; individual contribution history is retained in Git. Submission participant names should match the event registration.

Gemma's useful contribution is making research excerpts actionable and inspectable within the existing scan workflow while keeping LLM inference local. Contributors can improve evidence retrieval/validation, add useful documentation and reproducible tests, or improve the viewer. Keep changes focused, test them with the supplied samples, and explain the validation in a pull request.
