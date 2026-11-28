# T1–T6 metric definitions

All scores are in [0,1]. The fixed task-zone node set and reference graph define support once per SCM. A zero denominator is mapped to score 0 for ranking; this is a neutral no-credit convention, not evidence of poor calibration. Equal-weight subsets divide by the original subset cardinality even if a metric has zero reference support. UNRES counts as adjacent for skeleton T1 but never as a correct direction in T2–T6.

| Metric | S3 definition | Main limitation |
|---|---|---|
| T1 task skeleton F1 | Adjacency F1 on unordered pairs among fixed task-zone nodes; Rule A task FP included. | Ignores direction. |
| T2 task direction F1 | Directed-edge F1 on the same fixed task-zone pair universe; UNRES is incorrect. | Does not encode path or intervention effect size. |
| T3 causal-path edge recall | Fraction of reference edges lying on any directed X→Y path that are present with correct direction; each edge once. | No false-path precision; may reward partial disconnected path pieces. |
| T4 X→Y reachability | Binary directed reachability in current graph; traversal may use intermediate nodes. | Spurious path can score 1; says nothing about effect sign/magnitude. |
| T5 task-ancestor F1 | Ancestor-pair F1 among fixed task-zone nodes, with paths allowed through any graph nodes. | Broad relation; not specific to the X→Y causal path. |
| T6 backdoor-edge recall | Fraction of edges on open, unconditioned reference backdoor paths present in correct direction; each edge once. | Not an adjustment-set validity or identification metric. |

No process-flow metric or adjustment-set validity metric was used. S2’s graph-score association is distinct from S3’s per-edit score gain versus actual regret gain.