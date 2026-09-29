# Third-party notices

This file summarizes third-party material used or referenced by ClipTrail. It does not replace the authoritative upstream license files or terms.

## OpenAI CLIP

ClipTrail uses the public OpenAI CLIP ViT-B/16 model architecture/checkpoint through Transformers. The retained OpenAI CLIP license is the MIT License, copyright 2021 OpenAI. See [`third_party_licenses/OPENAI_CLIP_MIT.txt`](third_party_licenses/OPENAI_CLIP_MIT.txt).

Model weights are downloaded during local provisioning and are excluded from the public repository. Users remain responsible for the terms attached to the checkpoint and the software used to load it.

## Python libraries

The CPU reference uses PyTorch, Transformers, Hugging Face Hub, NumPy, Pillow, and PyAV. Exact versions are recorded in [`experiments/cliptrail/results/reference-freeze.txt`](experiments/cliptrail/results/reference-freeze.txt). These packages are installed from their upstream distributions and are not vendored here. Their respective upstream licenses apply.

## Reference videos

The frozen benchmark uses locally downloaded material from the Blender Foundation’s *Sintel* and *Tears of Steel* projects. The provisioning record declares CC BY 3.0 and records the creator/source attribution. Source videos are excluded from the public repository and are used for local evaluation. See [`experiments/cliptrail/results/provisioning.json`](experiments/cliptrail/results/provisioning.json) and [`experiments/cliptrail/datasets/windows-v1.json`](experiments/cliptrail/datasets/windows-v1.json).

The pitch, demo poster, and optional demo video show credited *Sintel* frames. The optional demo uses [*Happy Beats & Business Moves Vol. 12* by Sascha Ende](https://ende.app/en/song/12881-happy-beats-business-moves-vol-12) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The track was trimmed and mixed beneath narration. See [`final_submission/demo/credits.md`](final_submission/demo/credits.md) for the delivered video's credits. The video is a separate local upload artifact and is not included in the Git tree.

## Qualcomm and ONNX Runtime QNN material

The experimental Windows ARM64 path used an ONNX Runtime QNN distribution and Qualcomm AI Stack runtime files. Native packages, DLLs, wheels, and assembled bundles are excluded from the public repository. The locally retained Qualcomm terms state that the software may not be redistributed standalone; consult the authoritative license before using or distributing any runtime component. The working archive retains the original PDF and an explicitly approximate extracted text copy under `experiments/cliptrail_target/results/`.

Returned logs, hashes, small numeric outputs, and audit records document the target smoke; they are evidence rather than runtime redistribution.

## Project code license

The participant selected MIT for original ClipTrail code. See the root [`LICENSE`](LICENSE). That license does not replace or override any model, media, library, or runtime terms above.
