# Research D final evaluation readiness review

**Decision: `READY_FOR_EXTERNAL_FINAL_CONTRACT_REVIEW`. Final evaluation remains unapproved and ungenerated.** The same-condition Development Reproduction completed under its new locked run and matches the retained historical pilot summaries and recommendation rows exactly.

## Gates

| Gate | Decision | Evidence |
|---|---|---|
| Source recovery and original artifact audit | PASS | Historical pipeline expected bytes restored in `116e81d`; historical artifacts audited. The old pilot stays labeled `execution completed / provenance incomplete at original closeout`. |
| Actual-input dry run | PASS | Preflight attempt `rd-development-reproduction-20261125-02-preflight-03`; 0 samples; exact source/data/runtime/history/artifact bindings and recovery inputs. |
| Lock/source and recommendation boundary | PASS for this run | Commit `4f0bda5` clean at run time; code hashes matched after execution; pinned source and data hashes matched; recommendation subprocess emitted 2,720 rows and was hash-locked before evaluator subprocess. No OS sandbox claim. |
| Same-condition reproduction | PASS | Exact DRF 16-row diagnostic hash, training numeric digest, five actions, target/scale, 32 G0 seeds/initial graph hashes, recommendation actions/costs/graph hashes, five response hashes/means/variances, loss table, Primary, Secondary, baseline and intervals. |
| Independent saved-vector analysis | PASS | External 1,280-row float64 response NPZ was raw-hash checked; v2 analysis independently reproduced Primary and all three bootstrap intervals exactly. |
| CI and protected assets | PASS | GitHub Actions run `45573197045`, commit `4f0bda50816b2fa08b8bf8cce31fc3fea44582eb`: 393 tests, 392 passed, 1 skipped; remaining workflow validations succeeded. Research C and frozen files unchanged. |

## Scientific result and limits

The B=2 Primary is `+0.0033381254737865317`; paired two-source 95% interval `[-0.06532199359741737, 0.07546540523357707]` includes zero. The action-MC-only interval is `[-0.05853612495588549, 0.06343823975974354]`; G0-only interval is `[0.0005872563106569806, 0.007371723023403182]`. M4−Full Greedy mean contrast is zero and their recommended actions agree in all 32 G0s; mean edit costs are `0.1875` and `1.15625`, respectively. The graph-free association baseline is retained.

All five action means in the finite evaluator sample are below the training-only target. This is a limitation to disclose, not a reason to change task/action/target and not proof of population-level infeasibility. Results remain conditional on one reference graph, one DRF-based external semisynthetic generator, one training sample and 32 graph-corruption draws; not 32 independent SCMs, not a physical manufacturing validation and not deployment evidence.

Historical raw response vectors were deleted. Historical summary hashes and aggregates match the reproduction; the old bootstrap cannot be independently re-run. The new bootstrap was independently recalculated from the preserved external reproduction vectors. The reproduction analyzer's post-run axis/summary lookup errors were fixed in a separate v2 analysis script; no evaluator samples were regenerated.

## Proposed final design; decisions still open

The current proposal keeps the existing task, five actions, learner, policies, M1–M4, budgets, B=2 Primary and bias-corrected loss. It recommends freezing the reproduced training frame (choice A) to estimate the same training-conditioned contrast with new G0/evaluator streams. Choice B (new training frame) is a different training-conditioned environment and should be reported separately; one new frame still does not quantify training variation.

The initial final-scale candidate is 200 new G0 seeds, 2,500 evaluator rows/action, 10,000 bootstrap replicates, 2-hour wall time and 4-GiB memory. The reproduced delta-method approximation estimates about 2,399 rows/action for a 0.02 action-MC half-width. Both sample size and resource caps remain proposals; a response-blind resource benchmark must validate chunked bootstrap and the user must approve the training choice, precision goal and caps before a final lock is made.

## Required user decisions

1. Select training frame A (recommended) or B.
2. Confirm the candidate 0.02 action-MC reporting tolerance and whether to set a separate total-interval precision goal.
3. Review the proposed 200 G0s, 2,500 rows/action, 10,000 replicates and resource limits after the response-blind benchmark.

Only after those decisions and a separate approval may a final contract and final evaluation be locked. This readiness decision is not permission to generate final data. No final evaluation data, final G0 seeds or final training sample currently exist.
