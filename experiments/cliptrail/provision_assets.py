#!/usr/bin/env python3
"""Provision public reference assets explicitly; inference itself stays offline.

Original Blender videos are downloaded for local evaluation, not redistributed.
Download availability and bytes/hashes are recorded, never assumed from a URL.
"""
import argparse,hashlib,json,platform,sys,time,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MODEL=ROOT/'assets/model'
MODEL_REVISION='57c216476eefef5ab752ec549e440a49ae4ae5f3'
VIDEOS=[
    {'id':'sintel_trailer','url':'https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4',
     'filename':'sintel_trailer-480p.mp4','source':'https://durian.blender.org/',
     'creator':'Blender Foundation / Sintel team','declared_license':'CC BY 3.0; verify source attribution before redistribution'},
    {'id':'tears_of_steel','url':'https://download.blender.org/demo/movies/ToS/tears_of_steel_720p.mov',
     'filename':'tears_of_steel_720p.mov','source':'https://mango.blender.org/',
     'creator':'Blender Foundation / Tears of Steel team','declared_license':'CC BY 3.0; verify source attribution before redistribution'},
]

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--model-only',action='store_true');a=p.parse_args()
    (ROOT/'results').mkdir(exist_ok=True);MODEL.mkdir(parents=True,exist_ok=True)
    report={'schema':1,'status':'running','python':platform.python_version(),'model':{},'videos':[],'errors':[]}
    def save(): (ROOT/'results/provisioning.json').write_text(json.dumps(report,indent=2))
    save()
    try:
        from huggingface_hub import HfApi,snapshot_download
        api=HfApi();info=api.model_info('openai/clip-vit-base-patch16',revision=MODEL_REVISION)
        names={x.rfilename for x in info.siblings}
        weight='model.safetensors' if 'model.safetensors' in names else 'pytorch_model.bin'
        if weight not in names:raise RuntimeError('Expected official CLIP weight file is absent')
        patterns=['config.json','preprocessor_config.json','tokenizer_config.json','special_tokens_map.json','tokenizer.json','vocab.json','merges.txt',weight,'README.md']
        snapshot_download(repo_id='openai/clip-vit-base-patch16',revision=info.sha,local_dir=MODEL,allow_patterns=patterns)
        report['model']={'repo_id':'openai/clip-vit-base-patch16','revision':info.sha,
                         'weight_file':weight,'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in MODEL.iterdir() if p.is_file()}}
        print('Official ViT-B/16 weights staged:',info.sha,flush=True);save()
    except Exception as e:
        report['errors'].append({'stage':'model','error':f'{type(e).__name__}: {e}'});save()
    if not a.model_only:
        (ROOT/'assets/videos').mkdir(parents=True,exist_ok=True)
        for spec in VIDEOS:
            row=dict(spec);path=ROOT/'assets/videos'/spec['filename'];temp=path.with_suffix(path.suffix+'.part')
            try:
                if not path.exists():
                    request=urllib.request.Request(spec['url'],headers={'User-Agent':'ClipTrail-local-evaluation/0.1'})
                    with urllib.request.urlopen(request,timeout=60) as response,temp.open('wb') as f:
                        while chunk:=response.read(1024*1024):f.write(chunk)
                    if temp.stat().st_size<1024:raise RuntimeError('Downloaded asset is unexpectedly small')
                    temp.replace(path)
                import av
                with av.open(str(path)) as container:
                    stream=container.streams.video[0]
                    row.update(width=stream.width,height=stream.height,duration_s=float(container.duration/av.time_base) if container.duration else None)
                row.update(status='downloaded_and_decodable',bytes=path.stat().st_size,sha256=sha(path),local_path=str(path.relative_to(ROOT)))
                print('Video staged:',spec['id'],row['bytes'],'bytes',flush=True)
            except Exception as e:
                row.update(status='failed',error=f'{type(e).__name__}: {e}');report['errors'].append({'stage':spec['id'],'error':str(e)})
            report['videos'].append(row);save()
    report['status']='completed' if not report['errors'] else 'partial_or_failed';save()
    print(json.dumps({'status':report['status'],'errors':report['errors']},indent=2))
    return 0 if report['status']=='completed' else 2

if __name__=='__main__':raise SystemExit(main())
