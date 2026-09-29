"""v2: one authorized native attempt. Same v1 model/runtime/input/precision."""
import argparse
import datetime
import gc
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path
from target_common import sha,write,validate_files,native_probe,dependency_probe,loaded_accelerator_modules
from evidence_rules import provider_evidence,qnn_profile_evidence,classify,embedding_parity,PARITY
from attempt_policy import claim_native_once,target_inventory


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ticket',type=Path,required=True)
    args=parser.parse_args()
    root=args.bundle.resolve();output=args.output.resolve()
    if not output.is_relative_to(root/'evidence'):raise ValueError('Output must be inside bundle/evidence')
    output.mkdir(parents=True,exist_ok=True)
    report_path=output/'smoke.json'
    if report_path.exists():raise ValueError('Never overwrite an earlier smoke run')
    report={'schema':2,'bundle_version':'v2','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'started',
            'inference_performed':False,'npu_verified':False,'gate_checks':{},'calls':{'cpu':0,'qnn':0},
            'run_attempts':{'cpu':0,'qnn':0},'session_creation_attempts':{'cpu':0,'qnn':0},
            'automatic_retries':False,'stage_results':{},'runtime':{},'diagnostic_errors':[]}
    def checkpoint(stage):
        stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        report['stage']=stage;report['last_checkpoint_utc']=stamp;write(report_path,report)
        with (output/'stages.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps({'utc':stamp,'stage':stage,'calls':report['calls'],
                                'run_attempts':report['run_attempts']})+'\n')
        print(json.dumps({'utc':stamp,'stage':stage}),flush=True)
    checkpoint('native_architecture')
    code=2
    try:
        report['native']=native_probe()
        report['gate_checks']['native_windows_arm64']=report['native']['native_windows_arm64']
        if not report['native']['native_windows_arm64']:raise RuntimeError('Requires native Windows ARM64 Python; x64 emulation is rejected')
        report['stage_results']['native_arm64_python_initialized']=True
        report['runtime']['python']=platform.python_version()
        manifest=json.loads((root/'bundle-manifest.json').read_text())
        report['manifest_sha256']=sha(root/'bundle-manifest.json')
        checkpoint('v2_attempt_authorization')
        report['attempt_claim']=claim_native_once(root,output,manifest,args.ticket)
        report['target_inventory']=target_inventory(output,manifest['authorization']['target'])
        checkpoint('bundle_hash_validation')
        report['gate_checks']['bundle_hashes_valid']=validate_files(root,manifest)
        if platform.python_version()!=manifest['runtime']['python_version']:raise ValueError('Portable Python version mismatch')
        capi=root/manifest['runtime']['capi_directory']
        # Scoped DLL search path, held open for the lifetime of the sessions.
        dll_cookie=os.add_dll_directory(str(capi))
        qnn_cookie=os.add_dll_directory(str(root/manifest['runtime']['qnn_directory']))
        report['dll_directory_added']=manifest['runtime']['capi_directory']
        checkpoint('native_dependencies')
        report['native_dependencies']=dependency_probe()
        missing=[d['name'] for d in report['native_dependencies'] if d['required_before_ort_import'] and not d['loaded']]
        if missing:raise RuntimeError('Missing native Visual C++ runtime dependencies: '+', '.join(missing))
        checkpoint('dependency_import')
        import numpy as np
        report['runtime']['numpy']=np.__version__
        checkpoint('ort_import')
        import onnxruntime as ort
        ort.disable_telemetry_events()
        report['runtime'].update(onnxruntime=ort.__version__,build_info=ort.get_build_info(),
                                 available_builtin_providers=ort.get_available_providers(),
                                 telemetry_disabled_via_api=True)
        report['stage_results']['ort_imported']=True
        checkpoint('qnn_plugin_import')
        import onnxruntime_qnn as qnn_ep
        report['runtime'].update({
                           'qnn_plugin':qnn_ep.__version__,'qairt':qnn_ep.build_and_package_info.qnn_version,
                           'qnn_plugin_library':str(Path(qnn_ep.get_library_path()).relative_to(root))})
        report['stage_results']['qnn_plugin_imported']=True
        report['gate_checks']['runtime_versions_match']=(ort.__version__==manifest['runtime']['ort_version'] and
            qnn_ep.__version__==manifest['runtime']['qnn_version'] and np.__version__==manifest['runtime']['numpy_version'] and
            qnn_ep.build_and_package_info.qnn_version==manifest['runtime']['qairt_version'])
        if not report['gate_checks']['runtime_versions_match']:raise ValueError('Runtime versions differ from pinned wheels')
        ep_library=Path(qnn_ep.get_library_path()).resolve()
        if ep_library!=(root/manifest['runtime']['ep_library']).resolve():raise ValueError('Unexpected plugin library path')
        if sha(ep_library)!=manifest['runtime']['ep_sha256']:raise ValueError('QNN plugin DLL hash mismatch')
        checkpoint('qnn_plugin_registration')
        ort.register_execution_provider_library('QNNExecutionProvider',str(ep_library))
        report['stage_results']['qnn_provider_registered']=True
        checkpoint('qnn_device_enumeration')
        devices=ort.get_ep_devices()
        report['ep_devices']=[{'name':d.ep_name,'vendor':d.ep_vendor,'device_type':str(d.device.type),
                              'vendor_id':d.device.vendor_id,'device_id':d.device.device_id,
                              'device_metadata':dict(d.device.metadata),'ep_metadata':dict(d.ep_metadata)} for d in devices]
        selected=[d for d in devices if d.ep_name=='QNNExecutionProvider' and d.device.type==ort.OrtHardwareDeviceType.NPU]
        if len(selected)!=1:raise RuntimeError('Expected exactly one QNN NPU device; inspect returned enumeration')
        report['gate_checks']['qnn_npu_device_selected']=True
        with np.load(root/'input/target_input.npz',allow_pickle=False) as archive:
            feeds={k:archive[k] for k in archive.files}
        expected=np.load(root/'input/cpu_reference.npy',allow_pickle=False)
        model=root/'model/image_encoder.onnx'
        report.update(model_sha256=sha(model),precision=manifest['model']['precision'],
                      input_sha256=sha(root/'input/target_input.npz'),reference_sha256=sha(root/'input/cpu_reference.npy'))
        def opts(profile=False):
            o=ort.SessionOptions();o.intra_op_num_threads=2;o.inter_op_num_threads=1
            o.log_severity_level=0;o.log_verbosity_level=1
            o.enable_profiling=profile;o.profile_file_prefix=str(output/'ort-profile')
            return o
        def parity(array,limits):
            return embedding_parity(array,expected,limits)
        checkpoint('cpu_same_graph')
        report['session_creation_attempts']['cpu']+=1;checkpoint('cpu_session_creation')
        cpu=ort.InferenceSession(str(model),sess_options=opts(),providers=['CPUExecutionProvider'],enable_fallback=False);cpu.disable_fallback()
        report['cpu_session_providers']=cpu.get_providers()
        report['stage_results']['cpu_graph_loaded']=True
        report['run_attempts']['cpu']+=1;checkpoint('cpu_inference')
        start=time.perf_counter();cpu_embedding=cpu.run(['image_features'],feeds)[0]
        report['cpu_call_ms']=(time.perf_counter()-start)*1000;report['calls']['cpu']+=1
        np.save(output/'cpu_embedding.npy',cpu_embedding,allow_pickle=False)
        report['cpu_embedding_sha256']=sha(output/'cpu_embedding.npy')
        report['target_cpu_vs_frozen']=parity(cpu_embedding,{'cosine_min':.99999,'max_abs_max':.001})
        if manifest['model']['precision']=='float' and not report['target_cpu_vs_frozen']['pass']:
            raise ValueError('Same-graph target CPU output disagrees with frozen reference')
        del cpu;gc.collect()
        backend=(root/manifest['runtime']['htp_backend']).resolve()
        if backend.name.lower()!='qnnhtp.dll':raise ValueError('Backend must be the pinned QnnHtp.dll')
        report['gate_checks']['requested_pinned_htp_backend']=sha(backend)==manifest['runtime']['htp_sha256']
        qopts=opts(True);qopts.add_session_config_entry('session.disable_cpu_ep_fallback','1')
        provider_options={'backend_path':str(backend),'profiling_level':'detailed',
                          'profiling_file_path':str(output/'qnn-profile.csv'),
                          'offload_graph_io_quantization':'0','enable_htp_fp16_precision':'1',
                          'htp_performance_mode':'balanced','enable_framework_op_trace':'1',
                          'framework_op_trace_dir':str(output)}
        report['requested_provider_options']={**provider_options,'backend_path':manifest['runtime']['htp_backend'],
                                              'profiling_file_path':'qnn-profile.csv'}
        report['requested_provider_options']['framework_op_trace_dir']='this evidence directory'
        report['gate_checks']['strict_cpu_fallback_disabled']=True
        report['session_creation_attempts']['qnn']+=1;checkpoint('qnn_session_creation')
        start=time.perf_counter()
        qopts.add_provider_for_devices(selected,provider_options)
        session=ort.InferenceSession(str(model),sess_options=qopts,enable_fallback=False)
        session.disable_fallback();report['qnn_session_init_ms']=(time.perf_counter()-start)*1000
        report['session_providers']=session.get_providers()
        try: report['session_provider_options']=session.get_provider_options()
        except Exception as diagnostic_error:report['diagnostic_errors'].append('provider_options: '+str(diagnostic_error))
        if 'QNNExecutionProvider' not in session.get_providers():raise RuntimeError('ORT constructor fell back; refuse inference')
        report['stage_results']['prepared_graph_loaded_qnn']=True
        specs=session.get_inputs()
        if len(specs)!=1 or set(feeds)!={s.name for s in specs}:raise ValueError('Unexpected graph inputs')
        if any(tuple(feeds[s.name].shape)!=tuple(s.shape) for s in specs):raise ValueError('Input shape mismatch')
        report['run_attempts']['qnn']+=1;checkpoint('qnn_inference')
        start=time.perf_counter();embedding=session.run(['image_features'],feeds)[0]
        report['qnn_profiled_call_ms']=(time.perf_counter()-start)*1000
        report['calls']['qnn']+=1;report['inference_performed']=True
        report['gate_checks']['inference_completed']=True
        report['stage_results']['prepared_graph_executed_qnn']=True
        np.save(output/'qnn_embedding.npy',embedding,allow_pickle=False)
        report['qnn_embedding_sha256']=sha(output/'qnn_embedding.npy')
        checkpoint('embedding_validation')
        report['qnn_vs_frozen']=parity(embedding,PARITY[manifest['model']['precision']])
        report['gate_checks']['finite_unit_embedding']=report['qnn_vs_frozen']['finite_unit_embedding']
        report['gate_checks']['embedding_parity_passed']=report['qnn_vs_frozen']['pass']
        report['stage_results']['valid_embedding_produced']=report['qnn_vs_frozen']['finite_unit_embedding']
        checkpoint('execution_evidence_collection')
        profile=Path(session.end_profiling())
        report['ort_profile_file']=profile.name
        report['placement']=provider_evidence(json.loads(profile.read_text()))
        report['gate_checks']['qnn_compute_executed']=report['placement']['qnn_executed']
        report['gate_checks']['only_qnn_compute']=report['placement']['only_qnn_compute']
        report['loaded_modules']=loaded_accelerator_modules(root)
        report['gate_checks']['pinned_htp_loaded']=any(m['name'].lower()=='qnnhtp.dll' and m['inside_bundle'] and
            m['sha256']==manifest['runtime']['htp_sha256'] for m in report['loaded_modules'])
        del session;gc.collect()
        # Some versions flush backend profile on session destruction.
        csv_path=output/'qnn-profile.csv'
        report['htp_profile']=qnn_profile_evidence(csv_path.read_text(encoding='utf-8-sig')) if csv_path.exists() else {'hardware_work_seen':False,'reason':'No QNN profile produced'}
        report['gate_checks']['qnn_hardware_work_seen']=report['htp_profile']['hardware_work_seen']
        report['verification']=classify(report['gate_checks'])
        report['stage_results']['automated_htp_evidence_complete']=report['verification']['evidence_complete']
        report['status']='EVIDENCE_COMPLETE_REVIEW_REQUIRED' if report['verification']['evidence_complete'] else 'INCOMPLETE_EVIDENCE'
        code=0 if report['verification']['evidence_complete'] else 3
        ort.unregister_execution_provider_library('QNNExecutionProvider')
        qnn_cookie.close();dll_cookie.close()
    except Exception as e:
        code=2
        report['failed_stage']=report['stage']
        report['status']='BLOCKED_OR_FAILED';report['error']=f'{type(e).__name__}: {e}'
        (output/'exception.txt').write_text(traceback.format_exc(),encoding='utf-8')
        try: report['failure_loaded_modules']=loaded_accelerator_modules(root)
        except Exception as diagnostic_error:report['diagnostic_errors'].append(str(diagnostic_error))
        report['verification']=classify(report['gate_checks'])
    report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Supervisor hashes the complete evidence tree after all writers terminate.
    # Do not open live redirected stdout/stderr or supervisor-owned JSON here.
    report['result_hashes']={}
    for p in output.iterdir():
        if p.is_file() and (p.suffix=='.npy' or p.name.startswith('ort-profile') or
                            p.name in ('qnn-profile.csv','qnn_op_trace.json','exception.txt')):
            try: report['result_hashes'][p.name]=sha(p)
            except OSError as diagnostic_error:report['diagnostic_errors'].append('hash: '+str(diagnostic_error))
    checkpoint('finished')
    print(json.dumps({'status':report['status'],'npu_verified':False,'error':report.get('error'),
                      'verification':report.get('verification')},indent=2))
    return code


if __name__=='__main__':raise SystemExit(main())
