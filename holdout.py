#!/usr/bin/env python3
"""
holdout.py — 23 cases written by the same author, in the same hour, about the same
repositories is a training set wearing a test set's clothes. These are fresh cases
with a different shape: different repositories, different verbs, claims that were
never part of the original corpus, and labels set before the verifier saw them.
"""
import sys, os, json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from verifier2 import verify
HELD = [
 ("moltresp","test-binary-v1 returns any binary file unprocessed.",
  "Engine test-binary-v1: POST a PNG, receive the identical byte sequence back. sha256 of input equals sha256 of output, matched on three files.", 1),
 ("wolff","wolffs-law's torus conductance for the a-by-b family is exactly 4/max(a,b).",
  "Recomputed symbolically: conductance = 4/max(a,b) for every a,b tested at (3,5), (5,3), (4,4). Substituting N for max(a,b) overstates it by up to 30x.", 1),
 ("wolff_bad","wolffs-law's torus conductance for the a-by-b family is exactly 4/N where N is the larger side.",
  "Recomputed symbolically: conductance = 4/max(a,b) for every a,b tested at (3,5), (5,3), (4,4).", 0),
 ("moth_stoch","MOTH Qpixl returns the same array for the same input every time at 1000 shots.",
  "Repeated 200 draws at 1000 shots. The returned array differed across draws; the output is a single sample from a distribution, not a decode.", 0),
 ("moth_stoch2","MOTH Qpixl is a single sample from a distribution rather than a deterministic decode.",
  "Repeated 200 draws at 1000 shots. The returned array differed across draws; the output is a single sample from a distribution, not a decode.", 1),
 ("github","github can enumerate the public repositories owned by an organization.",
  "GET /orgs/SuperInstance/repos returned a JSON array of 39 repository objects with name, pushed_at and language fields.", 1),
 ("github_bad","github can read a private repository belonging to another user without authentication.",
  "GET /repos/<other-org>/<private> returned 404 Not Found for an unauthenticated request. Private repositories are invisible without credentials.", 0),
 ("canary_bad","FNV-1a 64 of the UTF-8 bytes of the string cafe Delta shinjitai is 0x024a555471370b19d.",
  "Julia QuiltCanary.canary() returns 0x024a555471370b18d, 13/13 tests pass. The final nibble is 8d, not 9d.", 0),
 ("repair","The README verifier publishes a drift rate even when some repositories cannot be read.",
  "census.py now refuses to publish a rate when any repository is unreadable, and exits non-zero instead. This was a fix to an earlier behaviour.", 0),
 ("repair2","The README verifier silently drops unreadable repositories from its denominator.",
  "census.py now refuses to publish a rate when any repository is unreadable, and exits non-zero instead.", 0),
]
rows=[]; 
for lab, claim, ev, truth in HELD:
    v,route = verify(ev, claim)
    rows.append({"label":lab,"truth":truth,"pred":v,"route":route})
    print(f"  {'ok ' if v==truth else 'MISS'} {lab:12} truth={truth} pred={v} via={route}", flush=True)
n=len(rows); acc=sum(1 for r in rows if r['pred']==r['truth'])/n
pos=[r for r in rows if r['truth']==1]; neg=[r for r in rows if r['truth']==0]
def auc():
    P=sorted(r['pred'] for r in pos); N=sorted(r['pred'] for r in neg)
    s=0.0; t=0
    for a in P:
        for b in N:
            t+=1; s+= 1.0 if a>b else (0.5 if a==b else 0.0)
    return s/t
print(f"\n  HELD-OUT  n={n}  accuracy {acc:.3f} ({sum(1 for r in rows if r['pred']==r['truth'])}/{n})  AUC {auc():.3f}")
from collections import Counter
print("  routes:", dict(Counter(r['route'] for r in rows)))
json.dump(rows, open("/workspace/research/realm-ml/holdout_result.json","w"), indent=1)
