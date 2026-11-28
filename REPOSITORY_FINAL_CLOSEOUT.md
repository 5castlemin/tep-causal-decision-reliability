# Repository final closeout — status report

## Current release status (2026-11-28)

The final integration is complete on `main` at `54933cb522bc7ec1e64164e1e17e0926cc396d63`. PRs #51 and #52 are merged; there are 0 open PRs and 3 remote branches (`main`, the retained legacy attic branch, and the separate `repo-step1` worktree branch). Research 0–4 navigation is published. `final-research-v1.0` points to the prior completed integration snapshot. The archive tag `archive/2026-11-28/unique-branch-tips` preserves historical unique branch tips. Research 3.3/S7 remains computationally incomplete, and no off-device backup is claimed. This file’s earlier PR-pending and cleanup-pending sections below are historical snapshots and are not current instructions.

## Historical closeout snapshots

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

## Canonical Research 0–4 taxonomy update (2026-11-28)

The current narrative and navigation now use Research 0–4: Research 0 (problem identification), Research 1 (WHERE), Research 2 (WHAT & WHY), Research 3 (GENERALIZATION), and Research 4 (HOW MUCH). The legacy experiment identifiers remain in frozen contracts, result paths, manifests, and historical records. Numeric entrypoints were added under `research/00_problem_identification/` through `research/04_how_much/`; original evidence directories were not moved or duplicated. `docs/RESEARCH_TAXONOMY.json`, `docs/RESEARCH_NAMING_MAP.md`, and `research/README.md` provide machine-readable, mapping, and navigation views. The initial taxonomy inventory classified 419 working-tree Markdown files (including one ignored pytest cache file). The release-QA inventory now covers 418 tracked Markdown files (20 active/current, 370 historical, 26 frozen, 1 archive, 1 generated); this is a path inventory, not a claim that every historical file was edited.

No experiment was run. Main remains `ad11afceb60a22958175b5a971f869869beac3e3`; PR #51 was still draft at head `df6b9f1e6e8d1c3a489df6537e894eec4fcef293` before these taxonomy edits. User-reported CI runs 46128275976 and 46128272208 succeeded for that prior head. Fresh CI is required after the taxonomy commit. PR #51 currently has no submitted reviews; the classic branch-protection endpoint was not readable, so no assumption about approval requirements is made. No PR closure, archive tag addition, remote branch deletion, or final research snapshot tag has yet been performed in this update.

The full local unittest discovery on Python 3.13 completed 488 tests with 1 skipped, 4 failures and 4 errors. The recorded failures include missing `jsonschema` and a historical Step 4 raw artifact SHA mismatch in the Windows checkout; no frozen file or validator was altered to make these pass. Taxonomy path checks, research-state check, docs-change check, and `git diff --check` passed after correcting the one S2 source path in the taxonomy JSON. See current PR-head CI before any merge decision.

## Final cleanup outcome (2026-11-28)

PR #51 was merged by the normal merge API as `f95ec7e646a11f1dd8ed727b398003911c54947d`; its pull-request and push CI runs on taxonomy head `e11bf25a58550dbfb5dbe24b26f03de257e056a6` both succeeded (46132429041 and 46132424976). Main CI run 46132707728 succeeded. PR #50 was closed as integrated via #51. Historical PRs #26–35 were closed after archival; there are now zero open PRs.

Remote branches fell from 48 to 3. Forty-five branches were deleted only after exact-SHA rechecks: 32 tips were reachable from main, and 13 unique historical tips were preserved as parents of archive commit `df0b58c69abad88d4f96a92ed2f6af9516415d16`, reachable from remote tag `archive/2026-11-28/unique-branch-tips`. The `attic/legacy-research-2026-11-10` branch remains pending a separate recovery-level review; `research/research-d-design-resolution` remains because the separate `repo-step1` worktree is using it. The third branch is main. The branch decision ledger records each exact deleted tip and disposition.

The remaining work is a small, protected follow-up PR to publish this post-merge cleanup record and then verify main. The final snapshot tag will be created only on the resulting main commit. The pre-cleanup bundle remains same-device only; no off-device backup is claimed.


## Final documentation release QA (2026-11-28)

The release-QA pass corrected the Research 3.2 S5 relative paths, connected Research 0.2 to the original diverse-structure pilot evidence, refreshed the tracked Markdown inventory to 418 files, updated current repository/archive status while retaining pre-cleanup narratives as historical snapshots, and aligned the canonical slide/storyboard labels and S6 reported interval with the saved v6 closeout. A relative-link and heading-anchor scan of 19 current representative Markdown documents found no unresolved local links. The official research-state check and `git diff --check` pass. The project CI contract uses Python 3.11; an isolated Python 3.11.15 environment was built from the declared requirements. One full local run discovered 488 tests: 486 passed, 1 skipped, 1 failed and 1 errored. The local frozen-asset manifest check also reports a config hash mismatch in this Windows checkout. No frozen source, expected checksum, or validation rule was altered; the remote main CI remains a separate verification.

The pre-cleanup and final snapshot bundles both pass `git bundle verify` and match their recorded SHA-256 values; they are same-device copies only. No new experiment or result replay was run.
