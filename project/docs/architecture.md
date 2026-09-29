# Architecture

The canonical public architecture and diagram are in [`docs/architecture.md`](../../docs/architecture.md). The detailed frozen application record remains in [`cliptrail-application-architecture.md`](cliptrail-application-architecture.md).

ClipTrail is a local video/folder indexing and semantic retrieval application backed by SQLite. The verified application path uses CPU CLIP. The optional Windows ARM64/QNN image backend is experimental: native provider-level graph execution, HTP loading, partitioning, and embedding parity were observed, while physical NPU execution was not verified.
