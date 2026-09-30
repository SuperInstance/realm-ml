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
