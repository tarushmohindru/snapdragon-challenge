"""Build an offline private ARM64 runtime from hash-verified official wheels."""
import ast
import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BUNDLE=ROOT/'bundle'
sys.path.insert(0,str(BUNDLE))
from target_common import sha,pe_machine,write,validate_files


def extract_zip(path,destination,wheel=False,data_prefix=None):
    with zipfile.ZipFile(path) as z:
        for i in z.infolist():
            if i.is_dir():continue
            if (i.external_attr>>16)&0o170000==0o120000:raise ValueError('Symlink rejected')
            parts=Path(i.filename).parts
            if any(p=='..' for p in parts) or Path(i.filename).is_absolute():raise ValueError('Unsafe ZIP member')
            file_root=destination
            if wheel and parts and parts[0].endswith('.data'):
                if parts[1] in ('purelib','platlib'):parts=parts[2:]
                elif parts[1]=='data' and data_prefix is not None:
                    file_root=data_prefix;parts=parts[2:]
                elif parts[1] in ('scripts','headers'):continue
                else:raise ValueError('Unsupported wheel data scheme '+i.filename)
            target=(file_root/Path(*parts)).resolve()
            if not target.is_relative_to(file_root.resolve()):raise ValueError('Archive escapes destination')
            data=z.read(i)
            if target.exists() and target.read_bytes()!=data:raise ValueError('Conflicting runtime file '+i.filename)
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)


def main():
    provisioning=json.loads((ROOT/'results/provisioning.json').read_text())
    graph=json.loads((ROOT/'results/graph-preparation.json').read_text())
    if graph['status']!='CPU_PARITY_VERIFIED':raise ValueError('CPU graph parity must pass before packaging')
    if sha(BUNDLE/'model/image_encoder.onnx')!=graph['image_graph_sha256']:
        raise ValueError('Image graph differs from CPU-tested graph')
    reference=json.loads((BUNDLE/'input/reference.json').read_text())
    for name,expected in reference['file_sha256'].items():
        if sha(BUNDLE/'input'/name)!=expected:raise ValueError('Reference asset differs: '+name)
    selected=provisioning['runtime_selection']
    if selected['status']!='downloaded_not_executed':raise ValueError('Missing runtime assets')
    runtime=BUNDLE/'runtime'
    # Fresh staging of exactly this lock; never merge multiple runtime versions.
    stage=ROOT/'runtime-stage'
    if stage.exists():raise ValueError('Runtime staging already exists; inspect it before retry')
    stage.mkdir()
    py=ROOT/selected['python_embed']['file']
    if sha(py)!=selected['python_embed']['sha256']:raise ValueError('Python archive hash mismatch')
    extract_zip(py,stage)
    site=stage/'Lib/site-packages'
    for wheel in selected['wheels']:
        path=ROOT/wheel['file']
        if sha(path)!=wheel['sha256']:raise ValueError('Wheel hash mismatch: '+path.name)
        extract_zip(path,site,wheel=True,data_prefix=stage)
    pths=list(stage.glob('python*._pth'))
    if len(pths)!=1:raise ValueError('Unexpected embedded Python configuration')
    original=pths[0].read_text()
    pths[0].write_text(original+'\nLib/site-packages\n..\n',encoding='utf8')
    if runtime.exists():raise ValueError('Runtime exists; no unreviewed overwrite')
    stage.rename(runtime)
    python_path=runtime/'python.exe'
    if pe_machine(python_path)!='0xaa64':raise ValueError('Python is not ARM64')
    qnn_dir=runtime/'Lib/site-packages/onnxruntime_qnn'
    capi=runtime/'Lib/site-packages/onnxruntime/capi'
    backend=qnn_dir/'QnnHtp.dll';ep=qnn_dir/'onnxruntime_providers_qnn.dll'
    native_files=[python_path,capi/'onnxruntime_pybind11_state.pyd',capi/'onnxruntime.dll',backend,ep]
    pe={str(p.relative_to(BUNDLE)):pe_machine(p) for p in native_files}
    if any(v not in ('0xaa64','0xa64e','0xa641') for v in pe.values()):raise ValueError('Non-ARM64 runtime binary')
    # Inspect package metadata without running ARM64 code on x86.
    assignments=ast.parse((qnn_dir/'build_and_package_info.py').read_text()).body
    qnn_info={n.targets[0].id:ast.literal_eval(n.value) for n in assignments if isinstance(n,ast.Assign)}
    versions={w['name']:w['version'] for w in selected['wheels']}
    shutil.copyfile(ROOT.parents[1]/'project/research/snapshots/clip-license.md',BUNDLE/'CLIP_LICENSE.txt')
    manifest={'schema':1,'assembled_utc':datetime.now(timezone.utc).isoformat(),
              'stage':'one-image CPU/HTP proof only; not the systems workload freeze',
              'deployment_gate':json.loads((ROOT/'deployment-gate.json').read_text()),
              'model':{'name':'AI Hub OpenAI CLIP ViT-B/16 image branch','release':'0.62.2',
                       'precision':graph['precision'],'sha256':graph['image_graph_sha256'],
                       'image_nodes':graph['image_nodes'],'interface':graph['image_interface'],
                       'upstream_archive_sha256':graph['asset']['sha256'],
                       'cpu_parity':graph['pruned_vs_frozen_reference']},
              'runtime':{'python_version':selected['python_version'],'python_abi':selected['python_abi'],
                         'ort_version':versions['onnxruntime'],'qnn_version':versions['onnxruntime-qnn'],
                         'qairt_version':qnn_info['qnn_version'],'numpy_version':versions['numpy'],
                         'capi_directory':str(capi.relative_to(BUNDLE)),
                         'qnn_directory':str(qnn_dir.relative_to(BUNDLE)),
                         'htp_backend':str(backend.relative_to(BUNDLE)),'htp_sha256':sha(backend),
                         'ep_library':str(ep.relative_to(BUNDLE)),'ep_sha256':sha(ep),
                         'wheels':selected['wheels'],'pe_machines':pe},
              'npu_verified':False,'files':{}}
    manifest['files']={str(p.relative_to(BUNDLE)):sha(p) for p in sorted(BUNDLE.rglob('*'))
                       if p.is_file() and p.name!='bundle-manifest.json' and '__pycache__' not in p.parts and 'evidence' not in p.relative_to(BUNDLE).parts}
    write(BUNDLE/'bundle-manifest.json',manifest)
    validate_files(BUNDLE,manifest)
    artifact=ROOT/'artifacts/ClipTrail-HTP-smoke-v1.zip'
    if artifact.exists():raise ValueError('Refusing to overwrite target bundle')
    with zipfile.ZipFile(artifact,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for relative in sorted(list(manifest['files'])+['bundle-manifest.json']):z.write(BUNDLE/relative,relative)
    write(ROOT/'results/bundle-audit.json',{'status':'ASSEMBLED_STATIC_CHECKS_PASS','zip_file':str(artifact.relative_to(ROOT)),
          'zip_sha256':sha(artifact),'zip_bytes':artifact.stat().st_size,'manifest_sha256':sha(BUNDLE/'bundle-manifest.json'),
          'files_checked':len(manifest['files']),'pe_machines':pe,'native_runtime_executed':False,'npu_verified':False})
    print(artifact)
    print('Bundle assembled and binary/hash checks pass; native Windows execution remains unverified.')


if __name__=='__main__':main()
