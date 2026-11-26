# Research E — Final results and closeout

## Gate and scope

**Gate: `RESEARCH_E_CORE_COMPLETED_WITH_LIMITATIONS`.** Locked reruns completed for E1–E3 on Research C inputs. E1 covers original C unit records and D's 85 saved policy-budget aggregates. E2 exactly restored all 264 original C SCM inputs, replayed B0–4, then evaluated B5–7 for Development and B5–9 for Held-out. E3 is limited to C and remains post-hoc exploratory. Research D unit-level extensions were not performed because the designated local D artifact contains no per-G0 recommendations or response vectors. No new SCM/G0, DRF fit or D intervention rows were created.

## E1 — budgets and trade-offs

Research C Held-out M4 mean regret was 0.093439, 0.029327, 0.003988, 0.001435, 0.001435 at B=0–4; mean edits were 0, 0.515, 0.695, 0.760, 0.780. The cohort mean was unchanged at B=3→4, then improved again at B=5 (0.001299 at B=5–9); B=3 is not a general final saturation point. Per-SCM results were not uniformly monotone. At B=4 M2+M4 reached 0.000964 mean regret at 1.440 edits, matching Full Greedy's reported mean regret with 2.005 edits. Research D's reported B2 graph-free association baseline matched Full Greedy's mean loss (0.789362) with zero graph edits; this only uses edit-count cost and does not imply zero modeling or operational cost.

Marginal benefit is previous-budget mean loss/regret minus current-budget mean loss/regret. Negative increments are retained; for example Research C Held-out M2 loses performance from B0 to B1 by 0.004823 regret units. The ratio per added mean edit is a descriptive ratio of cohort means, not a causal effect of an individual edit. C intervals resample paired SCM units jointly across budgets; D new uncertainty was not computed. Pointwise intervals across many policies/budgets are not simultaneous intervals.

The observed C Held-out frontier (B≤4) contains S0/B0, M3/B1, M4/B1–3 and M2+M4/B4, with exact coordinate ties retained. In D, the graph-free baseline's zero edit count and loss equal to Full Greedy make it competitive and dominating/equal under the narrow edge-count-only cost coordinate. Frontier membership is descriptive, not statistical superiority. Bootstrap frontier inclusion and leave-one-out diagnostics are in the output tables. The B4 M4–Full Greedy ordering reaches a tie boundary when the single influential Held-out SCM is omitted; no unit was excluded from the main analysis.

Lambda is a hypothetical standardized-loss penalty per atomic edit. The grid and exact pairwise breakpoints show how observed mean choices change under that constructed preference, not monetary prices. C and D lambda values are not comparable economic preferences.

## E2 — saturation

The pre-fixed cohort cap `max(4,max_i E_i)` is Bmax=7 for C Development and Bmax=9 for C Held-out. All original B0–4 outcomes matched by graph hash, edit sequence, selected action and analytic regret over 22,440 SCM×policy×budget rows before B>4 results were accepted. At Bmax, Canonical Oracle structurally removed all reference discrepancies in 64/64 Development and 200/200 Held-out cases. M4 completely restored the reference graph in 18/64 and 80/200 cases; the other 46/64 and 120/200 retained errors (mean residual counts 1.422 and 1.380). M2+M4 completely restored 27/64 and 109/200; the other 37/64 and 91/200 retained errors (mean residual counts 0.719 and 0.655). Structural restoration, policy candidate exhaustion, DAG-constraint saturation, and decision saturation are separate. DAG constraint saturation was nonzero in the cells listed in `research/final_integration/research_e_audit/corrected_saturation_rates.csv`; the earlier text saying only Held-out M4 was affected was incomplete. Full reference structure is not a decision-optimal oracle; residual decision loss is not uniquely attributed to one cause.

## E3 — bounded exploration

Adaptive M4 made no blocker edits in Development and two total blocker deletions in Held-out. It matched M4 at B2. At Held-out B3, Adaptive−M4 paired mean regret difference was −0.000471 (95% paired SCM bootstrap interval [−0.001414, 0.000000]); Adaptive cost was 0.780 versus M4 0.760, M2+M4 1.350 and Full Greedy 1.790. Only 1/200 SCM improved, 0/200 worsened and 199/200 tied; there were two blocker edits in two SCMs. This is a sparse, post-hoc result, not general superiority. Adaptive M4 is a one-blocker lookahead heuristic and can spend edits without changing actions or can worsen outcomes in individual SCMs.

Target sensitivity changed only `target=mean(Y_train)+delta×SD(Y_train)` for delta −1, −0.5, 0, 0.5, 1, retaining the existing C action grid. At delta 0, the action-grid optimum was interior for 90.6% Development and 92.5% Held-out SCMs under the selected M4/B2 diagnostic; the other tested deltas placed it at an endpoint. This demonstrates dependence on the target definition, not invalidity of the frozen task. No D sensitivity was run.

## Scientific interpretation

Research E is a post-hoc extension of already observed Research C Held-out results, not a new confirmatory study. C still supplies the independent synthetic-SCM evaluation under its frozen contract. D remains a single DRF-based semisynthetic DGP conditional on one fixed training frame and its graph-corruption draws; C and D loss scales and statistical units are not pooled. Edit counts are not labor, money, safety or deployment cost. All graph-repair analyses remain reference/Oracle-assisted. Nothing here validates interventions on a physical manufacturing process.

Detailed aggregate tables and figures are linked from `RESEARCH_E_PRESENTATION_EVIDENCE_GUIDE.md`; private/local unit-level outputs are excluded from Git.


## Final audit additions

The final closeout rechecked all public Research E source, aggregate and figure hashes against the original E manifest and confirmed all four original C SQLite cohort/proposal hashes plus the saved D audit-summary hash. Local-only unit tables had 42,704 extended C rows (8,704 Development; 34,000 Held-out), 2,512 Adaptive rows, 264 Reference learner rows and 19,800 target-sensitivity rows with unique expected keys. Research D raw response vectors/recommendations/training frame were not present in the designated external root during this closeout; its previous 27-check audit is preserved as a stored audit record, not represented as a fresh raw-data reanalysis.

The full-reference learner selected the grid-optimal action in 63/64 Development and 198/200 Held-out units; mean regret was 0.002560 and 0.000828, with 1 and 2 positive-regret cases. At Bmax, Full Greedy and Canonical Oracle matched the Reference learner action in all 264 units; M2+M4 also matched in all units despite residual structural errors, while M4 matched 263/264. Structure restoration and recommendation agreement are related but distinct.

At common target sensitivity delta=0, M4/B2 selected standardized action k=0 for every unit; the action-grid optimum was interior for 58/64 Development and 185/200 Held-out. This is a special mean-tracking target, not evidence across arbitrary targets. The observed C Held-out lower-envelope lambda transitions after including Adaptive M4 were approximately 0.0045445 (Adaptive M4 B5–9), 0.0235724 (Adaptive M4 B3), 0.0392675 (M4 B3), and 0.1287068 (M4 B2); at larger lambda the zero-edit policies tie. These are sample-conditioned hypothetical edit penalties. Expanded Pareto/bootstrap tables are in `research/final_integration/research_e_audit/`.
