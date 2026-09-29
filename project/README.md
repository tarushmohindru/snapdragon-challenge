# ClipTrail engineering archive

The public product entry point is the [root README](../README.md). Canonical submission documentation is under [`docs/`](../docs/) and [`submission/`](../submission/).

This `project/` directory preserves the engineering record that led to the feature-frozen ClipTrail application. It includes predeclared benchmark protocols, selection decisions, research snapshots, target evidence adjudication, and dated negative results. Those records support auditability; they are not the primary product narrative.

## Current canonical records

- [Product architecture](../docs/architecture.md)
- [Benchmark and evidence summary](../docs/evidence.md)
- [Detailed frozen application architecture](docs/cliptrail-application-architecture.md)
- [QNN target evidence adjudication](planning/cliptrail-deployment-outcome-v2.md)
- [Final submission checklist](../submission/checklist.md)

The working application uses CPU CLIP. The experimental Windows ARM64/QNN path has provider-level execution, HTP loading, partitioning, and embedding-parity evidence. Physical NPU execution, acceleration, energy benefit, HP deployment, and full target application behavior remain unverified.
