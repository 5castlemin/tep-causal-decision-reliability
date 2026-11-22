# Research C integration candidate

Status: **PROPOSED / NOT APPROVED / NOT PREREGISTERED**. This package currently
contains a structural repair engine, a deterministic G0 design candidate, and
an end-to-end **TEST_ONLY** adapter. It does not expose an enabled research
cohort runner.

## Fixed-fixture check

```powershell
uv run --python <Python-3.11.15-path> --with-requirements requirements.txt python -m unittest tests.test_original_objective_e2e_fixture -v
uv run --python <Python-3.11.15-path> --with-requirements requirements.txt python scripts/run_original_objective_e2e_fixture.py
```

The fixture uses explicit coefficients and a deterministic 512-row exogenous
sequence. Its output is labeled `TEST_ONLY`; it must not be cited as a research
SCM or policy-performance result. The script refuses to overwrite the fixture
output. `run_research_cohort()` fails closed until a separate user-approved,
preregistered runner and frozen execution configuration exist.

## Proposed SCM/task population

Candidate topology source is the existing four-template, 6–10-node topology
generator, with its 0.2–0.4 target density and three-parent limit, under a new
Research C RNG namespace. A task is sampled uniformly from all ordered pairs
that have at least one directed path of length two or more and no direct
`X→Y` edge. This is strict indirect-only eligibility. The observed common-cause
and multiple-path templates can supply open backdoor/multiple-path cases;
augmentation may create colliders and peripheral edges. Motifs are recorded,
not forced into every SCM. A structurally eligible task with no qualifying
pair is a recorded rejection, not a reason to change its seed or task rule.

Candidate SCM family reuses the explicit signed linear acyclic family already
implemented for Step 4 fixtures: edge magnitudes Uniform[0.25, 0.8], independent
fair signs, independent centered Gaussian disturbances with node SD Uniform
[0.8, 1.2], and one common 512-row observational matrix. This reuse is only a
candidate; its synthetic support does not establish DAT process realism. The
existing five-point action grid is expressed in observed action SD units; the
target is observational mean plus `delta × target SD`, and evaluation uses the
analytic SCM rather than a held-out observational outcome. The loss is squared
standardized target-mean error. The absence of a held-out observational split
means this candidate evaluates decisions under the specified model, not
generalization to a new production dataset.

## Proposed G0 corruption candidate

`g0_candidate.corrupt_graph_candidate()` implements a concrete but
unapproved corruption law: independently corrupt each true adjacency with
probability 0.15; conditional on corruption, choose FN/REV/UNRES with equal
probability. Independently attempt an FP on each true nonadjacent unordered
pair with probability 0.05 and choose its direction fairly. One domain-separated
deterministic stream is used for true and false pairs. Each pair is visited at
most once. If a reversal or FP makes the directed graph cyclic, that attempted
event is recorded and rejected without redraw. Consequently the delivered G0
distribution is DAG-conditioned and the realized kind/zone opportunity counts
must be reported; zero support is allowed. No coefficient, observation,
predicted action, GT effect, loss, or regret is used.

The rates are not empirically calibrated and require user approval. With a
fixed true-edge corruption rate, task-zone errors scale with task-zone support;
they are not artificially balanced against off-task errors. Conversely, the
policy engine's fixed-opportunity normalization can give a single event a
larger score when its support is small. The combination can favor a sparse M4
component in the repair score even when G0 generation itself did not force M4
coverage. Report per-metric opportunity counts, event counts, and same-graph
policy collisions. A matched-opportunity diagnostic is needed before claiming
that a difference is due to task relevance alone.

## End-to-end fixture adapter

`e2e_fixture.run_fixed_fixture()` runs S0, all 15 metric subsets, and the
Canonical Oracle comparator for the supplied budgets. It reuses the existing
Step 3 Ridge fitting, prediction, common action grid and analytic hard-do
evaluator. The learner receives observations, task and repaired directed graph
only. It does not receive GT coefficients/effects/losses/regret. GT evaluation
starts after recommendations are frozen. Residual UNRES is currently rejected
as `GRAPH_INPUT_UNSUPPORTED`; the Step 3 learner requires a directed DAG, so
silently treating unresolved adjacency as absent is prohibited. Errors,
no-candidate state, fit/recommendation failure and GT-evaluation failure are
separately represented. Equal selected actions are asserted to have equal
TEST_ONLY regret in the same fixture.

The deterministic fitted-result cache key covers final graph, observation
matrix hash, node order, task, delta, action grid, and Ridge setting. Each
policy record remains present even when the fitted result is shared.

## Gate and remaining execution work

The JSON Schema `research_c_candidate_config.schema.json` records proposed
settings but hard-codes research execution as disabled. No proposal loop,
durable registry, cohort checkpoint/resume, independent evaluation process, or
approved resource caps are implemented for Research C. The fixture script
measures its own wall time, process peak working set on Windows, and serialized
result bytes; these one-fixture measures are not a cohort projection. The
existing Step 4 runner's resume logic is not evidence that this new Research C
path is resumable.

No Step 4 assets, Step 5/6 raw data, or A/B results are modified by this
candidate.
