#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
model_path="$repo_dir/backend/brats_mri_segmentation.pth"
python_bin="$repo_dir/backend/.venv/bin/python"

if [[ ! -x "$python_bin" ]]; then
  echo "Missing backend Python environment. Run: python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt" >&2
  exit 1
fi

if [[ ! -f "$model_path" && -z "${MODEL_URL:-}" ]]; then
  model_url="https://developer.download.nvidia.com/assets/Clara/monai/tutorials/model_zoo/model_brats_mri_segmentation.pt"
  model_sha256="860ccb3f1c21c99d0410ad8a1ac4ef6b8fab60cec0a503b0ba42675741a750ae"
  download_path="$(mktemp "$repo_dir/backend/.model-download.XXXXXX")"
  trap 'rm -f "$download_path"' EXIT
  echo "Downloading MONAI BraTS model checkpoint..."
  curl -fL --retry 2 --output "$download_path" "$model_url"
  printf '%s  %s\n' "$model_sha256" "$download_path" | sha256sum --check --status
  mv "$download_path" "$model_path"
  trap - EXIT
fi

(cd "$repo_dir/neuroheist" && VITE_API_BASE_URL=/ npm run build)
cd "$repo_dir/backend"
export INFERENCE_SHAPE="${INFERENCE_SHAPE:-64,128,128}"
exec "$python_bin" -m uvicorn main:app --host 127.0.0.1 --port "${PORT:-8000}"
