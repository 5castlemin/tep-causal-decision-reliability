# Research 1 — WHERE: Task-Oriented Repair Location

**Question:** Where should limited graph-repair effort be allocated?

| ID | Purpose | Design, result, uncertainty | Original sources |
|---|---|---|---|
| 1.1 | Compare task-relevant and outside-task repair policies | Frozen-contract synthetic Development/Held-out evaluation; conclusions are conditional on the SCM, learner, task and edit rules | [`RESEARCH_C_EXPERIMENT_CONTRACT_V1.md`](../../RESEARCH_C_EXPERIMENT_CONTRACT_V1.md), [`RESEARCH_C_HELDOUT_V1_RESULTS.md`](../../RESEARCH_C_HELDOUT_V1_RESULTS.md), [`research/final_integration/FINAL_RESULTS_TABLES.md`](../../research/final_integration/FINAL_RESULTS_TABLES.md) |
| 1.2 | Test sensitivity to the decision objective | Post-hoc objective sensitivity; policy ranking changes with objective and target conditions | [`research/final_supplementary_validation/S1_DECISION_OBJECTIVE_ROBUSTNESS.md`](../../research/final_supplementary_validation/S1_DECISION_OBJECTIVE_ROBUSTNESS.md), [`research/final_supplementary_validation/SUPPLEMENTARY_FINAL_RESULTS.md`](../../research/final_supplementary_validation/SUPPLEMENTARY_FINAL_RESULTS.md) |
| 1.3 | Assess association between graph metrics and decision outcomes | Post-hoc predictive validation; association is distinct from causal effect or policy efficacy | [`research/final_supplementary_validation/S2_GROUPED_PREDICTIVE_VALIDATION.md`](../../research/final_supplementary_validation/S2_GROUPED_PREDICTIVE_VALIDATION.md), [`research/final_supplementary_validation/SUPPLEMENTARY_FINAL_RESULTS.md`](../../research/final_supplementary_validation/SUPPLEMENTARY_FINAL_RESULTS.md) |

**Core interpretation:** Task-oriented repair can be useful under the tested conditions, but it is reference-assisted, not a method for discovering unknown errors. Atomic edit count is not monetary cost. **Connection:** Research 2 examines prioritization within the task-relevant candidate set.
