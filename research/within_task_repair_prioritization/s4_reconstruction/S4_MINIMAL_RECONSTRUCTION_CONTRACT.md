# S4 minimal reconstruction and T5 replication contract

**Status:** `CONTRACT_LOCKED_BEFORE_GENERATION`; execution locks bind the actual committed runner and source hashes before each phase starts. The historical S4 pilot and unavailable cross-PC runs remain distinct.

## Population and evidence status

Both new phases use the existing outcome-blind proposal builder's accepted strict-indirect proposals, which also enforce its Q-common recipe admission. This is a bounded, explicitly Q-common-admitted population and is not presented as an unconditional Research C population. The historical opportunity-rich pilot is not pooled with the primary cohort. No SCM is selected by regret, action, repair success, or policy result.

The prior other-PC T5 selection report is known but cannot be independently checked. T5 is therefore a reported prior candidate fixed for replication; current development results do not choose the confirmation policy. The development analysis remains exploratory. The confirmation is a new independent replication, not recovery of the lost S4-3 run.

## Locked phases

`s4_reconstruction_contract.json` fixes the namespaces, seed values, screening caps, target sizes, primary policy, budgets, objective, estimator, bootstrap, and resource limits. Development target is 80 SCMs; confirmation target is 160. Both have fixed proposal caps and preserve shortfalls without replacement. Each retained SCM contributes one 512-row training frame and one G0. Evaluation uses the already implemented analytic SCM outcome function; sampled intervention responses are zero.

For all 63 T subsets, the equal-weight mean gain per unit edit cost is primary, M4 gain per cost is the secondary tie-break, then the existing canonical metric/pair/operation ordering applies. T5 keeps the public corrected S3 selector's M4 fallback and no-positive-gain stopping rule. Confirmation primary is paired `Regret(T5_GUIDED_M4) − Regret(FROZEN_M4)` at B=1, gamma=0; negative favors T5. Every generated SCM remains in the denominator, including no-op and zero-opportunity units. A 10,000-replicate SCM paired percentile interval and better/worse/tie counts are descriptive; no SESOI or equivalence margin is asserted.

Primary run-specific locks are created after the runner commit and before the corresponding sample generation. The runner requires clean Git state, the locked source commit/tree and code hashes, a unique empty private and aggregate output path, a sealed recommendation manifest, and the per-phase resource cap. Private artifacts are stored externally under `C:\DAT_RESEARCH\`; no raw unit-level data are published.
