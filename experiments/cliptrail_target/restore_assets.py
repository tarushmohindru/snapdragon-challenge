"""Restore exact locked public downloads. Does not resolve versions or run inference."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'bundle'))
from target_common import sha
from provision_assets import download


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    lock=json.loads((ROOT/'results/provisioning.json').read_text())
    runtime=lock['runtime_selection']
    records=[m for m in lock['models'].values() if m.get('status')=='downloaded']
    records += [runtime['python_embed']]+runtime['wheels']
    for entry in records:
        path=(ROOT/entry['file']).resolve()
        if not path.is_relative_to((ROOT/'assets').resolve()):raise ValueError('Unexpected locked download path')
        if path.exists():
            if sha(path)!=entry['sha256']:raise ValueError('Existing download hash mismatch: '+str(path))
            print('Verified',path.name)
        elif args.verify_only:raise FileNotFoundError(path)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            download(entry['url'],path,expected=entry['sha256'])
    print('Locked assets verified. No inference performed.')


if __name__=='__main__':main()
