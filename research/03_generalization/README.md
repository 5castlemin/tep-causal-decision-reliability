# Research 3 — GENERALIZATION

**Question:** Which findings carry over to external causal environments represented by semisynthetic benchmarks?

| ID | Purpose | Evidence and limits | Original sources |
|---|---|---|---|
| 3.1 | Historical semisynthetic validation (Research D) | One conditional DRF-based DGP with 200 G0 draws; primary S0−Full Greedy = +0.03422490, two-source 95% interval [0.00617347, 0.06535080]; preregistered precision targets were unmet. Not a physical manufacturing population. | `research/external_validation/semisynthetic_final/RESEARCH_D_FINAL_RESULTS.md`, `RESEARCH_D_FINAL_UNCERTAINTY_REPORT.md`, `final_public_execution_manifest.json` |
| 3.2 | External re-evaluation and scope (S5) | New conditional semisynthetic reconstruction; one shared DRF DGP, 200 corruption draws, not 200 independent SCMs. Shared graph-free association baseline was competitive. | `research/s4_reconstruction/` (S5 primary, parsimony, structural opportunity, uncertainty and synthesis reports) |
| 3.3 | Large-graph computational feasibility (S7) | Partial feasibility only: 98 nodes/485 directed edges; persisted 0/400 G0 and 0/24,000 recommendations; evaluator not run; no external performance result. Exit/cap telemetry unavailable. Optimization timings .7613s vs 1.474s remain discrepant; runner has a directed-edge input defect requiring repair before any future run. | `research/supplementary_validation/s7/S7_COMPUTATIONAL_CLOSEOUT.md` and related S7 feasibility records |

Do not combine analytic decision regret with standardized tracking loss. Distinguish G0 corruption draws from independent DGPs. **Connection:** Research 4 studies repair quantity and cost trade-offs using its own cohorts and metrics.
