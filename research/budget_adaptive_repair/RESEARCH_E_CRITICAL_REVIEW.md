# Research E — Critical review

## What worked

- Reaggregated the original Research C 22,440 policy-budget results from read-only ledgers and verified ledger payload checksums.
- Recovered exact existing C inputs for B>4 only after all 264 truth, observation, task and graph bindings matched, and replayed B0–4 before extension.
- Separated budget permitted from edits actually used, and distinguished structural, policy, feasibility and decision saturation.
- Included graph-free D in the cost frontier, despite its unfavorable comparison for graph-repair policies under edge-edit-only cost.
- Preserved negative marginal benefit, pointwise uncertainty and post-hoc status.

## Limits and potential counter-evidence

- The C cohorts are finite synthetic SCM samples from the frozen design; E results are post-hoc and do not create new confirmatory evidence.
- D is one fitted semisynthetic DGP and a fixed training frame. Only saved aggregate outputs were locally accessible; new D paired uncertainty, extended budgets, Adaptive M4 and target sensitivity are not verified.
- Average regret/loss curves can conceal SCM-specific worsening, action ties and unused budgets. No aggregate monotonicity claim is made.
- The metric subset and fixed opportunity support define what a policy can repair. A policy's plateau can mean candidate exhaustion or graph constraints, not that additional edits have no value in general.
- Edge edit count omits discovery, review, validation, safety and deployment cost. Lambda has no real-world monetary calibration.
- The reference graph and error labels are oracle-assisted. These analyses do not solve unknown-GT error detection.
- Target sensitivity intentionally changes the target-tracking task. It is a robustness description, not a search for a more favorable target.
- Full-reference learner performance is not an optimal decision oracle. Residual regret is not causally decomposed.

## Claims to avoid

Do not claim M4 is best for every budget, that more budget always improves outcomes, that all off-task errors are harmless, that graph accuracy guarantees decision improvement, that Adaptive M4 is generally superior, that Pareto inclusion implies statistical superiority, or that graph-free regression has zero real economic cost. No Research E result establishes manufacturing deployment, physical intervention effects or monetary savings.

## Execution and validation record

The locked analysis source revision was `bb7b275867274113db28cee664267298c0a25bd7`. Commands completed: `python -X utf8 research/budget_adaptive_repair/analyze_e1.py`; `python -X utf8 research/budget_adaptive_repair/run_e2_reconstruction.py` (124.13 s); `python -X utf8 research/budget_adaptive_repair/run_e3_exploratory.py` (48.20 s); and `python -X utf8 research/budget_adaptive_repair/summarize_e2_e3.py` (completed; wall duration not separately captured). Development/Held-out inputs remained the original cohorts; new SCM/G0 and D intervention rows were zero.

Research E focused tests passed 9/9. Root discovery ran 408 tests and ended with 406 passing, one failure and one error. Both failures are existing Windows environment binding mismatches: the frozen dependency guard expected pinned NumPy/Pandas/NetworkX versions but found `2.4.6/3.0.3/3.6.1`; the Step4B4 raw JSONL hash differs in CRLF checkout bytes, while LF normalization reproduces its manifest SHA-256. The frozen asset checker likewise reports seven graph config hash mismatches in Windows CRLF bytes; LF-normalized bytes match all seven recorded SHA-256 values. No frozen file, test or guard was changed. `git diff --name-only` shows no change to Research C protected code, root frozen state, `requirements.txt`, or frozen Research C assets. CI must be checked on the pushed PR; the local Windows failures are not represented as passes.
