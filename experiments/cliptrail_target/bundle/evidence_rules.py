"""Conservative proof checks. Registration/loading alone can never pass."""
import csv
import io
import math

PARITY={'float':{'cosine_min':.999,'max_abs_max':.02},
        'w8a16':{'cosine_min':.99,'max_abs_max':.05}}


def embedding_parity(array,reference,limits):
    import numpy as np
    x=np.asarray(array,dtype=np.float32)
    expected=np.asarray(reference,dtype=np.float32)
    if x.shape!=(1,512) or expected.shape!=(1,512) or not np.isfinite(x).all() or not np.isfinite(expected).all():
        raise ValueError('Expected finite [1,512] embeddings')
    norm=float(np.linalg.norm(x));refnorm=float(np.linalg.norm(expected))
    cosine=float(np.sum(x*expected)/(norm*refnorm)) if norm*refnorm else -1.
    maximum=float(np.max(np.abs(x-expected)))
    return {'cosine':cosine,'max_absolute_error':maximum,'norm':norm,'reference_norm':refnorm,'limits':limits,
            'finite_unit_embedding':.98<=norm<=1.02 and .98<=refnorm<=1.02,
            'pass':cosine>=limits['cosine_min'] and maximum<=limits['max_abs_max'] and
                   .98<=norm<=1.02 and .98<=refnorm<=1.02}


def provider_evidence(events):
    counts={}
    nodes=[]
    for e in events:
        provider=e.get('args',{}).get('provider')
        duration=e.get('dur',0)
        if provider and e.get('cat')=='Node' and isinstance(duration,(float,int)) and math.isfinite(duration) and duration>0:
            counts[provider]=counts.get(provider,0)+1
            nodes.append({'name':e.get('name'),'duration_us':e['dur'],
                          'provider':provider,'op_name':e.get('args',{}).get('op_name')})
    return {'counts':counts,'executed_nodes':nodes,
            'qnn_executed':counts.get('QNNExecutionProvider',0)>0,
            'only_qnn_compute':bool(counts) and set(counts)=={'QNNExecutionProvider'}}


def qnn_profile_evidence(text):
    # Official ORT QNN serializer schema. Unknown formats require inspection;
    # a file merely existing or containing 'QNN' must not count as execution.
    reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    required={'Message','Time','Unit of Measurement','Timing Source','Event Level','Event Identifier'}
    names={s.strip() for s in (reader.fieldnames or [])}
    if not required.issubset(names):
        return {'schema_recognized':False,'execute_events':[],'hardware_events':[],
                'hardware_work_seen':False,'reason':'Unknown QNN CSV schema; retain raw file for review'}
    execute,hardware=[],[]
    for original in reader:
        r={str(k).strip():str(v or '').strip() for k,v in original.items() if k is not None}
        try: value=float(r['Time'])
        except (ValueError,KeyError): continue
        if not math.isfinite(value) or value<=0 or r['Timing Source'].upper()!='BACKEND': continue
        if r['Unit of Measurement'].upper() not in ('US','CYCLES'): continue
        message=r['Message'].upper()
        if message in ('EXECUTE','EXECUTE DEVICE'):
            execute.append(r)
        identifier=r['Event Identifier'].upper()
        # QNN generic EXECUTE_DEVICE is a device-stage event. Backend-specific
        # positive cycles are also retained when named as accelerator work.
        if message=='EXECUTE DEVICE' or (message=='NODE' and r['Unit of Measurement'].upper()=='CYCLES' and
            any(s in identifier for s in ('HTP','DSP','HMX','HVX','ACCELERATOR'))):
            hardware.append(r)
    return {'schema_recognized':True,'execute_events':execute,'hardware_events':hardware,
            'hardware_work_seen':bool(execute and hardware)}


def classify(evidence):
    checks={k:evidence.get(k,False) is True for k in (
        'native_windows_arm64','bundle_hashes_valid','runtime_versions_match','qnn_npu_device_selected',
        'strict_cpu_fallback_disabled','requested_pinned_htp_backend','pinned_htp_loaded',
        'inference_completed','qnn_compute_executed','only_qnn_compute',
        'qnn_hardware_work_seen','finite_unit_embedding','embedding_parity_passed')}
    return {'checks':checks,'evidence_complete':all(checks.values()),
            'missing':[k for k,v in checks.items() if not v],
            'npu_verified':False,
            'review_required':'Review returned raw inventory, module identities, ORT placement/profile and QNN hardware events before recording final HTP verification.'}
