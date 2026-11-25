# Research D Pipeline Validation

## Gate status

- **G1 Scientific contract: PASS for the bounded Development Pilot.** The exact task, numeric actions, learner-training-only target/scale, q/r corruption, budgets, policy set, estimands, bootstrap, seeds, resource limits and code/source hashes were written to `development_run_lock.json` before any evaluator intervention sample was generated.
- **G2 Technical pipeline: PASS for this bounded pilot.** Fixture, Research C-policy-to-Ridge adapter, lock/tamper rejection, complete evaluator fixture, exact schema/finiteness, actual pinned R/DRF fit, parent-order checks, exact float hard-do, deterministic refit and separate evaluator subprocess all passed.
- **G3 Development Pilot: COMPLETED within bounds.** One DRF fit distribution, one 512-row training sample, 32 G0 seeds, 17 policies, five budgets, five common actions, 256 evaluator rows/action and 1,280 total evaluator rows. No final seed or final evaluation sample was created.

These are technical and development gates, not approval for a final external evaluation or a claim of real manufacturing validity.

## Pinned integration checks

- causalAssembly pinned source commit and the two source-file SHA-256 values matched the prior manifest.
- Runtime used Python `3.11.15`, NumPy `2.2.6`, pandas `2.3.1`, NetworkX `3.4.2`, R `4.5.3`, and R `drf` `1.3.1`; causalAssembly package version `1.2.1`.
- Fitted DRF `X_train.columns` exactly matched `model.parents(of_node=...)` order for every conditional Station1 node. Multiple-parent Station1 nodes included `Station1_mp_2` and `Station1_mp_4`; both orders were retained.
- Two independent same-seed DRF fits each generated a 16-row observational reproducibility check with the same exact SHA-256: `11f3a13511bfcf405c8ab167aced154a01fd068711a1fee06fca89e6362856f1`. The evaluator's own refit reproduced the same check digest. No check response values were recorded.
- A new two-parent deterministic adapter fixture explicitly checks a nontrivial parent order (`Z, X`) and its response. Existing root, nonroot, descendant, non-descendant, repeat-state, seed, invalid-input, and schema fixtures remain active.
- A disposable performance smoke generated 8 finite, schema-valid, exact-action rows at the predeclared grid median; it emitted no response values and its rows were discarded. This run took 49.382 seconds for sampling after a 36.975-second fit. This is separate from the 8 cumulative exploratory rows in the earlier adapter qualification record; there were 16 exploratory physical-data-free smoke rows before the 1,280 Development evaluator rows.

## Information boundary

1. **Generator/train process:** pinned source access, fitted DRF, deterministic fit check and one 512-row observational sample. Training digest: `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39`.
2. **Recommendation stage:** received training frame, reference graph, G0, fixed task/actions, training-only target/scale, and existing Research C repair plus Ridge recommendation code. It did not receive the fitted DRF or an intervention sample.
3. **Recommendation lock:** 2,720 rows (32 × 5 budgets × 17 policies) were written and content-hash verified before the evaluator process started. Recommendation lock SHA-256: `dd0edcef3a060d7f18857fb2a06df5b080231ee28f712100e87f9485b26c7c9b`.
4. **Evaluator process:** a separate Python subprocess reloaded and refit the pinned DRF, verified its deterministic refit sample digest, and loaded no `research.original_objective` policy/recommendation module. It accepted only the locked contract/recommendation files, pinned generator sources and evaluator seed namespace. This process separation is not an OS-level filesystem sandbox; the evaluator script and module-level checks provide the implemented boundary.
5. **Evaluator output:** only action-level count/mean/variance/hash/loss summaries, policy-to-action/loss rows and bootstrap summaries were saved in the ignored local evaluation artifact. Raw response frames were discarded in memory and were not added to Git.

## Fail-closed checks

- Reject missing/unlocked/tampered recommendation manifest, wrong contract hash, duplicate or incomplete G0×budget×policy rows, unsupported action recommendation, nonfinite output, wrong row/column order, duplicate action streams, output artifact overwrite, and sample count above 256/action or 1,280 total.
- The evaluator validates exact schema and finite values before calculating losses. The float adapter confirms the intervention equals the requested numeric value exactly on every generated row and leaves the fitted graph/mechanisms unchanged.
- G0 graph hash regeneration matched all 32 locked seed IDs. There were no seed replacements.
- No code modifies causalAssembly installation files or Research C implementation. The Research C runner's signed-linear population contract was not invoked.

## Tests and runtime evidence

Targeted tests run in the isolated repository CI Python environment:

```text
python -m unittest tests.test_research_d_float_hard_do_adapter tests.test_research_d_semisynthetic_pipeline -v
16 tests passed.
```

The separate integration command used the pinned `causalassembly-preflight-venv` and local ignored source/data directories. Windows R emitted known `sh`, ABI-mode, and locale startup warnings; each successful process exited 0. Full repository test suite and GitHub Actions are recorded in the final execution report after the final commit.

## Hash bindings

- Exact run-lock file SHA-256: `9f3c63c5aa33123a0619511bfc5cc129b887200700227c5fec4d2f4c2b88a404`.
- Recommendation content hash: `dd0edcef3a060d7f18857fb2a06df5b080231ee28f712100e87f9485b26c7c9b`.
- Development G0 manifest content hash: `03a238576ca3e25af47ac30bf818e86dbf06808d1c713924aed8956f59245a91`.
- The full local evaluator artifact is intentionally ignored by Git; its hash is recorded in `development_policy_diagnostics.json` and the execution report.\n