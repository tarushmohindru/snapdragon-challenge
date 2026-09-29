"""Read-only audit of tracked public files (alternate Git metadata supported)."""
from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[2]
GIT=['git','--git-dir=.publication.git','--work-tree=.']
paths=[Path(p) for p in subprocess.check_output(GIT+['ls-files','-z'],cwd=ROOT).decode().split('\0') if p]
errors=[]
json_count=0
link_count=0
secret_hits=[]
large=[]
for rel in paths:
    p=ROOT/rel
    if not p.is_file(): errors.append(f'missing: {rel}'); continue
    if p.stat().st_size > 5_000_000: large.append((str(rel),p.stat().st_size))
    if rel.suffix=='.json':
        try: json.loads(p.read_text(encoding='utf-8-sig')); json_count+=1
        except Exception as e: errors.append(f'JSON {rel}: {e}')
    if rel.suffix.lower() not in {'.md','.txt','.py','.sh','.ps1','.html','.js','.css','.json','.jsonl'}: continue
    try: s=p.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError: continue
    if '-----BEGIN '+'PRIVATE KEY-----' in s or 'gh'+'p_' in s or 'github_'+'pat_' in s or re.search(r'AKIA[0-9A-Z]{16}',s):
        secret_hits.append(str(rel))
    if re.search(r'(?i)\b(?:api[_-]?key|client[_-]?secret|password|access[_-]?token)\s*[=:]\s*["\']?[^\s"\']{12,}',s):
        secret_hits.append(str(rel))
    if rel.suffix=='.md':
        for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)|!\[[^\]]*\]\(([^)]+)\)',s):
            link=(target[0] or target[1]).split(' ',1)[0].strip('<>')
            if link.startswith(('http://','https://','mailto:','#','data:')): continue
            local=unquote(link.split('#')[0].split('?')[0])
            if local and not (p.parent/local).exists(): errors.append(f'broken link {rel}: {link}')
            link_count+=1
print(json.dumps({'tracked_files':len(paths),'total_bytes':sum((ROOT/p).stat().st_size for p in paths),'json_validated':json_count,'local_links_checked':link_count,'files_over_5MB':large,'secret_pattern_hits':sorted(set(secret_hits)),'errors':errors},indent=2))
if errors or large or secret_hits: raise SystemExit(1)
