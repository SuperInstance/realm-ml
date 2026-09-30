#!/usr/bin/env python3
"""
verifier.py — realm-specific claim verification.

THE REALM: statements the fleet makes about its own code. Not math, not prose, not
world-knowledge. Claims that name a symbol, a file, a count, or a number, and that
can be settled by looking.

That constraint is the whole algorithm. A claim is verifiable iff its evidence is
*mechanical*. So the features are not embeddings and not topics -- they are the kinds
of thing that can be checked:

  ev_listing   a file listing
  ev_grep      a search result with a match count
  ev_test      test output with a pass/fail count
  ev_exec      a measurement with a number
  ev_none      a claim shipped with no evidence at all     <- the dangerous case

and the claim side:

  c_symbol     names a function/method
  c_count      names a quantity of things
  c_path       names a file or directory
  c_number     states a literal value

A model trained on that vocabulary cannot generalise to sentiment, factuality or
safety. That is the point. It only has to be right about THIS.
"""
import os, json, re, urllib.request, urllib.error, time
GK=os.environ.get("GROQ_TOKEN",""); TK=os.environ.get("TYPESAFEAI_KEY","")
H={"Authorization":f"Bearer {GK}","Content-Type":"application/json","User-Agent":"Mozilla/5.0"}

# --- the claim-side feature extractors, written against the fleet's own vocabulary ---
SYMBOL=re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(|\.([a-z_][a-z0-9_]*)\s*\(')
COUNT =re.compile(r'\b(\d+)\s+(tests?|files?|engines?|methods?|claims?|repos?|ports?|opcodes?|languages?)\b', re.I)
PATH  =re.compile(r'`?([\w./-]+\.(?:py|ts|rs|js|jl|md|toml|yml|yaml|json|html))`?')
NUMBER=re.compile(r'\b0x[0-9a-f]+\b|\b\d+\.\d+\b|\b\d{2,}\b')

def claim_features(c):
    sym=SYMBOL.findall(c); sym=[a or b for a,b in sym]
    cnt=COUNT.findall(c)
    return {"c_symbol": float(bool(sym)), "c_count": float(bool(cnt)),
            "c_path": float(bool(PATH.search(c))), "c_number": float(bool(NUMBER.search(c)))}

def evidence_kind(ev):
    e=(ev or "").lower()
    if not e.strip(): return "ev_none"
    if "listing" in e or "no such file" in e or "file listing" in e: return "ev_listing"
    if re.search(r'grep|0 matches|zero matches|\b\d+ matches', e): return "ev_grep"
    if re.search(r'test|tests pass|assert|fail', e): return "ev_test"
    if re.search(r'measur|t\+|returned|http \d|status', e): return "ev_exec"
    return "ev_other"

# --- verifiers ---
def groq_judge(evidence, claim, model="allam-2-7b"):
    for a in range(3):
        try:
            body={"model":model,"messages":[
              {"role":"system","content":"You verify claims against artifacts. Answer with exactly one word: SUPPORTED or CONTRADICTED."},
              {"role":"user","content":f"ARTIFACT EVIDENCE:\n{evidence}\n\nCLAIM: {claim}\n\nOne word, SUPPORTED or CONTRADICTED:"}],
              "max_tokens":6,"temperature":0.0}
            req=urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(body).encode(), headers=H, method="POST")
            with urllib.request.urlopen(req,timeout=45) as r:
                t=json.loads(r.read())["choices"][0]["message"]["content"].strip().upper()
                return 1 if "SUPPORTED" in t else (0 if "CONTRADICTED" in t else None)
        except Exception: time.sleep(1.5)
    return None

def jev_relevance(evidence, claim):
    for a in range(3):
        try:
            body={"model":"jev-latest","state":evidence or claim,"questions":{"q":{"type":"noul",
              "instructions":"Is this claim true as stated, and would a careful reader who knows the subject agree?",
              "criteria":{"true":"The claim is accurate, specific, and verifiable.","false":"The claim is false, vague, or unverifiable."}}}}
            req=urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=json.dumps(body).encode(),
              headers={"Authorization":f"Bearer {TK}","Content-Type":"application/json"}, method="POST")
            with urllib.request.urlopen(req,timeout=60) as r:
                v=json.loads(r.read())["answers"]["q"]
                return float(v.get("noul", v.get("answer",{}).get("noul",-1)))
        except Exception: time.sleep(1.5)
    return None
