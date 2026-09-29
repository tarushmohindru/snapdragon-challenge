"""Budgeted timestamp selection. Score access is explicit; no model implied."""
def uniform(n, budget):
    if n<1 or budget<1: return []
    budget=min(n,budget)
    if budget==1:return [n//2]
    return sorted({round(i*(n-1)/(budget-1)) for i in range(budget)})


def changed(change,budget):
    selected=[]
    for i in sorted(range(len(change)),key=lambda i:(-change[i],i)):
        if all(abs(i-j)>2 for j in selected): selected.append(i)
        if len(selected)==budget:break
    for i in uniform(len(change),len(change)):
        if len(selected)==budget:break
        if i not in selected:selected.append(i)
    return sorted(selected)


def hierarchical(n,budget,encode_score):
    """Half uniform; repeatedly bisect around strongest observed anchors.

    encode_score only called on selected timestamps, and at most budget times.
    Tie-breaking is deterministic. This algorithm cannot recover unobserved
    semantic clues by magic; no-hint cases must be evaluated explicitly.
    """
    budget=min(n,budget)
    scores={i:encode_score(i) for i in uniform(n,max(2,budget//2))[:budget]}
    while len(scores)<budget:
        ordered=sorted(scores);options=[]
        for a,b in zip(ordered,ordered[1:]):
            if b-a>1:options.append((max(scores[a],scores[b]),b-a,-a,(a+b)//2))
        if not options:break
        i=max(options)[-1];scores[i]=encode_score(i)
    return sorted(scores)
