# Deployment status

The working submission path is the local CPU application described in the [root README](../../README.md). Provision it with `experiments/cliptrail/provision_reference.sh` and run `.venv-cliptrail/bin/python -m cliptrail_app serve`.

The optional QNN backend is an experimental integration path, not a deployment claim. One fixed CLIP image graph completed native ARM64 ONNX Runtime QNN execution on an ASUS Snapdragon X2 Elite with the issued HTP backend loaded and passing embedding parity. Hardware device events were not captured, and the process later exited abnormally. See the [full adjudication](../planning/cliptrail-deployment-outcome-v2.md).

No physical NPU verification, acceleration, power result, HP compatibility, target full-application run, installer, or production-stability claim is made.
