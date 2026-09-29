#!/usr/bin/env bash
# Run in the participant's network-capable WSL terminal. No sudo/global installs.
set -euo pipefail
cliptrail_target_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$cliptrail_target_root"
export UV_CACHE_DIR="$cliptrail_target_root/.cache/cliptrail-target-uv"
cliptrail_target_python="$cliptrail_target_root/.venv-cliptrail-target-tools/bin/python"
if [[ ! -x "$cliptrail_target_python" ]]; then
  uv venv --python "$cliptrail_target_root/.venv-cliptrail/bin/python" --seed "$cliptrail_target_root/.venv-cliptrail-target-tools"
fi
uv pip install --python "$cliptrail_target_python" qai_hub_models_cli onnx onnxruntime 'numpy==2.3.3' 'Pillow==11.3.0'
"$cliptrail_target_python" -m pip freeze > experiments/cliptrail_target/tooling-freeze.txt
"$cliptrail_target_python" experiments/cliptrail_target/provision_assets.py
echo 'Target assets/metadata provisioning finished. Read results/provisioning.json for successes and blockers.'
echo 'This does not run on the Snapdragon, establish HTP execution, or start the systems benchmark.'
