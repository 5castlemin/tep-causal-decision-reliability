# Historical research archive index

**As of 2026-11-28.** This index distinguishes material already preserved on `main`, existing attic tags, live remote branches, and the local pre-cleanup bundle. It does not claim that all remote branches have been deleted or that a second-device backup exists.

## Recovery sources

- The existing `attic/2026-11-10/*` tags preserve earlier TEP and legacy research snapshots. They were not modified.
- The remote `attic/legacy-research-2026-11-10` branch remains present at the pre-cleanup inventory revision and is retained because it has a broad historical/recovery diff.
- The verified pre-cleanup Git bundle is at `../pre_cleanup_all_refs.bundle` relative to the repository worktree. It contains 105 refs, passed `git bundle verify`, and has SHA-256 `aedcf74dfb2b914db0ad6546d25aae0b86d31c4e75c3658fd3721cb6fc657894`. This file is on the same device only.
- Branch tips and open PRs are listed in [`REPOSITORY_PRE_CLEANUP_INVENTORY.json`](REPOSITORY_PRE_CLEANUP_INVENTORY.json); proposed classifications and rationales are in [`BRANCH_CLEANUP_DECISIONS.csv`](BRANCH_CLEANUP_DECISIONS.csv).

## Research branches and PR disposition

PR #51 is the final integration PR. Its current source branch must remain until merge and post-merge verification. PR #50's S3 head is an ancestor of the final integration branch and should be treated as integrated by #51 only after #51 actually merges. PR #26 and stacked PRs #27–35 are not part of the final empirical claims. Their unique commits must be given immutable remote archive refs before those PRs or branches are closed/deleted.

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

The final narrative now uses Research 0–4. Start at `research/README.md`; the canonical-to-legacy mapping is in `docs/RESEARCH_NAMING_MAP.md`, machine-readable IDs and evidence paths in `docs/RESEARCH_TAXONOMY.json`, and the 419-file Markdown classification in `docs/MARKDOWN_DOCUMENT_INVENTORY.json`. Existing frozen/history directories remain in place. This update does not mean all historical Markdown was rewritten.

## Final remote archive snapshot

The multi-parent archive tag `archive/2026-11-28/unique-branch-tips` points to archive commit `df0b58c69abad88d4f96a92ed2f6af9516415d16`. Its 14 parent tips preserve the 13 deleted unique historical branch tips plus the retained legacy attic tip. The exact branch-to-tip mapping is recorded in `BRANCH_CLEANUP_DECISIONS.csv`; `git merge-base --is-ancestor <tip-sha> <archive-commit>` verifies reachability. The tag's tree is the finalized main tree at PR #51 merge. No private artifacts were added to the tag.

After the cleanup-record PR is merged and its main CI succeeds, the final submission tag `final-research-v1.0` will identify that final main snapshot. The remaining attic branch and active Research D worktree are intentionally retained.
