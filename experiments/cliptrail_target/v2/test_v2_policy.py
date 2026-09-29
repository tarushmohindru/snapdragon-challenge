"""Host-only policy/failure tests. No native device or model inference is invoked."""
import ast
import concurrent.futures
import copy
import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'bundle'))
sys.path.insert(0,str(HERE/'control'))
from attempt_policy import AUTHORIZATION_ID,claim_native_once,target_inventory,validate_authorization
from target_common import sha


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.root=self.base/'bundle';self.output=self.root/'evidence/attempt'
        self.output.mkdir(parents=True)
        self.guard_base=self.base/'localapp'
        self.guard=self.guard_base/'ClipTrail'/AUTHORIZATION_ID
        self.guard.mkdir(parents=True)
        self.auth=json.loads((HERE/'authorization-v2.json').read_text())
        self.manifest={'schema':2,'authorization':self.auth}
        (self.root/'bundle-manifest.json').write_text(json.dumps(self.manifest))
        self.ticket={'authorization_id':AUTHORIZATION_ID,'token':'host-test-only',
            'timeout_seconds':600,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'bundle_directory':str(self.root),'output_directory':str(self.output),
            'manifest_sha256':sha(self.root/'bundle-manifest.json')}
        self.ticket_path=self.output/'attempt-ticket.json'
        self.save_ticket()

    def tearDown(self):
        self.tmp.cleanup()

    def save_ticket(self):
        # PowerShell 5.1 emits BOMs; exercise that format.
        self.ticket_path.write_text(json.dumps(self.ticket),encoding='utf-8-sig')
        (self.guard/'attempt.json').write_text(json.dumps(self.ticket),encoding='utf-8-sig')

    def claim(self):
        return claim_native_once(self.root,self.output,self.manifest,self.ticket_path,guard_base=self.guard_base)

    def test_authorization_is_one_attempt_exactly_600_seconds(self):
        validate_authorization(self.auth)
        for key,value in [('max_native_attempts',2),('attempt_wall_timeout_seconds',601),
                          ('automatic_retries',True),('explicit_extension_after_v1_cutoff',False)]:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):validate_authorization({**self.auth,key:value})

    def test_second_native_start_is_refused_even_after_first_ends(self):
        self.claim()
        with self.assertRaises(FileExistsError):self.claim()

    def test_concurrent_claims_allow_only_one(self):
        def call():
            try:self.claim();return True
            except FileExistsError:return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(lambda _:call(),range(4))),1)

    def test_expired_ticket_does_not_launch_native_work(self):
        self.ticket['started_utc']=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(seconds=601)).isoformat()
        self.save_ticket()
        with self.assertRaises(ValueError):self.claim()
        self.assertFalse((self.guard/'native-started.json').exists())

    def test_forged_extraction_and_manifest_are_rejected(self):
        self.ticket['bundle_directory']=str(self.base/'another-bundle');self.save_ticket()
        with self.assertRaises(ValueError):self.claim()
        self.ticket['bundle_directory']=str(self.root);self.ticket['manifest_sha256']='0'*64;self.save_ticket()
        with self.assertRaises(ValueError):self.claim()

    def test_local_ticket_cannot_replace_persistent_claim(self):
        altered={**self.ticket,'token':'not-issued'}
        self.ticket_path.write_text(json.dumps(altered))
        with self.assertRaises(ValueError):self.claim()

    def test_missing_supervisor_ticket_is_rejected(self):
        (self.guard/'attempt.json').unlink()
        with self.assertRaises(FileNotFoundError):self.claim()

    def test_new_extraction_does_not_clear_persistent_native_marker(self):
        self.claim()
        other=self.base/'new-bundle';out=other/'evidence/attempt';out.mkdir(parents=True)
        (other/'bundle-manifest.json').write_text(json.dumps(self.manifest))
        # Even a mistakenly reissued ticket cannot clear the consumed native marker.
        self.ticket.update(bundle_directory=str(other),output_directory=str(out))
        (out/'attempt-ticket.json').write_text(json.dumps(self.ticket))
        (self.guard/'attempt.json').write_text(json.dumps(self.ticket))
        with self.assertRaises(FileExistsError):
            claim_native_once(other,out,self.manifest,out/'attempt-ticket.json',guard_base=self.guard_base)

    def test_expected_target_required(self):
        data=json.loads((ROOT/'results/inventory-user-extract-20260921.json').read_text())['inventory']
        p=self.output/'inventory-test/inventory.json';p.parent.mkdir();p.write_text(json.dumps(data),encoding='utf-8-sig')
        self.assertEqual(target_inventory(self.output,self.auth['target'])['model'],'Zenbook A14 UX3407NA')
        data['manufacturer']='HP';p.write_text(json.dumps(data))
        with self.assertRaises(ValueError):target_inventory(self.output,self.auth['target'])


class RuntimeControlTests(unittest.TestCase):
    def test_pinned_ort_constructor_failure_never_retries_when_disabled(self):
        import onnxruntime as ort
        self.assertEqual(ort.__version__,'1.30.0')
        # Test the real wrapper's failure branch; mock creation before any model load.
        with mock.patch.object(ort.InferenceSession,'_create_inference_session',side_effect=RuntimeError('host fixture: creation failed')) as create:
            with self.assertRaisesRegex(RuntimeError,'host fixture'):
                ort.InferenceSession('never-opened.onnx',enable_fallback=False)
            self.assertEqual(create.call_count,1)

    def test_every_session_constructor_disables_wrapper_retry(self):
        tree=ast.parse((HERE/'control/run_smoke.py').read_text())
        constructors=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='InferenceSession']
        self.assertEqual(len(constructors),2)
        for node in constructors:
            self.assertTrue(any(k.arg=='enable_fallback' and isinstance(k.value,ast.Constant) and k.value.value is False for k in node.keywords))

    def test_precision_provider_options_and_thread_policy_unchanged(self):
        def selected_ast(path):
            tree=ast.parse(path.read_text())
            options=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and
                any(isinstance(t,ast.Name) and t.id=='provider_options' for t in n.targets))
            thread_policy=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='opts')
            return ast.dump(options),ast.dump(thread_policy)
        self.assertEqual(selected_ast(HERE/'control/run_smoke.py'),selected_ast(ROOT/'bundle/run_smoke.py'))


if __name__=='__main__':unittest.main()
