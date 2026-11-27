# S5 External Primary Results

Run: `s5-station1-reconstruction-20261128-v1`; execution code: `c571d2a58fcc09d7799eb4a8965217e7ab997401`. Classification: `NEW_CONDITIONAL_EXTERNAL_SEMISYNTHETIC_RECONSTRUCTION`.

## Primary estimand

At B=2, gamma=0, `loss(No-repair) − loss(Frozen M4)` was **+0.00685175** (median 0; 45/200 G0 draws favored M4, 0 favored no-repair, 155 tied). The G0-only paired 95% interval was **[0.00486307, 0.00902371]**. This interval conditions on the shared action loss point estimates and does not include action Monte Carlo uncertainty; the action-MC and two-source intervals include zero. Thus this result is not evidence of an unqualified external benefit.

| Policy, B=2 | Mean bias-corrected standardized loss | Mean edge edits | Mean unused budget |
|---|---:|---:|---:|
| No-repair (S0) | 0.875236 | 0.000 | 2.000 |
| Frozen M4 | 0.868384 | 0.295 | 1.705 |
| T5-guided M4 | 0.868384 | 0.295 | 1.705 |
| Full T1–T6 | 0.868384 | 0.295 | 1.705 |
| Full Greedy | 0.868255 | 1.090 | 0.910 |
| M2+M4 | 0.867997 | 0.570 | 1.430 |
| Graph-free association | 0.867868 | 0.000 edge edits | 2.000 |
| Reference-graph learner diagnostic | 0.867868 | 0.000 edge edits | 2.000 |

The graph-free and reference-graph learner share the best displayed mean loss, slightly below M4, at zero **edge-edit** cost. This is not a comparison of total model-development or verification cost. Differences are small relative to action-MC uncertainty. The reference-graph learner is a diagnostic with privileged graph input.

The 200 units are corruption draws conditional on one fitted DRF DGP and fixed training frame, not independent SCMs. Research D used a different run and private raw materials were unavailable; this run is a new reconstruction, not D replication. No physical intervention or manufacturing deployment claim follows.
