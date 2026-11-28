# S4 multi-edit interaction framework

**Status: proposed protocol; exploratory S3 interaction aggregates are available.** For edits `i,j`, define `I(i,j)=V(i,j)-V(i)-V(j)` only when each edit is feasible from the same initial graph and the two-edit result is legally reachable. Preserve sequence dependence and re-evaluate candidates after the first edit. If an edit is only enabled by the other, classify it as feasibility interaction rather than forcing the additive contrast.

S3 found sparse, objective-sensitive SCM-level interactions. For gamma 0, mean interaction was -0.02215 on Development and +0.05248 on Held-out; intervals crossed zero. Gamma 0.2 Held-out mean was +0.02293 (interval -0.00108 to 0.05114), and gamma 0.5 was -0.00483 (-0.01833 to 0.00383). These are post-hoc, selected feasible-pair summaries, not population evidence of synergy.

An independent S4 should prespecify matched structural corruption blocks and analyze interaction contrasts at the SCM/block level. Do not treat pairs as independent or use ex-post outcome values to choose the primary interaction family.
