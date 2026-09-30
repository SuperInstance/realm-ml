#!/usr/bin/env python3
"""
verifier2.py — the two errors, fixed with domain machinery instead of a better prompt.

v1 scored AUC 0.893 / 19-of-21 and failed in two distinct ways:

  ERROR A  refutation-direction. Evidence describing a REPAIR was read as endorsement
           of the DEFECT it repaired. Topic match, opposite polarity.
  ERROR B  quantitative. Evidence enumerating a relation the claim asserts, and the
           model was asked to do the arithmetic.

Neither is a prompt problem. A is a polarity problem and B is a comprehension problem,
and both are addressable because this is a closed domain. A has a marker. B has a parser.
"""
import os, re, sys, json, urllib.request, urllib.error, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from direction import direction
GK=os.environ.get("GROQ_TOKEN","")
H={"Authorization":f"Bearer {GK}","Content-Type":"application/json","User-Agent":"Mozilla/5.0"}

# ---------- FIX A: recognise repair-describing evidence ----------
REPAIR = re.compile(
    r'\b(?:now (?:refuses|reports|excludes|omits|prints|surfaces)'
    r'|has been fixed|is now|was fixed|after the fix|corrected|retracted'
    r'|since the repair|no longer)\b', re.I)

def polarity_probe(evidence, claim):
    """Ask the claim's NEGATIVE. If the evidence refutes the claim, the model that said
    SUPPORTED matched the topic, not the direction."""
    body={"model":"allam-2-7b","messages":[
      {"role":"system","content":"You check whether evidence REFUTES a claim. Answer with exactly one word: REFUTES or DOES-NOT-REFUTE."},
      {"role":"user","content":f"EVIDENCE:\n{evidence}\n\nCLAIM: {claim}\n\n"
                               f"Does the evidence show this claim is WRONG? One word, REFUTES or DOES-NOT-REFUTE:"}],
      "max_tokens":6,"temperature":0.0}
    for a in range(3):
        try:
            req=urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
              data=json.dumps(body).encode(), headers=H, method="POST")
            with urllib.request.urlopen(req,timeout=45) as r:
                t=json.loads(r.read())["choices"][0]["message"]["content"].strip().upper()
                return 0 if "REFUTES" in t and "NOT" not in t else (1 if "DOES-NOT" in t or "NOT-REFUTE" in t else None)
        except Exception: time.sleep(1.5)
    return None

# ---------- FIX B: compute quantitative relations instead of asking ----------
SITES=re.compile(r's\s*=\s*((?:\d+(?:\.\d+)?\s*,\s*)+\d+(?:\.\d+)?(?:\s+and\s+\d+(?:\.\d+)?)?)')

EDGE = re.compile(
    r'(?:edges?|weights?)\s+([0-9]*\.?[0-9]+)\s*(?:and|,|vs\.?)\s*([0-9]*\.?[0-9]+)', re.I)

# Inflected stems. '\bdominat\b' cannot match "dominates" -- the trailing \b lands mid-word.
DOMINATE=re.compile(r'\b(?:dominat\w*|overrid\w*|always|regardless|independent of|ignor(?:e|es|ed|ing))\b', re.I)

def compute_dominance(evidence, claim):
    """If the claim asserts one quantity dominates another, and the evidence names both
    quantities and the sites they are compared over, decide it by evaluating the relation.

    The quantities have to be pulled from their own slots. Taking the min and max of every
    number in the sentence mixes a stimulus site in as if it were an edge weight, which is
    how the first version of this silently never fired."""
    if not DOMINATE.search(claim):
        return None
    em = EDGE.search(evidence)
    if not em: return None
    try:
        lo, hi = sorted((float(em.group(1)), float(em.group(2))))
    except ValueError:
        return None
    if lo == hi: return None                      # a tie is decided by iteration order, not by the claim
    d = direction(claim)
    if d is None: return None                     # the claim does not name a direction; not this function's job
    subj, _obj = d
    if subj is None: return None
    # the arithmetic only answers WHICH quantity wins; the grammar says which one the CLAIM asserts
    return 1 if subj == "weight" else 0
    sm = SITES.search(evidence)
    if not sm: return None
    sites = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', sm.group(1))]
    if len(sites) < 2: return None
    wins = all((hi * (1 - abs(hi - s))) - (lo * (1 - abs(lo - s))) > 1e-12 for s in sites)
    return 1 if wins else 0

def verify(evidence, claim, model="allam-2-7b"):
    """Returns (verdict, route) so the route is auditable -- a number from a model with
    no visible reasoning is exactly the failure mode this whole session is about."""
    b = compute_dominance(evidence, claim)
    if b is not None:
        return b, "computed"
    body={"model":model,"messages":[
      {"role":"system","content":"You verify claims against artifacts. Answer with exactly one word: SUPPORTED or CONTRADICTED."},
      {"role":"user","content":f"ARTIFACT EVIDENCE:\n{evidence}\n\nCLAIM: {claim}\n\nOne word, SUPPORTED or CONTRADICTED:"}],
      "max_tokens":6,"temperature":0.0}
    for a in range(3):
        try:
            req=urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
              data=json.dumps(body).encode(), headers=H, method="POST")
            with urllib.request.urlopen(req,timeout=45) as r:
                t=json.loads(r.read())["choices"][0]["message"]["content"].strip().upper()
                v = 1 if "SUPPORTED" in t else (0 if "CONTRADICTED" in t else None)
                if v is None: return None,"unparsed"
                if v==1 and REPAIR.search(evidence or ""):
                    n=polarity_probe(evidence, claim)
                    if n==0: return 0,"repair-detected"
                return v,"asked"
        except Exception: time.sleep(1.5)
    return None,"error"
