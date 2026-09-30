#!/usr/bin/env python3
import sys, os, json, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from corpus import CORPUS
from verifier import groq_judge, jev_relevance, claim_features, evidence_kind

def auc(pairs):
    pos=sorted(p for y,p in pairs if y==1); neg=sorted(p for y,p in pairs if y==0)
    if not pos or not neg: return float('nan')
    n=s=0
    for a in pos:
        for b in neg:
            n+=1; s+= 1.0 if a>b else (0.5 if a==b else 0.0)
    return s/n

rows=[]
t0=time.time()
for lab, claim, ev, truth in CORPUS:
    g=groq_judge(ev, claim)
    j=jev_relevance(ev, claim)
    f=claim_features(claim); k=evidence_kind(ev)
    rows.append({"label":lab,"truth":truth,"groq":g,"jev":j,"ev_kind":k,**f})
    mark = "  " if truth is None else ("ok" if g==truth else "MISS")
    print(f"  {mark} {lab:12} t={truth}  groq={g}  jev={j if j is None else round(j,3)}  {k:10} "
          f"sym={int(f['c_symbol'])} cnt={int(f['c_count'])} path={int(f['c_path'])} num={int(f['c_number'])}", flush=True)

L=[r for r in rows if r["truth"] is not None and r["groq"] is not None]
J=[r for r in rows if r["truth"] is not None and r["jev"] is not None]
print(f"\n  n labelled+answered: groq={len(L)} jev={len(J)}   wall={time.time()-t0:.0f}s")
if L:
    a=auc([(r["truth"],float(r["groq"])) for r in L])
    acc=sum(1 for r in L if r["groq"]==r["truth"])/len(L)
    print(f"  GROQ  AUC {a:.3f}   accuracy {acc:.3f}  ({sum(1 for r in L if r['groq']==r['truth'])}/{len(L)})")
    print(f"        mean(true)={sum(r['groq'] for r in L if r['truth']==1)/max(1,sum(1 for r in L if r['truth']==1)):.3f}"
          f"  mean(false)={sum(r['groq'] for r in L if r['truth']==0)/max(1,sum(1 for r in L if r['truth']==0)):.3f}")
if J:
    a=auc([(r["truth"],r["jev"]) for r in J])
    print(f"  JEV   AUC {a:.3f}   mean(true)={sum(r['jev'] for r in J if r['truth']==1)/max(1,sum(1 for r in J if r['truth']==1)):.3f}"
          f"  mean(false)={sum(r['jev'] for r in J if r['truth']==0)/max(1,sum(1 for r in J if r['truth']==0)):.3f}")
# per evidence-kind accuracy -- the realm-specific question
print("\n  accuracy by evidence kind (groq):")
for k in sorted({r["ev_kind"] for r in L}):
    g=[r for r in L if r["ev_kind"]==k]
    print(f"    {k:10} n={len(g):2}  acc={sum(1 for r in g if r['groq']==r['truth'])/len(g):.2f}")
json.dump(rows, open("/workspace/research/realm-ml/corpus_result.json","w"), indent=1)
