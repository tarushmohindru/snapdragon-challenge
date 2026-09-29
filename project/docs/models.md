# Model and backend status

ClipTrail uses OpenAI CLIP ViT-B/16 with normalized 512-dimensional image and text embeddings.

- **Verified application backend:** pinned Transformers/PyTorch CPU reference. Model revision and dependency versions are recorded under `experiments/cliptrail/`.
- **Experimental backend:** an extracted CLIP image graph through ONNX Runtime QNN on compatible native Windows ARM64, with the text tower still on CPU.

Backend identity is stored with each index so incompatible vectors cannot mix. The QNN smoke established provider-level execution, HTP loading, partitioning, and one-image embedding parity. It did not verify physical NPU execution, speed, energy, production stability, or full application behavior on target.

Weights and runtime packages are downloaded locally and excluded from the public repository. Their upstream licenses and distribution terms continue to apply.
