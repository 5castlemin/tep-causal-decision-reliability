# Research 4 — HOW MUCH: Repair Budget and Resource Allocation

**Question:** How far should repair proceed when marginal decision benefit and actual edit count are considered together?

| ID | Purpose | Design and limits | Original sources |
|---|---|---|---|
| 4.1 | Compare budgets and adaptive policies (Research E) | Post-hoc reuse of C Development 64 and Held-out 200; budget curves can be nonmonotone and a temporary plateau is not a universal stopping rule | [`research/final_integration/RESEARCH_E_FINAL_AUDIT.md`](../final_integration/RESEARCH_E_FINAL_AUDIT.md), `research/final_integration/research_e_audit/` |
| 4.2 | Marginal benefit and cost-weighted policy analysis (E Extension) | Retrospective aggregation of sealed S4 Development 80, replication 160 and S5 200 G0 records for B=0–4 (16,560 policy-budget rows); no new SCM/G0/observations/responses. S4/S5 B=5–9 not run. | `research/budget_adaptive_repair/RESEARCH_E_EXTENSION_RESULTS.md`, `RESEARCH_E_MARGINAL_BENEFIT_REPORT.md`, `RESEARCH_E_COST_WEIGHTED_POLICY_REPORT.md`, `RESEARCH_E_EXTERNAL_BUDGET_ANALYSIS.md`, `outputs/final_extension_v1/` |

The lambda cost weight is hypothetical per atomic graph edit, not money, labor time, or operating cost. Keep Research C/S4 regret distinct from S5 tracking loss. Graph-free's zero edge-edit count is not zero total modeling cost. **Connection:** Research 4 closes the allocation question without claiming a universal optimal policy or budget.
