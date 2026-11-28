# Historical research archive index

## Current archive and repository state (2026-11-28)

Final integration is on `main` at `54933cb522bc7ec1e64164e1e17e0926cc396d63`; PRs #51 and #52 are merged and no PRs remain open. Three remote branches remain: `main`, `attic/legacy-research-2026-11-10` (historical recovery source), and `research/research-d-design-resolution` (used by the separate `repo-step1` worktree). Forty-five branches were deleted after their disposition and exact tips were recorded; historical unique tips are reachable from [`archive/2026-11-28/unique-branch-tips`](https://github.com/5castlemin/tep-causal-decision-reliability/tree/archive/2026-11-28/unique-branch-tips), target `df0b58c69abad88d4f96a92ed2f6af9516415d16`. Existing attic tags and the v1.0 submission tag remain unchanged. Private data is not in these public refs. No off-device backup is claimed.

The pre-cleanup status statements below are historical snapshots; use the current state above for present-day disposition.

**As of 2026-11-28.** This index distinguishes material already preserved on `main`, existing attic tags, live remote branches, and the local pre-cleanup bundle. It does not claim that all remote branches have been deleted or that a second-device backup exists.

## Recovery sources

- The existing `attic/2026-11-10/*` tags preserve earlier TEP and legacy research snapshots. They were not modified.
- The remote `attic/legacy-research-2026-11-10` branch remains present at the pre-cleanup inventory revision and is retained because it has a broad historical/recovery diff.
- The verified pre-cleanup Git bundle is at `../pre_cleanup_all_refs.bundle` relative to the repository worktree. It contains 105 refs, passed `git bundle verify`, and has SHA-256 `aedcf74dfb2b914db0ad6546d25aae0b86d31c4e75c3658fd3721cb6fc657894`. This file is on the same device only.
- Branch tips and open PRs are listed in [`REPOSITORY_PRE_CLEANUP_INVENTORY.json`](REPOSITORY_PRE_CLEANUP_INVENTORY.json); proposed classifications and rationales are in [`BRANCH_CLEANUP_DECISIONS.csv`](BRANCH_CLEANUP_DECISIONS.csv).

## Research branches and PR disposition

Historical pre-cleanup guidance: PR #51 was the final integration PR; PR #50 was integrated by it. PRs #26 and #27–35 were closed after their unique commits were archived. These instructions describe the earlier cleanup plan and are no longer pending actions.

The pre-cleanup inventory has 48 remote branches, 12 open PRs, 39 merged/closed PRs, and no GitHub releases. No remote branch or PR was deleted or closed in this closeout snapshot. The PR #51 head at inventory time had no review submissions. The connected GitHub integration returned 403 on the classic branch-protection endpoint, so required-review configuration could not be independently read. Therefore the history-preserving cleanup sequence is pending the final PR gate.

## Restore commands

To inspect the bundle without changing an existing repository:

```powershell
git clone --mirror ..\pre_cleanup_all_refs.bundle restored-repository.git
git -C restored-repository.git show-ref
```

For a future branch deletion, first create and push an `archive/2026-11-28/<branch-path>` tag at the exact inventory SHA, verify the remote tag resolves to that SHA, close or merge the associated PR, then recheck the branch SHA before deletion. Never force-update an archive tag. The separate `research/research-d-design-resolution` worktree is active and is not a deletion candidate.

## Private data

Private raw ledgers, candidate records, training frames, recommendation records, response vectors and fitted objects are not included in GitHub public refs, tags or this bundle unless already part of the public repository. Existing private artifact archives remain subject to their own manifests and access limits. No off-device private-data backup is claimed.

## Canonical taxonomy navigation

The final narrative uses Research 0–4. Start at `research/README.md`; the canonical-to-legacy mapping is in `docs/RESEARCH_NAMING_MAP.md`, machine-readable IDs and evidence paths in `docs/RESEARCH_TAXONOMY.json`, and the tracked Markdown classification in `docs/MARKDOWN_DOCUMENT_INVENTORY.json`. Existing frozen/history directories remain in place. This update does not mean all historical Markdown was rewritten.

## Final remote archive snapshot

The multi-parent archive tag `archive/2026-11-28/unique-branch-tips` points to archive commit `df0b58c69abad88d4f96a92ed2f6af9516415d16`. Its 14 parent tips preserve the 13 deleted unique historical branch tips plus the retained legacy attic tip. The exact branch-to-tip mapping is recorded in `BRANCH_CLEANUP_DECISIONS.csv`; `git merge-base --is-ancestor <tip-sha> <archive-commit>` verifies reachability. The tag's tree is the finalized main tree at PR #51 merge. No private artifacts were added to the tag.

The final submission tag `final-research-v1.0` identifies the completed integration snapshot. The remaining attic branch and separate Research D worktree branch are intentionally retained.
