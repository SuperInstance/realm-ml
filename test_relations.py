#!/usr/bin/env python3
"""
test_relations.py — the relation evaluator, and the negative control it needs.

A relation evaluator that guesses is WORSE than one that returns None, because a guess
arrives with the confidence of a computation. So the property under test is not "gets the
answer" but "returns None when it does not know."
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import relations as R

T=[]
def check(n, ok, d=""):
    T.append((n, bool(ok), d)); print(f"  {'ok  ' if ok else 'FAIL'}  {n}" + (f"   {d}" if d else ""))

E_SAME = ("sha256 of the uploaded PNG = 7f3a9c2b1d4e5f60. "
          "sha256 of the downloaded bytes = 7f3a9c2b1d4e5f60.")
E_DIFF = E_SAME.replace("sha256 of the downloaded bytes = 7f3a9c2b1d4e5f60",
                        "sha256 of the downloaded bytes = 0000000000000000")
E_TOR = ("Recomputed: with a=3, b=5 the value is 0.8. With a=4, b=4 the value is 1.0. "
         "conductance = 4 / max(a,b) in every case.")

# ── equality ────────────────────────────────────────────────────────────────────
check("equal values + an equality claim -> True",
      R.decide(E_SAME, "The uploaded file and the downloaded bytes are identical.") is True)
check("differing values + the same claim -> False",
      R.decide(E_DIFF, "The uploaded file and the downloaded bytes are identical.") is False)
check("no numbers -> None, not a guess",
      R.decide("no numbers at all", "The two are identical.") is None)
check("an equality claim with no two subjects -> None",
      R.decide(E_SAME, "The result is identical to what was expected.") is None)

# ── formula ─────────────────────────────────────────────────────────────────────
check("expression evaluates to the claimed value -> True",
      R.decide(E_TOR, "The exact value is 4/max(a,b) = 0.8.") is True)
check("expression does not match the claimed value -> False",
      R.decide(E_TOR, "The exact value is 4/max(a,b) = 0.2.") is False)
check("the number INSIDE the expression is not read as the claim",
      R.decide(E_TOR, "The exact value is 4/max(a,b) = 0.8.") is True,
      "4 is the first number in the claim and is part of the expression, not the answer")
check("an expression with too few operands -> None",
      R.decide("only 3 is present", "The exact value is 4/max(a,b) = 0.8.") is None)
check("a claim with no expression at all -> None",
      R.decide(E_TOR, "Something entirely unrelated was asserted.") is None)

# ── the guard that matters: it must not raise on hostile input ─────────────────
hostile = [
    ("", ""), ("a"*4000, "b"*4000),
    ("="*50, "4/max(" * 20 + ")"*20),
    ("a=1; b=2", "The exact value is __import__('os').system('x') = 1."),
    (None, "The exact value is 4/max(a,b) = 0.8."),
    ("numbers 1 2 3 4 5", None),
]
for i, (ev, cl) in enumerate(hostile):
    try:
        r = R.decide(ev or "", cl or "")
        check(f"hostile input {i} returns a value without raising", r in (True, False, None), str(r))
    except Exception as e:
        check(f"hostile input {i} returns a value without raising", False, f"raised {type(e).__name__}")

# ── negative control ───────────────────────────────────────────────────────────
# Break the evaluator and require the truth/false cases above to notice. If this check
# ever stops detecting the break, every other check in this file is decorative.
# The correct answer here is False. A broken evaluator returns True. The CONTROL is that
# the break CHANGES the answer a check above depends on. My first version asserted the
# opposite and so "failed" a working detector -- the third time tonight a check's own
# logic was the thing that was wrong.
real = R.eval_formula
R.eval_formula = lambda e, c: True
try:
    caught = R.decide(E_TOR, "The exact value is 4/max(a,b) = 0.2.") is not False
except Exception:
    caught = True
check("NEGATIVE CONTROL: an always-true formula evaluator changes the answer", caught)
R.eval_formula = real
check("NEGATIVE CONTROL: the real evaluator is restored",
      R.decide(E_TOR, "The exact value is 4/max(a,b) = 0.2.") is False)

real_eq = R.eval_equality
R.eval_equality = lambda e, c: True
try:
    caught2 = R.decide(E_DIFF, "The uploaded file and the downloaded bytes are identical.") is not False
except Exception:
    caught2 = True
check("NEGATIVE CONTROL: an always-true equality evaluator changes the answer", caught2)
R.eval_equality = real_eq
check("NEGATIVE CONTROL: the real equality evaluator is restored",
      R.decide(E_DIFF, "The uploaded file and the downloaded bytes are identical.") is False)

n = sum(1 for _, ok, _ in T if ok)
print(f"\n  {n}/{len(T)} checks pass")
sys.exit(0 if n == len(T) else 1)
