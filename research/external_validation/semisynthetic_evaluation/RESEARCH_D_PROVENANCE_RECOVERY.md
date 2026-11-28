# Research D provenance recovery and historical artifact audit

**Status:** Recovery verified; historical pilot remains `execution completed / provenance incomplete at original closeout`. This audit does not retroactively promote it to verified evidence.

## Exact source recovery

The original run lock expected `pipeline.py` SHA-256 `cbb830bc9421bbde851183868037ddc7681dbbac72c1847feb662cf75ae51291`. Recovery commit `116e81d48dbeb4ee86ea164be8f1ffd908c03f62` contains those exact raw bytes, including the terminal LF. The earlier incorrect current file hash was `5a36774cca62dd3b33bb61e2d9aff74e1a90f72a665d66b54edf153902be150f`; appending one LF produced the locked digest exactly. Later evaluator-hardening edits are separate changes and do not alter the recovery commit.

The other nine locked source files were separately checked against the historical commit, the runtime checkout bytes, and the equivalent Windows CRLF representation. Each original expected digest matched one of those byte streams. Git blob identity, the historical commit/tree, and runtime checkout SHA-256 are distinct records; CRLF equivalence was used only to explain the Windows checkout bytes.

## Historical artifacts

`original_pilot_artifact_audit_v2.json` records raw file hashes and the saved-artifact checks. The original lock is SHA-256 `9f3c63c5aa33123a0619511bfc5cc129b887200700227c5fec4d2f4c2b88a404`. The recommendation manifest canonical content hash is `dd0edcef3a060d7f18857fb2a06df5b080231ee28f712100e87f9485b26c7c9b`; the G0 manifest canonical hash is `03a238576ca3e25af47ac30bf818e86dbf06808d1c713924aed8956f59245a91`; the locally retained evaluator artifact raw SHA-256 is `6d92f8dbed13c0b82da012b7366847b5ca5ade7fe8463d48f87a4f4fa3d68eb4`.

The audit verified 2,720 unique recommendation rows (32 G0 × 5 budgets × 17 policies), 2,720 policy evaluation rows, 1,280 response rows, five action summaries, and binding hashes across the stored artifacts. Recomputing the B=2 primary from saved policy rows gives `0.0033381254737865317`, equal to the reported aggregate. The M4–Full Greedy B=2 contrast is zero in saved records, and the actions agree in all 32 G0s. Same-action loss values match the saved action loss table. The historical bootstrap intervals cannot be independently reproduced because raw evaluator response rows were discarded; the audit does not claim otherwise.

## Integrity and limitations

Pinned source-data SHA-256 values remain `afc079bfca962a4746afd316713743d7702ebc7ea00f98255cd8289d72ecef0e` for the 500×98 public sample and `86378888c66089aebb94616dce121b5e8400414112eb221b78dff3a4ca84cab8` for the official reference. These and causalAssembly commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9` were verified locally.

This historical audit establishes byte provenance and internal consistency of retained summaries. It does not reconstruct discarded rows, independently validate the original evaluator's bootstrap, or convert the old closeout status into a verified pilot. The one authorized same-seed reproduction is a separate run and separate evidence record.

## Follow-up same-condition Development Reproduction

The historical pilot status above remains unchanged. A separately authorized run `rd-development-reproduction-20261125-02` completed under immutable commit `4f0bda50816b2fa08b8bf8cce31fc3fea44582eb` (tree `595379c1020649c9bbaec3b9794e0937aa2a2fa1`). The pre-run actual-input dry run `reproduction_preflight_03.json` passed with 0 generated study samples. A prior invocation at `a13e917` stopped after generating and saving the same-seed 512-row learner input and deterministic 32-seed G0 request because NetworkX descendant-set order made `support_checks` metadata differ. The node order is now deterministic by reverse topological order; no action, target, support rule or learner changed.

The failed invocation's 512-row training frame was verified against the historical numeric digest and reused without drawing a replacement. The recovery record binds its raw CSV and numeric hashes, the recommendation-request hash, run ID and failed attempt stage. On continuation, all 32 G0 request records were deterministically reconstructed and compared before recommendations. The scientific lock then passed. The evaluator generated exactly 1,280 rows once and persisted the float64 response vectors only in the ignored external work directory. No final evaluation seeds or samples were created.

The new raw run-lock SHA-256 is `1476308f85c01b0c02941275d6b37d2d8ea973a0487f33efa4cff8a40abad8fa`; execution-manifest SHA-256 is `2c291c1de94feb56c472addf68b59e8a70ffe949411af509e728a70bfee42e75`; response-vector artifact SHA-256 is `251ee7d5fbfb6ec473fa79229ac8741af0ce6d4a325a0377d5f9d3fb388ca803`. The tracked v2 comparison independently verifies the new vector artifact and exact agreement with historical saved hashes, summaries and Primary; historical raw vectors remain unavailable, so their bootstrap is not independently recalculated.

The run reached `READY_FOR_EXTERNAL_FINAL_CONTRACT_REVIEW`. This status does not approve final data generation. User review is still required for fixed versus new training frame, the precision goal and final resource/sample limits. Raw response vectors, training CSV, recommendations and evaluator JSON remain outside Git.
