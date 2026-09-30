#!/usr/bin/env python3
"""
corpus.py — every claim this session settled by artifact, with its evidence and its truth.

Not invented. Each row's ground truth was fixed earlier tonight by a file listing, a
grep, a test run, or a measurement, and the evidence string is what that inspection
actually returned. This is the labelled set the realm-specific verifier trains on.
"""
CORPUS = [
# ---- FALSE: the thing is absent or the number is wrong ----
("claw",   "The claw repository implements a ternary action routing system.",
 "Repository file listing, complete: README.md, LICENSE, .gitignore, Dockerfile, docker-compose.yml, claw.toml, package.json, .github/workflows/ci.yml, tests/run.sh, docs/*.md. No routing, conservation, or gamma source files exist.", 0),
("claw2",  "claw enforces a gamma plus eta equals C conservation framework.",
 "Exhaustive filename search across 7445 files: gamma returns 0, conservation returns 0, ternary returns 0.", 0),
("forgemaster","Forgemaster's Forge.compile method exists in the source and is documented in the README.",
 "grep -rniw compile over forgemaster/src/ returns zero matches. The README documents Forge.compile; the method does not exist in the source.", 0),
("vectorize","Cloudflare Vectorize silently drops writes: insert returns 200 and the row count stays 0 forever.",
 "POST /insert returned HTTP 200. GET /list showed 0 rows at t+0s and t+5s. At t+15s the row was present. The write was not dropped; the read was too early.", 0),
("tps",     "polln's README documented 273 total tests.",
 "The live suite registers 268 test files in tests/ plus 8 in tools/test-qa.js, total 276. The documented figure was 268, not 273.", 0),
("subagent","A subagent session reporting succeeded produced a written report artifact at the requested path.",
 "Five of five subagent sessions during the token outage reported succeeded. The Claw and ESP32 artifacts did not appear on disk.", 0),
("mothorder","MOTH Qpixl decodes an array exactly, so the same input always returns the same output.",
 "Engine version 1.1.9. Order is preserved in a single draw, but the engine is stochastic at fixed shots; tied inputs can split and nearest-level glyph values cross quantization boundaries.", 0),
("family",  "The family report's exact torus conductance is 4/N.",
 "Recomputed: the exact value is 4/max(a,b). The prior 30x claim was a unit error, substituting N for max(a,b).", 0),
("qthe",    "qthe-codec implements a complete per-cell LITERAL/DELTA/SKIP/COARSE mode menu.",
 "qthe-codec has a partial dead-code 2-bit mode selector. The complete menu is not implemented.", 0),
("zeppos",  "The pincher README documents a landlock fallback under default landlock feature configuration.",
 "The warning fired under default landlock = []. With an empty list no mechanism is active, so the warning falsely claimed a fallback that could not run.", 0),
# ---- TRUE: executed, measured, or enumerated ----
("canary",  "FNV-1a 64 of the UTF-8 bytes of the string cafe Delta shinjitai is 0x024a555471370b18d.",
 "Julia QuiltCanary.canary() returns 0x024a555471370b18d, 13/13 tests pass. Python, TypeScript, Rust and C# all produce the same digest.", 1),
("aperture","A content matcher on a repeating texture reports 33.2 percent of cells unmatched when 100 percent of cells truly moved.",
 "GPU run, 60s. 50% of cells panned. Motion-mask content matcher reports 33.2% unmatched. A true baseline in which NO cell moves reports 0.0%. So 33.2% is 100% of what actually moved.", 1),
("egg",     "In quilt-egg, relationship weight dominates the stimulus in the resonance formula.",
 "Julia port measured it: modulated edges 0.026909 and 0.028727; the heavier edge wins at s = 0.0, 0.1, 0.3, 0.5, 0.9 and 1.0. Exact ties are resolved by iteration order.", 1),
("egg_inverted", "In quilt-egg, the stimulus dominates relationship weight in the resonance formula.",
 "Julia port measured it: modulated edges 0.026909 and 0.028727; the heavier edge wins at s = 0.0, 0.1, 0.3, 0.5, 0.9 and 1.0. Exact ties are resolved by iteration order.", 0),
("egg_tie", "In quilt-egg, the stimulus determines which edge resonates at an exact tie.",
 "Julia port measured it: modulated edges 0.026909 and 0.028727; at an exact tie the winner is decided by iteration order, not by the stimulus.", 0),
("pincher", "pincher-core's CI has been failing continuously since 2026-06-06.",
 "CI run 2026-06-06 onward: job test (ubuntu-latest, default) failing continuously. The test asserts a sandbox mechanism the runner does not provide.", 1),
("pollnci", "polln's CI never ran its 185 test files; the workflow only built, with continue-on-error.",
 "Workflow audit: the test step is present but continue-on-error true and the matrix names only the build job. 185 test files were never executed.", 1),
("wheel",   "The wheel's GAP cells were produced by a stop-word list that filtered the corpus's own vocabulary.",
 "The stop-word list was applied to the corpus and removed terms that belonged to the material itself, creating the gaps. GAP cells are therefore an artefact of the filter, not of the corpus.", 1),
("wraps",   "The relabel attempt's wrapper defeated the capture harness.",
 "Not settled this session; included as an unlabelled control.", None),
("pollln",  "PlinkoLayer's calculateEntropy returns Shannon entropy of the confidence distribution.",
 "polln PR #63: real Shannon entropy computed over normalized confidences, with a zero-total guard and a known-answer control. Before the fix it returned a fixed value.", 1),
("workerskv","polln's Workers KV namespace reads back what it writes.",
 "PUT returned success:true; GET returned 404 on the first read. It was not retested after a delay, so this is unresolved rather than established.", None),
("registrator","A comment containing /register on a commit is the documented trigger for Registrator.jl to open a registration pull request.",
 "Both /register comments were posted and returned HTTP 201 with comment URLs. The General pull requests have not appeared yet, so registration is in progress rather than complete.", None),
("juliacanary","The Julia toolchain is unavailable in the sandbox.",
 "Julia 1.11.3 was downloaded and extracted to /opt/julia/bin/julia and runs. 13/13 QuiltCanary tests and 29/29 QuiltEgg tests execute.", 0),
("readmeclaim","A census that excludes unreadable repositories from its denominator is a valid drift rate.",
 "The verifier now refuses to publish a rate when any repository is unreadable. The 62% figure was instrument false positives: relative links compared against absolute paths, 180 files sampled from 6000-file repos.", 0),
("narrator","The narrator produced a narrated audio file for the two source chunks.",
 "Self-test 4/4 passed but the narration receipt reports PARTIAL: 0 of 2 chunks verified, 0 bytes. ElevenLabs balance is 0, TTS returns HTTP 401 quota_exceeded. No audio exists.", 0),
("signature","chain-lint reported the witness chain as intact.",
 "chain-lint reported DECLARED-NOT-USED. A live sample showed 0 LINKED, 14 ZERO, 0 MISSING; prev_hash exists but is zero or null in every sampled cell.", 0),
]
