#!/usr/bin/env python3
"""
groq_labeller.py — is the cheapest model on Groq a usable truth signal for THIS realm?

JEV turned out to measure vagueness, not falsity. That leaves a hole: something has to
supply the truth signal. The only honest candidate is the artifact. This asks whether a
7B model on the cheapest tier can look at an artifact and judge a codebase claim.

Two models, because "cheapest" is ambiguous:
  allam-2-7b                      the cheapest general chat model on the account
  meta-llama/llama-prompt-guard-2-22m   22M params, 0.3s -- a CLASSIFIER, not a chat model

The 22M one matters more. It is 300x smaller and returns a float, not words. If a 22M
guard can carry any of the signal, the marginal cost of verification collapses.
"""
import os, json, time, urllib.request, urllib.error
GK=os.environ.get("GROQ_TOKEN",""); U="https://api.groq.com/openai/v1/chat/completions"
H={"Authorization":f"Bearer {GK}","Content-Type":"application/json","User-Agent":"Mozilla/5.0"}

# (label, artifact-evidence, claim, truth)
CASES=[
 ("claw","Repository file listing: README.md, LICENSE, Dockerfile, claw.toml, package.json, .github/workflows/ci.yml, tests/run.sh, docs/*.md. No routing, conservation, or gamma source files exist.",
  "The claw repository implements a ternary action routing system.",0),
 ("forgemaster","grep -rniw compile over forgemaster/src/ returns zero matches. The Forge.compile method named in the README does not exist in the source.",
  "Forgemaster's Forge.compile method exists in the source.",0),
 ("canary","Test output: QuiltCanary.canary() returns 0x024a555471370b18d, 13/13 tests pass. Python, TypeScript, Rust, C#, and Julia all produce the same digest.",
  "FNV-1a 64 of 'cafe Delta 日本語' is 0x024a555471370b18d.",1),
 ("egg","Julia port measured this: modulated edges 0.026909 and 0.028727; the heavier edge wins at s = 0.0, 0.1, 0.3, 0.5, 0.9 and 1.0. Exact ties are resolved by iteration order.",
  "In quilt-egg, relationship weight dominates the stimulus in the resonance formula.",1),
 ("vectorize","Measurement: POST /insert returned 200. GET /list showed 0 rows at t+0 and t+5s. At t+15s the row was present. The write was not dropped; the read was too early.",
  "Cloudflare Vectorize silently drops writes: the row count stays 0 forever.",0),
 ("pincher","CI run 2026-06-06 onward: job 'test (ubuntu-latest, default)' has been failing continuously. The test asserts a sandbox mechanism the runner does not provide.",
  "pincher-core's CI has been failing continuously since 2026-06-06.",1),
]
def ask(model, msgs, max_tokens=140, temp=0.0):
    for a in range(3):
        try:
            req=urllib.request.Request(U, data=json.dumps(
                {"model":model,"messages":msgs,"max_tokens":max_tokens,"temperature":temp}).encode(),
                headers=H, method="POST")
            with urllib.request.urlopen(req,timeout=45) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e: err=f"HTTP{e.code}"
        except Exception as e: err=str(e)[:50]
        time.sleep(1.5)
    return {"err":err}
def auc(pairs):
    pos=sorted(p for y,p in pairs if y==1); neg=sorted(p for y,p in pairs if y==0)
    if not pos or not neg: return float('nan')
    n=s=0
    for a in pos:
        for b in neg:
            n+=1; s+= 1.0 if a>b else (0.5 if a==b else 0.0)
    return s/n

if __name__=="__main__":
    print("  === A. the 7B chat model, asked to judge ===")
    rows=[]
    for lab,ev,claim,truth in CASES:
        t0=time.time()
        d=ask("allam-2-7b",[
          {"role":"system","content":"You verify claims against artifacts. Answer with exactly one word: SUPPORTED or CONTRADICTED."},
          {"role":"user","content":f"ARTIFACT EVIDENCE:\n{ev}\n\nCLAIM: {claim}\n\nOne word, SUPPORTED or CONTRADICTED:"}])
        dt=time.time()-t0
        txt=(d.get("choices",[{}])[0].get("message",{}).get("content","") if "choices" in d else str(d.get("err")))
        pred = 1 if "SUPPORTED" in txt.upper() else (0 if "CONTRADICTED" in txt.upper() else None)
        rows.append((lab,truth,pred,txt.strip()[:26],dt))
        ok = "ok " if pred==truth else "MISS"
        print(f"    {ok} {lab:11} truth={truth} said={txt.strip()[:22]!r:26} {dt:.1f}s")
    scored=[(t,p) for _,t,p,_,_ in rows if p is not None]
    if scored:
        acc=sum(1 for t,p in scored if t==p)/len(scored)
        print(f"    {len(scored)}/{len(rows)} parseable, accuracy {acc:.2f}, AUC {auc([(t,float(p)) for t,p in scored]):.3f}")

    print("\n  === B. the 22M guard, as a raw score ===")
    g=[]
    for lab,ev,claim,truth in CASES:
        t0=time.time()
        d=ask("meta-llama/llama-prompt-guard-2-22m",
              [{"role":"user","content":f"{ev}\n\n{claim}"}], max_tokens=8)
        dt=time.time()-t0
        raw=(d.get("choices",[{}])[0].get("message",{}).get("content","") if "choices" in d else str(d.get("err")))
        try: v=float(raw.strip())
        except Exception: v=None
        g.append((lab,truth,v,raw.strip()[:20],dt))
        print(f"    {lab:11} truth={truth}  raw={raw.strip()[:18]!r:22} {dt:.1f}s")
    gp=[(t,v) for _,t,v,_,_ in g if v is not None]
    if len(gp)==len(g):
        print(f"    AUC {auc(gp):.3f}   (0.5 = no signal, >0.7 = usable, <0.3 = inverted)")
    json.dump({"chat":[{"label":l,"truth":t,"pred":p,"raw":r,"sec":d} for l,t,p,r,d in rows],
               "guard":[{"label":l,"truth":t,"score":v,"raw":r} for l,t,v,r,_ in g]},
              open("/workspace/research/realm-ml/groq_result.json","w"), indent=1)
