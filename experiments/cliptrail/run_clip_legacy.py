#!/usr/bin/env python3
"""Real OpenAI CLIP CPU embedding proof; requires local weights and images."""
import argparse,hashlib,importlib.util,json,platform,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--weights',type=Path);p.add_argument('--images',type=Path)
    p.add_argument('--query',default='a red connector beside a circuit board')
    p.add_argument('--output',type=Path,default=Path(__file__).parent/'results/clip-cpu.json');a=p.parse_args()
    result=dict(inference_performed=False,status='not_started',model='OpenAI CLIP ViT-B/16',host=platform.platform(),python=platform.python_version())
    try:
        if any(importlib.util.find_spec(x) is None for x in ('torch','clip','PIL')):
            raise RuntimeError('Required torch, OpenAI clip and Pillow packages unavailable. No inference performed.')
        if not a.weights or not a.weights.is_file() or not a.images or not a.images.is_dir():
            raise RuntimeError('Explicit local ViT-B/16 weights and PNG directory required; downloads disabled.')
        import torch,clip
        from PIL import Image
        paths=sorted(a.images.glob('*.png'))
        if not paths:raise RuntimeError('No PNG images supplied')
        start=time.perf_counter();model,preprocess=clip.load(str(a.weights),device='cpu',jit=False)
        if not hasattr(model.visual,'transformer') or tuple(model.visual.conv1.kernel_size)!=(16,16) or model.visual.conv1.out_channels!=768 or len(model.visual.transformer.resblocks)!=12:
            raise RuntimeError('Local checkpoint architecture does not match expected ViT-B/16 image tower.')
        model.eval();result['init_ms']=(time.perf_counter()-start)*1000
        rows=[]
        with torch.inference_mode():
            text=model.encode_text(clip.tokenize([a.query]));text=text/text.norm(dim=-1,keepdim=True)
            for path in paths:
                with Image.open(path) as im:batch=preprocess(im).unsqueeze(0)
                start=time.perf_counter();v=model.encode_image(batch);v=v/v.norm(dim=-1,keepdim=True)
                rows.append(dict(file=path.name,encode_ms=(time.perf_counter()-start)*1000,cosine=float((v@text.T).item()),embedding=v[0].tolist()))
        result.update(status='completed',inference_performed=True,provenance='MEASURED local CPU CLIP; no NPU claim',query=a.query,outputs=rows,
                      weights_sha256=hashlib.file_digest(a.weights.open('rb'),'sha256').hexdigest())
    except Exception as exc:result.update(status='blocked_or_failed',error=f'{type(exc).__name__}: {exc}')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='outputs'},indent=2))
    return 0 if result['inference_performed'] else 2
if __name__=='__main__':raise SystemExit(main())
