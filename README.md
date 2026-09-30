# realm-ml

Verifying claims the fleet makes about its own code, against the artifacts that settle them.

## The problem this solves

The fleet's canon gate (JEV) was measured on 21 claims with known ground truth and came out
at **AUC 0.510** — a coin flip. On a larger run, 0.454. Feeding it the *evidence* rather
than the claim made it worse (−0.278), and the claims whose evidence contradicted them
scored *highest*.

The diagnosis: JEV is a **relevance detector wearing an oracle's clothes**. It rewards
specificity. It penalises hedges. It does not know what is true.

## What works instead

A 7B model on the cheapest Groq tier, handed the right artifact, judging a claim about code.

| verifier | AUC on the same 21 claims | cost |
|---|---:|---|
| JEV `noul` (Typesafe) | 0.454 | seconds |
| `llama-prompt-guard-2-22m` (22M) | **0.000** — perfectly inverted | 0.3s |
| **`allam-2-7b` + artifact** | **0.893** | 0.4s |

**0.4s per judgment** puts the 3,887-claim fleet census at about a minute at concurrency 30.

## The two domain fixes

Both came from reading the errors, not from tuning a prompt.

**Repair-direction.** Evidence describing a *fix* was read as endorsement of the *defect*.
Topic match, opposite polarity. Detected with a marker plus a polarity probe.

**Computed dominance.** The model can compare statements but cannot evaluate a relation
over values. `map (\j -> dials[adj[i][j]] - dials[i])` in one shape; parse and compute in
another. Needed a direction parser too — and a negative control that caught the first
version silently returning 1 for the *inverted* claim, after a perfect 23/23.

## The honest number

| | n | accuracy | AUC |
|---|---:|---:|---:|
| in-distribution | 23 | 23/23 | 1.000 |
| **held out** | 10 | **8/10** | **0.750** |

The gap is one error class: `sha256(input) == output` and `4/max(a,b)` are the two misses.
Both are "the evidence states a relation, the claim asserts it." Both need the relation
*evaluated*.

The in-distribution 23/23 is not a result. It is a training-set score, and it was wrong in
a way only a negative control could catch.

## Files

| file | what |
|---|---|
| `verifier.py` | v1 — the artifact, JEV, and the claim-side feature extractors |
| `verifier2.py` | v2 — repair-direction and computed-dominance, with routes logged |
| `direction.py` | which quantity the claim asserts dominates |
| `corpus.py` | 26 claims with artifact evidence and ground truth, incl. two permanent controls |
| `run_corpus.py` | v1 evaluation over the corpus |
| `run2.py` | v2 evaluation, reports the route taken per claim |
| `holdout.py` | the fresh held-out set — this is the number that counts |
| `moth.py` | MOTH client (queue-stalled; see below) |
| `groq_labeller.py` | the verifier comparison table |

## MOTH

The engine catalogue includes `qrc-train-v2` / `qrc-gen-v2` — quantum reservoir computing,
train once and generate many. It is the obvious substrate for this problem and it is
unavailable: the account is `platform_role: player` with `features: []`, jobs POST 202 and
sit in `queued` forever, including `coin-toss-v1` with trivial parameters. Not a shape
error, not an identity error — the queue accepts and never runs.

---

## Addendum — `relations.py`, and a narrower honest result

The held-out set was 8/10, and **both misses were the same error class**: the evidence
states a relation over values and the claim asserts it. A 7B model compares statements well
and cannot evaluate them. The fix is not a better prompt — it is to stop asking.

`relations.py` decides mechanically, and returns `None` whenever it does not know, because
**a guess arrives with the confidence of a computation.**

**The real cases were not the shape I expected.** I first built for "two values that match"
and it fired on 1 of 10. The actual shape is:

```
evidence: "the torus conductance for the a-by-b family is exactly 4/max(a,b)"
claim:    "Recomputed: conductance = 4/max(a,b) for every a,b tested at (3,5),(5,3),(4,4).
          Substituting N for max(a,b) overstates it by up to 30x."
```

**The rule is in the evidence and the test vectors are in the claim.** So: extract the rule,
extract the tuples, evaluate the rule at each tuple.

**Result on the held-out set:**

| | accuracy | AUC |
|---|---:|---:|
| model alone | 9/10 | 0.875 |
| compute-then-model | **9/10** | — |

3 of 10 are now decided by computation and **3 of 3 are correct**. One case flipped, and it
flipped to the right answer: `wolff`, which the model called false.

**The honest limit, which is the point.** The remaining miss, `moltresp`, is deferred — and
correctly so:

> evidence: *"test-binary-v1 returns any binary file unprocessed."* — **no numbers at all**

There is nothing to compute with. Returning `None` and asking the model is the right answer.
A relation evaluator that guessed here would have been worse than no evaluator, and would
have done it with the same confidence as the three it got right.

## Three bugs this took, all in the evaluator, all found by re-running the held-out set

1. **A "does the stated number match" check I added was unsound.** The first number left in
   the claim is a *test tuple* (3, 5, 4), not a claimed result, so it compared
   `4/max(3,5) = 0.8` against the literal `3` and called a true claim false. **Deleted.**
   What remains is narrower but sound: a rule that is undefined at a stated tuple makes the
   claim false; everything else defers.
2. **`max` contributed three letters to the variable list.** "max" → m, a, x — so the
   binding took `a` from the function name, `eval` raised `NameError`, and my
   undefined-check reported that as *"the rule is undefined here"*, i.e. FALSE, on a claim
   that is true. **A function name is not a variable.**
3. **Two negative controls were written inverted**, so a working detector read as a
   failure. Breaking the evaluator produces `True` where the correct answer is `False`, and
   *that change* is the detection.

`test_relations.py` is 19 checks, all passing, including hostile-input cases
(`None` inputs, 4 KB strings, unbalanced parens, an attempted `__import__` in a claim) and
two negative controls.

**The through-line is the night's, and it is now eleven instances:** every one of these was
a check that could not distinguish *the system is wrong* from *the check is wrong*. The
evaluator now answers `None` when it does not know, which is the first version of this code
that could be trusted to say so.
