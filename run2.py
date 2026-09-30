import sys, os, json, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from corpus import CORPUS
from verifier2 import verify
def auc(p):
    pos=sorted(x for y,x in p if y==1); neg=sorted(x for y,x in p if y==0)
    if not pos or not neg: return float('nan')
    n=s=0
    for a in pos:
        for b in neg:
            n+=1; s+= 1.0 if a>b else (0.5 if a==b else 0.0)
    return s/n
rows=[]; t0=time.time()
for lab, claim, ev, truth in CORPUS:
    v,route=verify(ev,claim)
    rows.append({"label":lab,"truth":truth,"pred":v,"route":route})
    m="  " if truth is None else ("ok" if v==truth else "MISS")
    print(f"  {m} {lab:12} t={truth}  pred={v}  via={route}", flush=True)
L=[r for r in rows if r["truth"] is not None and r["pred"] is not None]
print(f"\n  n={len(L)}  wall={time.time()-t0:.0f}s")
print(f"  v2  AUC {auc([(r['truth'],float(r['pred'])) for r in L]):.3f}  "
      f"accuracy {sum(1 for r in L if r['pred']==r['truth'])/len(L):.3f}  "
      f"({sum(1 for r in L if r['pred']==r['truth'])}/{len(L)})")
from collections import Counter
print("  routes:", dict(Counter(r['route'] for r in rows)))
json.dump(rows, open("/workspace/research/realm-ml/v2_result.json","w"), indent=1)
