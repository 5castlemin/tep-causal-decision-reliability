# Research D Structural Preflight (Outcome Blind)

The preflight ran before learner recommendations and before any evaluator intervention draw. It used the locked Station1 graph, existing Research C corruption/policy code, and a fixed 64-seed Research D structural seed range. It did not generate, inspect, fit, or score action-response outcomes.

## Reference and task

The pinned official Station1 component contains six nodes and seven directed edges. The selected task is `Station1_mp_0 → Station1_mp_1 → Station1_mp_4`; no direct reference edge joins `Station1_mp_0` to `Station1_mp_4`. The task zone uses the existing graph engine's all-directed-path plus open-unconditioned-backdoor rule. Here only the two edges on the directed path are task-zone edges; Rule A assigns a false adjacency among task-zone nodes to M4. This is strict indirect-only relative to the official benchmark reference, not a claim that the graph is complete physical ground truth.

## Prespecified structural run

- G0 seed IDs: `701001..701064` (64, all retained).
- True-adjacency corruption `q=0.15`; reference-absent FP proposal `r=0.05`.
- Conditional FN/REV/UNRES mix equal; FP direction fair.
- DAG-invalid proposals recorded and rejected without redraw.
- Existing Rule A, G0-fixed opportunity normalization, atomic costs, M1–M4, S0, 15 metric subsets, Canonical Oracle, and B=0..4.
- No outcomes or learner were used in this stage.

## Observed structural support

| Check | Result |
|---|---:|
| G0 seeds | 64 |
| Initial no-error G0 | 12 / 64 (18.75%) |
| G0 with at least one task-zone error | 23 / 64 (35.94%) |
| Task-zone error events | 27 |
| Total proposals | 104 |
| DAG-rejected proposals | 12 (no redraw) |
| Seeds with at least one M1 error | 17 / 64 |
| Seeds with at least one M2 error | 20 / 64 |
| Seeds with at least one M3 error | 22 / 64 |
| Seeds with at least one M4 error | 23 / 64 |
| Policy × budget structural rows | 5,440 (=64 × 17 × 5) |
| Excess duplicate final graph rows within seed/budget groups | 4,685 / 5,440 |

M1–M4 all have support somewhere in this fixed pilot. Each metric is absent in many individual G0s and must be allowed to no-op. Nearly all policy/budget outcomes collapse to duplicate final graphs within a G0/budget group; this constrains the amount of distinct policy behavior available in a six-node graph. This was recorded as a structural limitation rather than corrected by selecting seeds or increasing task-zone error frequency.

## Development G0 manifest

The 32 Development seed IDs were generated from the already locked run settings, with no outcome-based selection. Their G0s were regenerated using those exact IDs and checked against the graph hashes in the recommendation lock. All 32 matched. `development_g0_manifest.json` records, per seed, the initial graph hash, proposal order and status, accepted/rejected error types, task/off-task counts, metric opportunity supports, and initial error counts. This regeneration is deterministic, outcome blind, and did not replace any seed.

The detailed 64-seed structural result is in `structural_preflight.json`; the fixed 32-seed record is in `development_g0_manifest.json`. These graph seeds are not independent external SCMs.\n