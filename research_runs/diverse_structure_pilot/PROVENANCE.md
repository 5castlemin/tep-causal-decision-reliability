# Provenance and scope

- causalAssembly commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`; unmodified `causalAssembly/models_fcm.py` SHA `c1f1b7f6b62c8916ebd23cb0002cdad1e9fcfb995b81cfae9558271987c4290e`. Source header: AGPL-3.0-or-later. It remains an external hash-checked module, not vendored code.
- The eight equation sets, coefficients, task definitions and all seeds are this project's declared synthetic fixtures, not a reconstruction of TEP or a claim about the manufacturing generator. Every direct reference is checked against the actual upstream returned graph.
- The prior isolated Python3.11 environment was reused, without reinstalling packages. Exact versions are in `run_v1/environment.json` and `requirements.lock.txt`. Existing TEP/frozen/Step6/first/repeated inputs were not regenerated.
- `PLAN_v1.json` SHA `0d010bf81b6e6e688130ae499c920502e4571e24f6f4b72e64bd19f403c1fb6b` was saved before source execution. Executed source hashes are captured before the new Git commit; the subsequent commit publishes those exact bytes.
- Native library graph endpoints/weights, confirmed and unresolved representations are retained. The learner worker receives no reference graph/equation/task. Simulated evaluation is generated after all policy SHA freezes.
- Data and noise CSVs are generated synthetic values. Raw original worker console lives in the user-designated archive because it can include local Python paths; Git contains sanitized console and original byte hashes.
- Initial reference diagram and a readable layout revision are both preserved. Layout changes do not change matrix/equation/reference data. Matplotlib SVG metadata may change on a future render; that is not a scientific data replay.
- CI verifies recorded data, equations, policies, statistics, hashes and LOSO separation. It does not reinstall the external simulator or relearn144 models. Full144-learning replay is NOT_RUN; source API same-seed repetitions were actually executed.
- No recovery/safety/physical clock/counterfactual abduction/manufacturing adoption/automatic PR merge. PR12 remains the unmerged parent snapshot at task start.
