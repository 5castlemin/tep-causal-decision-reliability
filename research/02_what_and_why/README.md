# Research 2 — WHAT & WHY: Repair Priority and Added Information

**Question:** Within task-relevant errors, what should be repaired first, why, and does finer structural information add dependable value?

| ID | Purpose | Design and evidence status | Original sources |
|---|---|---|---|
| 2.1 | Explore task metrics and within-task repair policies | Exploratory historical analysis; retain historical and corrected result versions separately | `research/within_task_repair_prioritization/` (S3 contracts, correction audit, deep analysis, corrected results) |
| 2.2 | Describe repair value and structural mechanisms | Retrospective single-edit diagnostics; candidate rows are clustered within SCM and are not independent samples | `research/within_task_repair_prioritization/s4_reconstruction/` (direct off-task edit diagnostics and metric reconstruction) |
| 2.3 | Develop and independently evaluate detailed repair policies | Development 80 and replication 160 under Q-common-admitted strict-indirect population; not identical to earlier populations | `research/within_task_repair_prioritization/s4_reconstruction/` (replication lock, primary results, sample-size plan, integrity manifest) |
| 2.4 | Evaluate incremental error-type and metric information | Retrospective B=1 replay of saved candidates; v6 is final, v5 superseded; no policy superiority, equivalence, or noninferiority established | [`research/supplementary_validation/s6/S6_B1_POLICY_MATRIX_CLOSEOUT.md`](../supplementary_validation/s6/S6_B1_POLICY_MATRIX_CLOSEOUT.md), `research/supplementary_validation/s6/outputs/saved_candidates_v6/` |

Replication v6 means: Frozen M4 regret .038817; Type-ranked .036613; T5-guided .030152; Full T .031391; ex-post oracle .012907. T5−M4 was −.008664 (pointwise 95% interval [−.020398, 0], better/worse/tie 4/1/155; Holm-adjusted paired-t p=1.0). High tie mass limits ranking opportunities. The oracle uses outcomes and is a privileged diagnostic.

**Connection:** Research 3 tests stated external semisynthetic settings; Research 4 considers budget and marginal benefit.
