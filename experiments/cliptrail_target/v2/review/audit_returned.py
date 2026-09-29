"""Read-only checks of returned v2 evidence. No runtime/model loading or inference.

Run with .venv-cliptrail-target-tools/bin/python; emits JSON to stdout only.
"""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
TARGET = ROOT / 'experiments/cliptrail_target'
sys.path.insert(0, str(TARGET / 'bundle'))
from evidence_rules import PARITY, embedding_parity, provider_evidence


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    archive = ROOT / 'smoke-v2-20260921T123814481Z-9573326e.zip'
    lock = json.loads((TARGET / 'v2/v1-preservation-lock.json').read_text())
    historical = {n: sha((ROOT / n).read_bytes()) == h for n, h in lock['files'].items()}
    assert all(historical.values()), 'Historical v1 artifact changed'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        names = z.namelist()
        normalized = [n.replace('\\', '/') for n in names]
        assert len(set(normalized)) == len(names)
        assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
                   and ':' not in n for n in normalized)
        data = {n: z.read(n) for n in names}
        read = lambda n: json.loads(data[n].decode('utf-8-sig'))
        hashes = read('evidence-hashes-v2.json')
        assert set(hashes) == set(names) - {'evidence-hashes-v2.json'}
        assert all(sha(data[n]) == h for n, h in hashes.items())
        manifest = read('bundle-manifest-v2.json')
        assert data['bundle-manifest-v2.json'] == (TARGET / 'v2/smoke-manifest-v2.json').read_bytes()
        assert data['authorization-v2.json'] == (TARGET / 'v2/authorization-v2.json').read_bytes()
        smoke = read('smoke.json')
        outcome = read('smoke-outcome-v2.json')
        assert smoke['manifest_sha256'] == outcome['manifest_sha256'] == sha(data['bundle-manifest-v2.json'])
        assert smoke['calls'] == smoke['run_attempts'] == smoke['session_creation_attempts'] == {'cpu': 1, 'qnn': 1}
        assert outcome['status'] == 'INCOMPLETE_EVIDENCE' and not outcome['timed_out']
        assert outcome['native_exit_code_hex'] == read('native-child.json')['native_exit_code_hex'] == 'C0000005'
        assert read('attempt-ticket.json')['token'] == smoke['attempt_claim']['token']
        for name, expected in smoke['result_hashes'].items():
            assert sha(data[name]) == expected
        reference_bytes = (TARGET / 'bundle/input/cpu_reference.npy').read_bytes()
        assert sha(reference_bytes) == smoke['reference_sha256']
        reference = np.load(io.BytesIO(reference_bytes), allow_pickle=False)
        cpu = np.load(io.BytesIO(data['cpu_embedding.npy']), allow_pickle=False)
        qnn = np.load(io.BytesIO(data['qnn_embedding.npy']), allow_pickle=False)
        parity = {
            'cpu_vs_frozen': embedding_parity(cpu, reference, {'cosine_min': .99999, 'max_abs_max': .001}),
            'qnn_vs_frozen': embedding_parity(qnn, reference, PARITY['float']),
            'qnn_vs_target_cpu': embedding_parity(qnn, cpu, PARITY['float']),
        }
        assert all(p['pass'] for p in parity.values())
        placement = provider_evidence(read(smoke['ort_profile_file']))
        assert placement == smoke['placement']
        assert placement['only_qnn_compute']
        loaded = smoke['loaded_modules']
        assert any(m['name'].lower() == 'qnnhtp.dll' and m['inside_bundle']
                   and m['sha256'] == manifest['runtime']['htp_sha256'] for m in loaded)
        payload = manifest['files']
        inventory_name = next(n for n in names if n.startswith('inventory-'))
        inventory = read(inventory_name)
        assert inventory['manufacturer'] == 'ASUS' and inventory['model'] == 'Zenbook A14 UX3407NA'
        assert inventory['errors'] == []
        assert any('X2E88100' in p['Name'] for p in inventory['processors'])
        assert smoke['native']['native_machine'] == smoke['native']['python_pe_machine'] == '0xaa64'
        assert smoke['native']['process_machine'] == '0x0' and smoke['native']['pointer_bits'] == 64
        for item in inventory['local_runtime_files']:
            assert item['sha256'] == payload[item['path'].replace('\\', '/')]
        for filename in ['run_smoke.py', 'run_smoke.ps1', 'invoke_attempt_v2.ps1', 'attempt_policy.py']:
            assert sha((TARGET / 'v2/control' / filename).read_bytes()) == payload[filename]
        # Local shipped payload identity corroborates reported loaded module hashes.
        for m in loaded:
            if m['inside_bundle']:
                p = m['path'].replace('\\', '/')
                expected = payload[p]
                if isinstance(expected, dict): expected = expected['sha256']
                assert m['sha256'] == expected
        trace = read('qnn_op_trace.json')
        assert trace['summary']['qnn_subgraphs'] == len(trace['subgraph_traces']) == 1
        assert trace['summary']['total_qnn_ops'] == sum(len(s['op_mappings']) for s in trace['subgraph_traces'])
        assert trace['subgraph_traces'][0]['graph_name'] + '_kernel_time' == placement['executed_nodes'][0]['name']
        stages = [json.loads(l) for l in data['stages.jsonl'].decode().splitlines()]
        assert stages[-1]['stage'] == 'finished' and stages[-1]['calls'] == {'cpu': 1, 'qnn': 1}
        print(json.dumps({
            'status': 'PASSED_ARTIFACT_CONSISTENCY_NOT_HARDWARE_VERIFICATION',
            'archive': str(archive.relative_to(ROOT)), 'archive_sha256': sha(archive.read_bytes()),
            'archive_bytes': archive.stat().st_size,
            'members': [{'archive_name': n, 'normalized_path': p, 'bytes': len(data[n]), 'sha256': sha(data[n])}
                        for n, p in zip(names, normalized)],
            'recorded_hashes_checked': len(hashes), 'v1_preservation_checks': historical,
            'manifest_and_authorization_match_issued_v2': True,
            'inventory_runtime_hashes_checked': len(inventory['local_runtime_files']),
            'issued_runner_sources_match_manifest': True,
            'recomputed_parity': parity, 'recomputed_ort_placement': placement,
            'framework_trace_summary': trace['summary'], 'stages': stages,
            'missing_hardware_artifacts': ['qnn-profile.csv', 'qnn-profile_qnn.log', 'ETW .etl or hardware event export'],
            'npu_verified': False, 'new_inference_performed': False,
        }, indent=2))


if __name__ == '__main__':
    main()
