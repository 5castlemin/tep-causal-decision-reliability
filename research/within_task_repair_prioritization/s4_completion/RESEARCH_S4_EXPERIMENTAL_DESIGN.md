# Research S4 experimental design

**Status: `PROPOSED`; no new SCM/G0 or data rows created.** Use two separately reported populations: (A) a general independently generated SCM cohort; (B) an opportunity-rich diagnostic cohort admitted only by structural rules fixed before outcome generation (at least two initially feasible M4 edits). Do not select units by regret or policy performance.

Within each SCM, use matched corruption variants that hold the truth, task, and nuisance settings fixed while varying prespecified error location/type/role. Keep the design focused on a small number of identifiable contrasts: single-path vs alternate-path structure; path-position errors; individual vs paired feasible errors; and sign/magnitude/cancellation strata. Treat nonlinear mechanisms as a separate stratum only if the generator contract and sample resources support it; do not silently factorialize every factor.

Primary comparison: Frozen M4 versus one Development-selected structural prioritization policy at B=2 on SCM-level mean regret. Secondary: regret-greedy and <=2-edit ex-post optimum gaps; edit value and interactions; structural recovery; opportunity-rich conditional results. Use SCM/block-paired resampling and prespecified multiplicity control.

Sample size is not yet estimable responsibly from the repeatedly examined C cohorts. Before confirmatory execution, specify a decision-relevant minimum effect or precision half-width, obtain an independent pilot variance estimate under the finalized design, and calculate N for paired SCM outcomes with allowance for attrition/invalid generation. Report sensitivity over plausible variance and effect values. Do not substitute post-hoc S3 variance as an unbiased independent pilot or select N to reproduce its observed effect.

Feasibility gate before execution: prove structural eligibility yield without observing outcomes, bound exact two-step enumeration cost, validate deterministic policy replay, freeze the generator/code/data seed namespace, and verify storage/resource limits. This design document does not authorize those data-generating steps.
