"""Copy the frozen v1 ZIP payload, changing only authorized v2 control files."""
import ast
import copy
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT/'bundle'))
from target_common import sha, write


def verify_v1():
    lock = json.loads((HERE/'v1-preservation-lock.json').read_text())
    for name, expected in lock['files'].items():
        if sha(REPO/name) != expected:
            raise ValueError('Historical v1 artifact changed: '+name)
    return lock


def main():
    lock = verify_v1()
    artifact = ROOT/'artifacts/ClipTrail-HTP-smoke-v2.zip'
    if artifact.exists():
        raise ValueError('Never overwrite v2 bundle; inspect the existing artifact')
    authorization = json.loads((HERE/'authorization-v2.json').read_text())
    overlays = {p.name:p.read_bytes() for p in (HERE/'control').iterdir() if p.is_file()}
    overlays['authorization-v2.json'] = (HERE/'authorization-v2.json').read_bytes()
    for name, data in overlays.items():
        if name.endswith('.py'):
            ast.parse(data, filename=name)
    original_zip = ROOT/'artifacts/ClipTrail-HTP-smoke-v1.zip'
    removed = {'INVENTORY_README.txt'}  # obsolete v1 instructions, never model/runtime data
    with zipfile.ZipFile(original_zip) as source:
        original = json.loads(source.read('bundle-manifest.json'))
        if sha(ROOT/'bundle/bundle-manifest.json') != lock['files'][str((ROOT/'bundle/bundle-manifest.json').relative_to(REPO))]:
            raise ValueError('Unexpected source manifest')
        manifest = copy.deepcopy(original)
        manifest.update(schema=2,bundle_version='v2',assembled_utc=datetime.now(timezone.utc).isoformat(),
                        stage='One explicitly authorized native smoke attempt only; stop for review',
                        authorization=authorization,npu_verified=False)
        manifest['original_v1'] = {'zip_sha256':sha(original_zip),
            'manifest_sha256':hashlib.sha256(source.read('bundle-manifest.json')).hexdigest(),
            'deployment_gate_at_v1_assembly':manifest.pop('deployment_gate'),
            'preserved_artifacts':lock['files']}
        manifest['files'] = {k:v for k,v in original['files'].items() if k not in removed}
        for name,data in overlays.items():
            manifest['files'][name] = hashlib.sha256(data).hexdigest()
        protected = [n for n in original['files'] if n.startswith(('model/','runtime/','input/'))]
        if any(manifest['files'].get(n) != original['files'][n] for n in protected):
            raise ValueError('Model/runtime/input changed')
        if manifest['model'] != original['model'] or manifest['runtime'] != original['runtime']:
            raise ValueError('Model or runtime metadata changed')
        write(HERE/'smoke-manifest-v2.json', manifest)
        with zipfile.ZipFile(artifact,'x',zipfile.ZIP_DEFLATED,compresslevel=3) as target:
            for name,digest in sorted(manifest['files'].items()):
                data = overlays[name] if name in overlays else source.read(name)
                if hashlib.sha256(data).hexdigest()!=digest:
                    raise ValueError('Payload hash mismatch: '+name)
                target.writestr(name,data)
            target.writestr('bundle-manifest.json',(HERE/'smoke-manifest-v2.json').read_bytes())
    # Reopen the produced archive; compare every payload to its manifest and v1.
    with zipfile.ZipFile(artifact) as target:
        if len(target.namelist()) != len(set(target.namelist())):
            raise ValueError('Duplicate ZIP members')
        if set(target.namelist()) != set(manifest['files'])|{'bundle-manifest.json'}:
            raise ValueError('Unexpected ZIP members')
        for name,digest in manifest['files'].items():
            h=hashlib.sha256()
            with target.open(name) as f:
                for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
            if h.hexdigest()!=digest:raise ValueError('ZIP verification failed: '+name)
        unpacked_bytes=sum(i.file_size for i in target.infolist())
    verify_v1()
    changed = sorted(n for n in original['files'] if n in manifest['files'] and original['files'][n]!=manifest['files'][n])
    added = sorted(set(manifest['files'])-set(original['files']))
    audit = {'status':'V2_BUNDLE_STATICALLY_VERIFIED','created_utc':datetime.now(timezone.utc).isoformat(),
        'artifact':str(artifact.relative_to(ROOT)),'zip_sha256':sha(artifact),'zip_bytes':artifact.stat().st_size,
        'unpacked_bytes':unpacked_bytes,'manifest_sha256':sha(HERE/'smoke-manifest-v2.json'),
        'files_checked':len(manifest['files']),'v1_preservation_checks_passed':True,
        'protected_payload_files_identical':len(protected),'model_metadata_identical':True,'runtime_metadata_identical':True,
        'changed_control_files':changed,'added_control_files':added,'removed_instruction_files':sorted(removed),
        'native_attempt_started':False,'npu_verified':False,'runtime_reprovisioned':False}
    write(HERE/'results/bundle-audit-v2.json',audit)
    write(HERE/'results/smoke-outcome-v2.json',{'schema':2,'authorization_id':authorization['authorization_id'],
        'status':'AWAITING_SINGLE_TARGET_ATTEMPT','updated_utc':datetime.now(timezone.utc).isoformat(),
        'max_attempts':1,'timeout_seconds':600,'automatic_retries':False,'target_attempts_observed':0,
        'native_initialization':None,'qnn_provider_load':None,'graph_execution':None,'htp_evidence':None,
        'embedding_parity':None,'runtime_observed':None,'warnings_or_fallback_partitions':None,
        'npu_verified':False,'systems_benchmark_started':False,'v2_zip_sha256':audit['zip_sha256'],
        'note':'This is a pending handoff record, not a native result. Preserve returned raw evidence before updating the outcome.'})
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
