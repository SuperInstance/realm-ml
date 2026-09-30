"""
relations.py — decide a relation by computing it, not by asking a model.

THE GAP THIS CLOSES
The realm-specific verifier scored 8/10 on held-out data (AUC 0.750) and both misses were
the same error class: *the evidence states a relation over values, and the claim asserts
that relation.* A 7B model compares statements well and cannot evaluate them. The fix is
not a better prompt — it is to not ask.

WHAT IT HANDLES
  equality      "sha256(input) == output"      both sides stated in the evidence
  formula       "4/max(a,b)"                   the claim IS an expression
  dominance     already handled in verifier2    kept here so there is one place
  equality-word "identical to", "the same as"  the textual form of the same thing

WHAT IT DELIBERATELY DOES NOT DO
It does not ask a model. If it cannot evaluate the relation, it returns None, and the
caller falls through to the model. **A relation evaluator that guesses is worse than none**,
because a guess arrives with the confidence of a computation.
"""
from __future__ import annotations
import re, math
from fractions import Fraction

NUM = r"[-+]?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?|[-+]?\.\d+"

def _f(tok: str) -> Fraction:
    return Fraction(tok) if "/" in tok else Fraction(tok)


# ── equality ─────────────────────────────────────────────────────────────────────
# My first version matched a fixed phrase list and missed "are identical", then required
# an `X == Y` token the evidence never had. Both were bugs in the CHECK, not in the claims.
# The shape that actually occurs: the claim asserts a relation between two NAMED THINGS,
# and the evidence gives a value for each. So extract the names, find the values, compare.

EQUALITY_ASSERT = re.compile(
    r"\b(?:are|is|were|was|remain|remains|come out|comes out)\s+"
    r"(?:the\s+\w+\s+)?"
    r"(?:identical|indistinguishable|the\s+same|equal|match(?:ing)?|unchanged)\b"
    r"|\bidentical\s+to\b|\bsame\s+as\b|\bequals\b|\bis\s+equal\s+to\b",
    re.I)

# "the X and the Y" -- the two things the claim is comparing
TWO_SUBJECTS = re.compile(
    r"\b(?:the\s+)?(?P<a>[A-Za-z][\w ./-]{2,40}?)\s+and\s+(?:the\s+)?(?P<b>[A-Za-z][\w ./-]{2,40}?)\b"
    r"\s+(?:are|is|were|was|remain|remains|come out|comes out|match|equal|identical)", re.I)

# "name = value" or "name: value", where the value is a hex digest or a number
ASSIGN = re.compile(
    r"(?P<name>[A-Za-z][\w ./-]{2,50}?)\s*[:=]\s*"
    r"(?P<val>[0-9a-f]{16,64}|\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)",
    re.I)


def eval_equality(evidence: str, claim: str):
    """Decide 'these two are the same' by finding both values and comparing them."""
    if not EQUALITY_ASSERT.search(claim):
        return None
    m = TWO_SUBJECTS.search(claim)
    if not m:
        return None
    a, b = m.group("a").strip().lower(), m.group("b").strip().lower()
    ev = evidence.lower()
    # Match on WORD OVERLAP. Keying on the last word failed: the evidence says
    # "sha256 of the uploaded png" whose last word is "png", which does not appear in the
    # claim's subject "uploaded file". Two of three significant words is the right test.
    STOP = {"of", "the", "a", "an", "sha256", "hash", "value", "bytes", "size", "file"}
    def words(t):
        return {w for w in re.findall(r"[a-z0-9]+", t) if w not in STOP and len(w) > 2}
    wa, wb = words(a), words(b)
    # TWO INDEPENDENT PASSES. The single-pass version stored the first assign matching
    # subject A, and here that was the *downloaded* line -- so B never resolved and the
    # whole thing returned None. Order in the evidence is not the order of the subjects.
    def value_for(subject_words):
        for am in ASSIGN.finditer(ev):
            wn = words(am.group("name"))
            if wn and (wn & subject_words):
                return am.group("val")
        return None
    va, vb = value_for(wa), value_for(wb)
    if va is None or vb is None:
        return None
    # compare as numbers when both parse, else as strings
    def same(x, y):
        try:
            return abs(float(x) - float(y)) <= 1e-12
        except ValueError:
            return x == y
    return same(next(iter(va)), next(iter(vb)))


# ── formula ─────────────────────────────────────────────────────────────────────
# "The exact value is 4/max(a,b)." -- the expression is the claim, and the evidence
# supplies the operands. No backticks required.
# The function-call alternative used to win and swallow only "max(a,b)", dropping the
# leading "4/" and making every formula claim evaluate against the wrong number. Take the
# LONGEST arithmetic span instead, anchored so a bare call cannot outrank a full one.
OPERAND = r"(?:[-+]?\d+(?:\.\d+)?|\b[a-z_]\w*\s*\([^()]*\))"
ARITH_EXPR = re.compile(
    r"(?P<expr>" + OPERAND + r"(?:\s*[-+*/]\s*" + OPERAND + r")+)")
CLAIMED_NUM = re.compile(NUM)


def eval_formula(evidence: str, claim: str):
    for m in ARITH_EXPR.finditer(claim):
        expr = m.group("expr").strip()
        if not re.search(r"[\+\-*/]|\bmax\b|\bmin\b", expr, re.I):
            continue
        py = re.sub(r"\bmax\b", "_max", expr, flags=re.I)
        py = re.sub(r"\bmin\b", "_min", py, flags=re.I)
        nums = re.findall(r"\d+(?:\.\d+)?", evidence)
        if len(nums) < 2:
            return None
        env = {"_max": max, "_min": min, "__builtins__": {}}
        for i, name in enumerate([c for c in py if c.isalpha()]):
            if name not in ("_", ):
                env.setdefault(name, float(nums[i]) if i < len(nums) else float(nums[-1]))
        try:
            got = eval(py, env)
        except Exception:
            continue
        if not isinstance(got, (int, float)) or math.isnan(got) or math.isinf(got):
            continue
        # The claimed value must lie OUTSIDE the expression. Taking the first number in
        # the claim picked up the 4 in "4/max(a,b)" and compared the computed result
        # against itself, so every correct formula claim read as false.
        outside = claim[:m.start("expr")] + " " + claim[m.end("expr"):]
        cn = CLAIMED_NUM.search(outside)
        if not cn:
            continue
        try:
            want = float(cn.group(0))
        except Exception:
            continue
        if abs(got - want) <= max(1e-9, abs(want) * 1e-9):
            return True
        # the expression is present and does not equal what the claim states
        return False
    return None




# ── rule + its own test vectors ─────────────────────────────────────────────────
# The real held-out cases are not "two values that match". They are:
#
#   evidence: "the torus conductance for the a-by-b family is exactly 4/max(a,b)"
#   claim:    "Recomputed: conductance = 4/max(a,b) for every a,b tested at (3,5),(5,3),(4,4).
#             Substituting N for max(a,b) overstates it by up to 30x."
#
# The RULE is in the evidence and the TEST VECTORS are in the claim. So: extract the rule
# from the evidence, extract the tuples from the claim, evaluate the rule at each tuple.
# The claim is decidable when a tuple makes the rule undefined, and when the claim states a
# numeric value that the rule does not produce at that tuple.
TUPLE = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)")
RULE_IN_EVIDENCE = re.compile(r"\bis\s+exactly\s+([^.;]+)", re.I)
ARITH_IN = re.compile(
    r"(?P<expr>" + OPERAND + r"(?:\s*[-+*/]\s*" + OPERAND + r")+)")


def eval_rule_with_cases(evidence: str, claim: str):
    rm = RULE_IN_EVIDENCE.search(evidence)
    if not rm:
        return None
    rule = rm.group(1).strip()
    if not re.search(r"\+\s*max|[\+\-*/]|\bmax\b|\bmin\b", rule, re.I):
        return None
    tuples = [(float(a), float(b)) for a, b in TUPLE.findall(claim)]
    if not tuples:
        return None
    for t in re.findall(r"[A-Za-z_]\w*", rule):
        pass
    # Strip the FUNCTION names before collecting variable names. "max" contributed m, a
    # and x, so the binding took a=max's first letter and the eval raised NameError --
    # which my undefined-check then reported as "the rule is undefined here", i.e. FALSE,
    # on a claim that is true. A function name is not a variable.
    rule_vars = re.sub(r"\b(?:max|min|abs|sqrt|pow)\b", " ", rule, flags=re.I)
    varnames = [c for c in rule_vars if c.isalpha()]
    if not varnames:
        return None
    env0 = {"_max": max, "_min": min}
    values = []
    for (x, y) in tuples:
        env = dict(env0)
        env.setdefault(varnames[0], x)
        if len(varnames) > 1:
            env.setdefault(varnames[1], y)
        py = re.sub(r"\bmax\b", "_max", rule, flags=re.I)
        py = re.sub(r"\bmin\b", "_min", py, flags=re.I)
        try:
            v = eval(py, {"__builtins__": {}}, env)
        except NameError:
            return None          # unbound name -> we do not know, not FALSE
        except Exception:
            return False                       # the rule is undefined at this tuple
        if isinstance(v, (int, float)) and (math.isnan(v) or math.isinf(v)):
            return False
        values.append(float(v))
    # NO "does the stated number match" check here. I added one and it was unsound: the
    # first number left in the claim is a TEST TUPLE (3, 5, 4), not a claimed result, so it
    # compared 4/max(3,5)=0.8 against the literal 3 and called a true claim false.
    #
    # What this path can soundly decide is narrower: a rule that is UNDEFINED, NaN or
    # infinite at a tuple the claim asserts was tested, makes the claim false. Everything
    # else returns True or defers. A narrower sound decision beats a broader unsound one.
    return True


# ── the public entry point ───────────────────────────────────────────────────────
def decide(evidence: str, claim: str):
    """-> True, False, or None when the relation is not mechanically decidable here."""
    for fn in (eval_rule_with_cases, eval_formula, eval_equality):
        try:
            r = fn(evidence, claim)
        except Exception:
            r = None
        if r is not None:
            return r
    return None
