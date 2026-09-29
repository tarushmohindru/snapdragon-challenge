"""Inspect released ONNX, prune only the image branch, prove CPU equivalence."""
import copy
import gc
import hashlib
import json
import shutil
import time
import zipfile
from pathlib import Path
import numpy as np
import onnx
import onnxruntime as ort
from onnx.external_data_helper import convert_model_from_external_data
ort.disable_telemetry_events()

ROOT=Path(__file__).resolve().parent


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n')


def safe_extract(archive,destination):
    with zipfile.ZipFile(archive) as z:
        if sum(i.file_size for i in z.infolist())>3_000_000_000: raise ValueError('Unexpected expanded model size')
        for info in z.infolist():
            p=(destination/info.filename).resolve()
            if not p.is_relative_to(destination.resolve()) or info.filename.startswith('/'):
                raise ValueError('Unsafe archive path')
            if (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Archive symlinks are not allowed')
            if info.is_dir():continue
            p.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as source,p.open('wb') as target:shutil.copyfileobj(source,target)


def describe(session):
    return {'inputs':[{'name':v.name,'shape':v.shape,'type':v.type} for v in session.get_inputs()],
            'outputs':[{'name':v.name,'shape':v.shape,'type':v.type} for v in session.get_outputs()]}


def options():
    opts=ort.SessionOptions(); opts.intra_op_num_threads=2; opts.inter_op_num_threads=1
    return opts


def compare(output,expected):
    actual=np.asarray(output,dtype=np.float32)
    if actual.shape!=(1,512) or not np.isfinite(actual).all():raise ValueError('Expected finite [1,512] image output')
    norm=float(np.linalg.norm(actual)); refnorm=float(np.linalg.norm(expected))
    cosine=float(np.sum(actual*expected)/(norm*refnorm)) if norm*refnorm>0 else -1
    return {'cosine':cosine,'max_abs':float(np.max(np.abs(actual-expected))),'norm':norm,
            'pass':bool(cosine>=.99999 and np.max(np.abs(actual-expected))<=.001 and .99<=norm<=1.01)}


def main():
    output=ROOT/'results/graph-preparation.json'
    if output.exists() and json.loads(output.read_text()).get('status')=='CPU_PARITY_VERIFIED':
        old=json.loads(output.read_text())
        assert sha(ROOT/'bundle/model/image_encoder.onnx')==old['image_graph_sha256']
        print('Existing CPU-verified graph preserved.');return
    provisioning=json.loads((ROOT/'results/provisioning.json').read_text())
    precision,asset=next((p,a) for p,a in provisioning['models'].items() if a.get('status')=='downloaded')
    report={'status':'started','precision':precision,'asset':asset,'onnx':onnx.__version__,'ort':ort.__version__,
            'npu_verified':False,'source_model_modified':'Image branch pruned; target compatibility must be verified anew.'}
    write(output,report)
    try:
        archive=ROOT/asset['file']
        assert sha(archive)==asset['sha256']
        source_dir=ROOT/'assets/released_graph'
        safe_extract(archive,source_dir)
        candidates=sorted(source_dir.rglob('*.onnx'))
        if len(candidates)!=1:raise ValueError('Expected one released ONNX graph; inspect candidates: '+str(candidates))
        source=candidates[0]
        inspected=onnx.load(source,load_external_data=False)
        report['source_interface']={'inputs':[v.name for v in inspected.graph.input],
                                     'outputs':[v.name for v in inspected.graph.output],
                                     'operators':sorted({n.domain+':'+n.op_type for n in inspected.graph.node}),
                                     'opsets':{o.domain:o.version for o in inspected.opset_import}}
        report['released_files']={str(p.relative_to(source_dir)):sha(p) for p in source_dir.rglob('*') if p.is_file()}
        for tensor in inspected.graph.initializer:
            if tensor.data_location==onnx.TensorProto.EXTERNAL:
                location=next(v.value for v in tensor.external_data if v.key=='location')
                if not (source.parent/location).resolve().is_relative_to(source_dir.resolve()):
                    raise ValueError('Unsafe external tensor path')
        if 'image_features' not in report['source_interface']['outputs'] or 'image' not in report['source_interface']['inputs']:
            raise ValueError('Unexpected names; inspect exact source graph before mapping tensors')
        combined=ort.InferenceSession(str(source),sess_options=options(),providers=['CPUExecutionProvider'])
        report['combined_interface']=describe(combined)
        raw=np.load(ROOT/'bundle/input/image_raw_nchw.npy',allow_pickle=False)
        feeds={}
        for spec in combined.get_inputs():
            shape=tuple(spec.shape)
            if not all(isinstance(d,int) and d>0 for d in shape):raise ValueError('Graph has dynamic input dimensions')
            if spec.name=='image':
                if spec.type!='tensor(float)':raise ValueError('Unexpected image dtype')
                if shape==(1,3,224,224):feeds[spec.name]=raw.copy()
                elif shape==(1,224,224,3):feeds[spec.name]=raw.transpose(0,2,3,1).copy()
                else:raise ValueError('Unexpected image layout '+str(shape))
            elif spec.name=='text':
                if shape[-1]!=77:raise ValueError('Unexpected text shape')
                dtype={'tensor(int32)':np.int32,'tensor(int64)':np.int64}.get(spec.type)
                if dtype is None:raise ValueError('Unexpected text dtype')
                ids=np.zeros(shape,dtype=dtype);ids[...,0]=49406;ids[...,1]=49407
                feeds[spec.name]=ids
            else:raise ValueError('Unexpected input '+spec.name)
        start=time.perf_counter();combined_output=combined.run(['image_features'],feeds)[0]
        report['combined_cpu_call_ms']=(time.perf_counter()-start)*1000
        expected=np.load(ROOT/'bundle/input/cpu_reference.npy',allow_pickle=False)
        report['combined_vs_frozen_reference']=compare(combined_output,expected)
        if not report['combined_vs_frozen_reference']['pass']:
            raise ValueError('Released graph differs from frozen CPU reference; no target ship until explained')
        del combined,inspected;gc.collect()
        model=onnx.load(source,load_external_data=True)
        branch=onnx.utils.Extractor(model).extract_model(['image'],['image_features'])
        # Store a self-contained image-only graph; no external relative paths.
        convert_model_from_external_data(branch)
        model_dir=ROOT/'bundle/model';model_dir.mkdir(exist_ok=True)
        target=model_dir/'image_encoder.onnx'
        onnx.save_model(branch,target,save_as_external_data=False)
        onnx.checker.check_model(str(target),full_check=True)
        report['source_nodes']=len(model.graph.node);report['image_nodes']=len(branch.graph.node)
        report['image_operators']=sorted({n.domain+':'+n.op_type for n in branch.graph.node})
        del model,branch;gc.collect()
        image_session=ort.InferenceSession(str(target),sess_options=options(),providers=['CPUExecutionProvider'])
        image_input={'image':feeds['image']}
        start=time.perf_counter();image_output=image_session.run(['image_features'],image_input)[0]
        report['image_only_cpu_call_ms']=(time.perf_counter()-start)*1000
        report['pruned_vs_combined']=compare(image_output,combined_output)
        report['pruned_vs_frozen_reference']=compare(image_output,expected)
        if not report['pruned_vs_combined']['pass'] or not report['pruned_vs_frozen_reference']['pass']:
            raise ValueError('Pruning changed the image embedding')
        np.savez(ROOT/'bundle/input/target_input.npz',**image_input)
        np.save(ROOT/'bundle/input/onnx_cpu_reference.npy',image_output,allow_pickle=False)
        report.update(status='CPU_PARITY_VERIFIED',image_graph_sha256=sha(target),
                      image_graph_bytes=target.stat().st_size,image_interface=describe(image_session))
        write(output,report)
        print(json.dumps({k:report[k] for k in ['status','precision','image_graph_bytes','image_nodes','pruned_vs_frozen_reference']}))
    except Exception as e:
        report.update(status='BLOCKED',error=f'{type(e).__name__}: {e}')
        write(output,report);raise


if __name__=='__main__':main()
