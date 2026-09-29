#!/usr/bin/env python3
"""Mechanistic oracle experiment: not real CLIP accuracy."""
import hashlib,json,platform
from pathlib import Path
from sampling import uniform,changed,hierarchical

ROOT=Path(__file__).resolve().parent
def main():
    n,budget=240,16
    cases=[]
    for name,onset,duration,hint,distractors in (
        ('short_with_precursor',103,5,True,False),
        ('short_no_hint',103,5,False,False),
        ('short_distractor_cuts',103,5,False,True),
        ('long_state',80,65,False,True)):
        scores=[.1]*n;motion=[0.]*n
        for i in range(onset,onset+duration):scores[i]=1.
        if hint:
            for i in range(onset-30,onset):scores[i]=.7*(i-(onset-30))/30+.1
        motion[onset]=.2;motion[onset+duration]=.2
        if distractors:
            for i in range(3,n,7):motion[i]=.9
        for method in ('uniform','change','hierarchical','hybrid'):
            queried=[]
            def encode(i):queried.append(i);return scores[i]
            if method=='hierarchical':selected=hierarchical(n,budget,encode)
            elif method=='uniform':selected=uniform(n,budget)
            elif method=='change':selected=changed(motion,budget)
            else:
                selected=uniform(n,budget//2)
                for i in changed(motion,n):
                    if len(selected)==budget:break
                    if i not in selected:selected.append(i)
            if method!='hierarchical':
                for i in selected:encode(i)
            assert len(queried)==len(set(queried))<=budget
            ranked=sorted(selected,key=lambda i:(-scores[i],i))[:5]
            cases.append(dict(case=name,method=method,image_encodes=len(queried),budget=budget,
                              event_interval=[onset,onset+duration],selected=selected,top5=ranked,
                              hit5=any(onset<=i<onset+duration for i in ranked)))
    result=dict(provenance='SIMULATED score oracle, NOT CLIP embeddings or retrieval benchmark',
                host=platform.platform(),frames=n,results=cases,
                algorithm_sha256=hashlib.sha256((ROOT/'sampling.py').read_bytes()).hexdigest())
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results/sampling-oracle.json').write_text(json.dumps(result,indent=2))
    for c in cases:print(c['case'],c['method'],'hit5',c['hit5'],'calls',c['image_encodes'])
if __name__=='__main__':main()
