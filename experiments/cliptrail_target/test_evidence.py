"""Host tests of rejection/proof accounting, never substitutes for target traces."""
import json
import math
import platform
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'bundle'))
from evidence_rules import classify,embedding_parity,PARITY,provider_evidence,qnn_profile_evidence
from target_common import validate_files,sha,pe_machine
from assemble_bundle import extract_zip

HEADER='Msg Timestamp,Message,Time,Unit of Measurement,Timing Source,Event Level,Event Identifier\n'


class ProofTests(unittest.TestCase):
    def setUp(self):
        self.complete={k:True for k in classify({})['checks']}
        self.reference=np.zeros((1,512),np.float32);self.reference[0,0]=1

    def test_every_check_is_required_and_manual_review_remains(self):
        self.assertTrue(classify(self.complete)['evidence_complete'])
        self.assertFalse(classify(self.complete)['npu_verified'])
        for key in self.complete:
            with self.subTest(key=key):
                self.assertFalse(classify({**self.complete,key:False})['evidence_complete'])
                self.assertFalse(classify({**self.complete,key:'false'})['evidence_complete'])

    def test_registration_and_model_loading_do_not_pass(self):
        self.assertFalse(classify({'qnn_npu_device_selected':True,'inference_completed':True})['evidence_complete'])
        p=provider_evidence([{'cat':'Session','dur':1,'args':{'provider':'QNNExecutionProvider'}}])
        self.assertFalse(p['qnn_executed'])

    def test_cpu_compute_invalidates_strict_placement(self):
        events=[{'cat':'Node','dur':12,'args':{'provider':'QNNExecutionProvider'}}]
        self.assertTrue(provider_evidence(events)['only_qnn_compute'])
        events.append({'cat':'Node','dur':1,'args':{'provider':'CPUExecutionProvider'}})
        self.assertFalse(provider_evidence(events)['only_qnn_compute'])

    def test_zero_or_nonfinite_durations_not_execution(self):
        for dur in (0,-1,float('nan'),float('inf'),'1'):
            self.assertFalse(provider_evidence([{'cat':'Node','dur':dur,'args':{'provider':'QNNExecutionProvider'}}])['qnn_executed'])

    def test_device_work_required_beyond_host_execute(self):
        host=HEADER+'0,EXECUTE,100,US,BACKEND,ROOT,execute\n'
        self.assertFalse(qnn_profile_evidence(host)['hardware_work_seen'])
        self.assertFalse(qnn_profile_evidence(host+'0,FINALIZE,50,CYCLES,BACKEND,ROOT,HTP\n')['hardware_work_seen'])
        good=host+'0,EXECUTE DEVICE,80,US,BACKEND,SUB-EVENT,device\n'
        self.assertTrue(qnn_profile_evidence(good)['hardware_work_seen'])
        for value in ('0','-1','nan','inf'):
            self.assertFalse(qnn_profile_evidence(host+f'0,EXECUTE DEVICE,{value},US,BACKEND,SUB-EVENT,device\n')['hardware_work_seen'])
        self.assertFalse(qnn_profile_evidence(host+'0,EXECUTE DEVICE,1,BYTES,BACKEND,SUB-EVENT,device\n')['hardware_work_seen'])

    def test_unrecognized_profile_fails_closed(self):
        for text in ('','QNN HTP inference successful','provider,time\nQNN,1\n'):
            self.assertFalse(qnn_profile_evidence(text)['hardware_work_seen'])

    def test_extra_op_source_column_and_bom_are_supported(self):
        csv='\ufeff'+HEADER.rstrip()+',ONNX Source Ops\n0,EXECUTE DEVICE,10,US,BACKEND,SUB-EVENT,device,matmul\n'
        self.assertTrue(qnn_profile_evidence(csv)['hardware_work_seen'])

    def test_parity_rejects_wrong_direction_scale_shape_nan(self):
        self.assertTrue(embedding_parity(self.reference,self.reference,PARITY['float'])['pass'])
        for value in (-self.reference,2*self.reference,np.zeros_like(self.reference)):
            self.assertFalse(embedding_parity(value,self.reference,PARITY['float'])['pass'])
        for value in (np.ones(512),np.full((1,512),np.nan)):
            with self.assertRaises(ValueError):embedding_parity(value,self.reference,PARITY['float'])

    def test_hash_tampering_missing_and_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'file';p.write_bytes(b'original')
            manifest={'files':{'file':sha(p)}}
            self.assertTrue(validate_files(root,manifest))
            p.write_bytes(b'tampered')
            with self.assertRaises(ValueError):validate_files(root,manifest)
            p.unlink()
            with self.assertRaises(ValueError):validate_files(root,manifest)
            with self.assertRaises(ValueError):validate_files(root,{'files':{'../outside':'0'*64}})

    def test_pe_architecture_is_read_from_binary(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake.exe';data=bytearray(134);data[:2]=b'MZ'
            struct.pack_into('<I',data,60,128);data[128:132]=b'PE\0\0'
            for arch in (0xaa64,0x8664):
                struct.pack_into('<H',data,132,arch);p.write_bytes(data)
                self.assertEqual(pe_machine(p),hex(arch))

    def test_unsafe_and_conflicting_archives_rejected(self):
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);archive=root/'bad.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape','x')
            with self.assertRaises(ValueError):extract_zip(archive,root/'out')
            with zipfile.ZipFile(archive,'w') as z:z.writestr('module.py','good')
            extract_zip(archive,root/'out')
            (root/'out/module.py').write_text('bad')
            with self.assertRaises(ValueError):extract_zip(archive,root/'out')

    def test_wheel_data_is_installed_at_runtime_prefix(self):
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);archive=root/'wheel.zip';prefix=root/'runtime'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('example.data/data/share/man/example.1','manual')
                z.writestr('example/__init__.py','')
            extract_zip(archive,prefix/'Lib/site-packages',wheel=True,data_prefix=prefix)
            self.assertEqual((prefix/'share/man/example.1').read_text(),'manual')
            self.assertTrue((prefix/'Lib/site-packages/example/__init__.py').exists())

    @unittest.skipIf(platform.system()=='Windows','This rejection test intentionally requires a non-Windows host')
    def test_non_windows_runner_stops_before_dependencies(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'evidence/test'
            result=subprocess.run([sys.executable,str(ROOT/'bundle/run_smoke.py'),'--bundle',str(root),'--output',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            report=json.loads((out/'smoke.json').read_text())
            self.assertEqual(report['failed_stage'],'native_architecture')
            self.assertEqual(report['calls'],{'cpu':0,'qnn':0})
            self.assertFalse(report['npu_verified'])


if __name__=='__main__':unittest.main()
