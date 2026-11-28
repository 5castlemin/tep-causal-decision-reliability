# Repository final closeout — status report

**As of:** 2026-11-28 (KST)

**Target:** `feature/final-s6-s7-validation`, PR #51
**Gate:** `PROJECT_FINALIZED_WITH_CLEANUP_LIMITATIONS`

## Research and documentation

No scientific experiment or dataset generation was performed in this closeout. The representative documents now correct Research D's primary contrast attribution to `S0−Full Greedy = +0.03422490` (the two-source 95% interval `[0.00617347,0.06535080]` excludes zero, while the predeclared action-MC and two-source precision targets were still missed); distinguish it from the mean-derived `S0−M4 ≈ +0.032995`; report S6 v6 policy results from saved S4 candidate records; and preserve S7 as incomplete with zero recommendation/evaluator results.

S6 B=1 replication results remain post-hoc: Frozen M4 `.038817`, Type-ranked M4 `.036613`, T5 `.030152`, Full T `.031391`, ex-post oracle `.012907`. Type-ranked−M4 was `−.002204` (95% paired SCM bootstrap `[−.009283,.003545]`, better/worse/tie `2/1/157`, Holm-adjusted paired-t p `1.0`). T5−M4 was `−.008664` (`[−.020398,0]`, `4/1/155`, adjusted p `1.0`). T5's observed mean advantage does not establish superiority, equivalence or noninferiority. No new SCMs/G0/observations were generated.

S7 persisted `0/400` G0 and `0/24,000` recommendations; it has no recommendation seal and no evaluator outcomes. Its attempt-specific final supervisor report is missing, so cap enforcement, final elapsed time, exit reason and peak RSS cannot be verified. The separate task-zone feasibility record reports `.7613 s` in machine JSON and `1.474 s` in prose; the timing discrepancy is unresolved. Static code review confirmed a runner defect: recommendation fitting receives canonical unordered pair keys where `fit_model` expects directed `(source,target)` edges. No recommendation was persisted, so there is no S7 performance result. The frozen runner was not changed.

Updated reference files include `FINAL_RESEARCH_FRAMEWORK.md`, `FINAL_RESEARCH_EVIDENCE_MATRIX.md`, `FINAL_RESEARCH_TEAM_GUIDE.md`, `FINAL_RESEARCH_CLAIMS_AND_LIMITATIONS.md`, `FINAL_SCIENTIFIC_INTEGRITY_REVIEW.md`, `research/final_integration/FINAL_RESEARCH_REPORT.md`, `research/final_integration/FINAL_RESULTS_TABLES.md`, `research/final_integration/FINAL_PRESENTATION_EVIDENCE_GUIDE.md`, `README.md`, and the generated current-state dashboard.

## Repository inventory and preservation

At pre-cleanup inventory time there were **48 remote branches**, **12 open PRs**, default branch `main`, remote main `ad11afceb60a22958175b5a971f869869beac3e3`, and PR #51 at `5eced12d1847868b7b6a9fb9433d92169bf7c5ba`. The other `repo-step1` worktree is on `research/research-d-design-resolution` and remains untouched. Detailed per-branch SHAs, ancestry, ahead/behind counts, open-PR association and proposed decisions are in `archive/REPOSITORY_PRE_CLEANUP_INVENTORY.json` and `archive/BRANCH_CLEANUP_DECISIONS.csv`.

A complete-history Git bundle containing 105 refs was created outside the checkout at `../pre_cleanup_all_refs.bundle`. `git bundle verify` passed; SHA-256 is `aedcf74dfb2b914db0ad6546d25aae0b86d31c4e75c3658fd3721cb6fc657894`. This is a same-device backup only. The existing attic tags and branch refs were not modified. No remote branch was deleted and no PR was closed in this snapshot.

## PR and cleanup gate

PR #51 is still a draft at the inventory snapshot. Its existing two `verify` checks succeeded on `5eced12d1847868b7b6a9fb9433d92169bf7c5ba` (Actions runs `46125787331` and `46125792972`), but they do not validate subsequent documentation edits. The review API returned no review submissions. The connected GitHub integration could not read classic branch protection (403); the rulesets endpoint returned an empty list. Because the new head's CI and required reviewer/protection conditions are not yet known, the PR has not been marked ready or merged. This is a real closeout blocker, not a scientific result.

The pre-cleanup decision ledger classifies branches for later, exact-SHA review. The intended order remains: refresh PR #51 head and CI; obtain any required independent approval; merge using repository policy; verify main CI; then archive exact unique tips, close superseded PRs, recheck remote SHAs, and delete only eligible branches. PR #26 and #27–35 contain historical unique work and must not be deleted before remote archive refs exist. The active `repo-step1` worktree branch is retained.

## Validation and remaining work

The final docs and state dashboard pass the repository's structural research-state check and `git diff --check` at this point. The historical PR #51 local Python 3.14 run reported environment/fixture failures, while the prior remote CI passed on the previous head. Fresh CI on the current documentation commit is still required. No frozen experimental code, result tables, contracts, raw/private data or requirements were changed.

To finish the repository closeout: push this documented change on PR #51, verify new-head Actions, transition the PR to ready only when appropriate, satisfy repository review rules, merge if GitHub accepts under policy, verify main, and then perform the safe archive/PR/branch cleanup described above. If review/protection prevents merge, retain the branches and PRs and report `PROJECT_FINALIZED_WITH_CLEANUP_LIMITATIONS` rather than claiming full main integration.
