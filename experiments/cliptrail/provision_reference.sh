#!/usr/bin/env bash
# Run from a normal network-capable WSL/Linux terminal. No sudo/global installs.
set -euo pipefail
cliptrail_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$cliptrail_root"
export UV_CACHE_DIR="$cliptrail_root/.cache/cliptrail-uv"
export HF_HOME="$cliptrail_root/.cache/cliptrail-hf"
cliptrail_venv="$cliptrail_root/.venv-cliptrail"
if ! command -v uv >/dev/null 2>&1; then
  echo 'uv is required for this provisioning script; no system software was changed.' >&2
  exit 2
fi
if [[ ! -x "$cliptrail_venv/bin/python" ]]; then
  uv venv --python 3.12 "$cliptrail_venv"
fi
uv pip install --python "$cliptrail_venv/bin/python" --index-url https://download.pytorch.org/whl/cpu 'torch==2.8.0'
uv pip install --python "$cliptrail_venv/bin/python" -r experiments/cliptrail/requirements-reference.txt
"$cliptrail_venv/bin/python" experiments/cliptrail/provision_assets.py
"$cliptrail_venv/bin/python" -m pip --version >/dev/null 2>&1 && \
  "$cliptrail_venv/bin/python" -m pip freeze > experiments/cliptrail/results/reference-freeze.txt || \
  uv pip freeze --python "$cliptrail_venv/bin/python" > experiments/cliptrail/results/reference-freeze.txt
echo 'ClipTrail reference provisioning finished. No benchmark or Snapdragon claim has been made.'
