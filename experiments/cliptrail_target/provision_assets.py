"""Resolve public official model/runtime assets; record every version and hash."""
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from packaging.version import Version

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT/'assets'
RESULTS = ROOT/'results'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n')


def fetch_json(url):
    with urllib.request.urlopen(url,timeout=60) as r:
        return json.load(r)


def download(url,path,expected=None):
    receipt=path.with_suffix(path.suffix+'.download.json')
    if path.exists() and receipt.exists():
        d=json.loads(receipt.read_text())
        if d['url']==url and sha(path)==d['sha256'] and (not expected or d['sha256']==expected):
            return d
    temporary=path.with_suffix(path.suffix+'.part')
    print('Downloading',path.name,flush=True)
    req=urllib.request.Request(url,headers={'User-Agent':'ClipTrail-research-provisioner/1'})
    with urllib.request.urlopen(req,timeout=120) as r,temporary.open('wb') as f:
        length=r.headers.get('Content-Length')
        while True:
            block=r.read(4*1024*1024)
            if not block: break
            f.write(block)
    if length and temporary.stat().st_size!=int(length): raise ValueError('Incomplete download')
    digest=sha(temporary)
    if expected and digest!=expected: raise ValueError('Published SHA-256 mismatch')
    temporary.replace(path)
    d={'url':url,'sha256':digest,'bytes':path.stat().st_size,'file':str(path.relative_to(ROOT))}
    save(receipt,d)
    return d


def model_assets(report):
    from qai_hub_models_cli.fetch import get_asset_url
    report['cli_version']=importlib.metadata.version('qai_hub_models_cli')
    report['models']={}
    # Fixed release from prior primary research; no broad version or model search.
    for precision in ('float','w8a16'):
        try:
            url=get_asset_url(model='openai_clip',runtime='onnx',precision=precision,version=Version('0.62.2'),quiet=True,url_only=True)
            parsed=urlparse(url)
            if parsed.scheme!='https' or not parsed.netloc.startswith('qaihub-public-assets.') or not parsed.netloc.endswith('amazonaws.com'):
                raise ValueError('Resolver did not return the expected public Qualcomm asset store: '+url)
            info=download(url,ASSETS/f'openai_clip-0.62.2-{precision}.zip')
            report['models'][precision]={'status':'downloaded','release':'0.62.2',**info}
            # First float route is enough for the immediate smoke. Do not download
            # a second large graph unless float resolution/download is unavailable.
            break
        except Exception as e:
            report['models'][precision]={'status':'blocked','error':f'{type(e).__name__}: {e}'}
            print('Model',precision,report['models'][precision]['error'],flush=True)


def runtime_assets(report):
    metadata=fetch_json('https://pypi.org/pypi/onnxruntime-qnn/json')
    save(RESULTS/'pypi-onnxruntime-qnn.json',metadata)
    versions=sorted((Version(v) for v in metadata['releases'] if not Version(v).is_prerelease),reverse=True)
    choices=[]
    for v in versions:
        for abi,py,embed in [('cp312','312','3.12.10'),('cp311','311','3.11.9')]:
            candidates=[f for f in metadata['releases'][str(v)] if not f.get('yanked') and
                        f['filename'].endswith(f'-{abi}-{abi}-win_arm64.whl')]
            if candidates: choices.append((v,abi,py,embed,candidates[0]))
        if choices: break
    if not choices: raise ValueError('No stable native win_arm64 cp312/cp311 QNN wheel found')
    version,abi,py,embed,wheel=choices[0]
    report['runtime_selection']={'qnn_version':str(version),'python_abi':abi,'python_version':embed,
                                 'selection_rule':'Newest stable public QNN wheel; prefer cp312 then cp311 within that release',
                                 'qnn_published_sha256':wheel['digests']['sha256']}
    wheelhouse=ASSETS/'wheelhouse'
    wheelhouse.mkdir(exist_ok=True)
    command=[sys.executable,'-m','pip','download','--only-binary=:all:','--platform','win_arm64',
             '--python-version',py,'--implementation','cp','--abi',abi,'--dest',str(wheelhouse),
             '--index-url','https://pypi.org/simple',f'onnxruntime-qnn=={version}','numpy']
    proc=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (RESULTS/'wheel-download.log').write_text(proc.stdout)
    report['runtime_selection']['download_command']=command[1:]
    if proc.returncode: raise RuntimeError('ARM64 dependency wheel resolution failed; see wheel-download.log')
    actual=wheelhouse/wheel['filename']
    if not actual.exists() or sha(actual)!=wheel['digests']['sha256']:
        raise ValueError('QNN wheel differs from public PyPI SHA-256')
    records=[]
    # Audit every wheel against the public PyPI release metadata, not just QNN.
    from packaging.utils import parse_wheel_filename
    for path in sorted(wheelhouse.glob('*.whl')):
        name,v,_,tags=parse_wheel_filename(path.name)
        if not any(t.platform in ('win_arm64','any') for t in tags):
            raise ValueError('Unexpected wheel platform '+path.name)
        info=fetch_json(f'https://pypi.org/pypi/{name}/{v}/json')
        matches=[x for x in info['urls'] if x['filename']==path.name]
        if len(matches)!=1 or sha(path)!=matches[0]['digests']['sha256']:
            raise ValueError('Published dependency hash mismatch '+path.name)
        records.append({'name':str(name),'version':str(v),'file':str(path.relative_to(ROOT)),
                        'sha256':sha(path),'bytes':path.stat().st_size,'url':matches[0]['url']})
    report['runtime_selection']['wheels']=records
    url=f'https://www.python.org/ftp/python/{embed}/python-{embed}-embed-arm64.zip'
    report['runtime_selection']['python_embed']=download(url,ASSETS/f'python-{embed}-embed-arm64.zip')
    report['runtime_selection']['status']='downloaded_not_executed'


def main():
    ASSETS.mkdir(parents=True,exist_ok=True); RESULTS.mkdir(exist_ok=True)
    report={'started_utc':datetime.now(timezone.utc).isoformat(),'npu_verified':False,'inference_performed':False}
    for key,fn in [('model_assets',model_assets),('runtime_assets',runtime_assets)]:
        try: fn(report)
        except Exception as e:
            report[key+'_error']=f'{type(e).__name__}: {e}'
            print(key,report[key+'_error'],flush=True)
        save(RESULTS/'provisioning.json',report)
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    save(RESULTS/'provisioning.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
