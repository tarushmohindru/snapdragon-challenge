#!/usr/bin/env python3
"""Real embedding smoke proof using the same CPU adapter as the kill gate."""
import argparse
import json
from pathlib import Path
from reference_backend import ClipReference, cosine


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model-dir', type=Path, default=Path(__file__).parent / 'assets/model')
    p.add_argument('--provisioning', type=Path, default=Path(__file__).parent / 'results/provisioning.json')
    p.add_argument('--images', type=Path, required=True)
    p.add_argument('--query', default='a person standing outdoors')
    p.add_argument('--output', type=Path, default=Path(__file__).parent / 'results/clip-cpu.json')
    p.add_argument('--threads', type=int, default=2)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Output exists; choose another path to preserve earlier evidence')
    result = {'inference_performed': False, 'status': 'not_started', 'npu_verified': False, 'outputs': []}
    try:
        paths = sorted(p for p in a.images.iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg'))
        if not paths:
            raise ValueError('No local images provided')
        model = ClipReference(a.model_dir, a.provisioning, a.threads)
        model.warmup(paths[0])
        text, text_cost = model.encode_text(a.query)
        result.update(model=model.metadata, text_embedding=text, text_cost=text_cost, query=a.query)
        for path in paths:
            vector, cost = model.encode_image(path)
            result['outputs'].append({'file': str(path), 'embedding': vector, 'cosine': cosine(vector, text), 'cost': cost})
            result['inference_performed'] = True
        result.update(status='completed', provenance='MEASURED local CPU CLIP; no NPU claim')
    except Exception as exc:
        result.update(status='blocked_or_failed', error=f'{type(exc).__name__}: {exc}')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({k: v for k, v in result.items() if k not in ('outputs', 'text_embedding', 'model')}, indent=2))
    return 0 if result['status'] == 'completed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
