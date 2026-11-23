# Research C integration candidate

Status: **PROPOSED / NOT APPROVED / NOT PREREGISTERED**. This package currently
contains a structural repair engine, a deterministic G0 design candidate,
an end-to-end **TEST_ONLY** adapter, and an independent single-fixture runner.
Research cohort execution is implemented behind a strict approval gate and
remains disabled until a user-approved contract/configuration and matching
manifest are supplied.

## Fixed-fixture check

```powershell
uv run --python <Python-3.11.15-path> --with-requirements requirements.txt python -m unittest tests.test_original_objective_e2e_fixture -v
uv run --python <Python-3.11.15-path> --with-requirements requirements.txt python scripts/run_original_objective_e2e_fixture.py
```

The fixture uses explicit coefficients and a deterministic 512-row exogenous
sequence. Its output is labeled `TEST_ONLY`; it must not be cited as a research
SCM or policy-performance result. The script refuses to overwrite the fixture
output. Legacy fixture APIs named `run_research_cohort()` remain blocked; the
approved CLI path is implemented separately in `runner.run_research_mode()`.

The independent runner starts from the fixed SCM, produces deterministic G0
with the existing corruption generator, then runs S0, all 15 metric subsets,
and the canonical comparator through the existing repair/fit/recommend/analytic
GT evaluation function. It atomically writes a checksummed result with code,
configuration, and input hashes; existing outputs are never overwritten:

```powershell
uv run --python <Python-3.11.15-path> --with-requirements requirements.txt python scripts/run_research_c_runner.py --mode fixture --output research/original_objective/test_outputs/independent_runner_fixture_v2.json
```

`--mode research` is fail-closed unless an approved config and matching
execution manifest are provided. It requires the cohort/admission target and
proposal cap, budgets, RNG namespace, runtime fingerprint, production resource
profile, output root, config/contract/resource hashes, commit/tree, and all
runner code hashes. Once validated, it calls the same durable SCM runner and
policy/fit/recommend/GT evaluation core. This path has not been exercised with
a real approval bundle, and no such bundle is currently present. Therefore
this implementation does not authorize or imply that a research cohort may
run. TEST_ONLY subprocess runs remain labeled and stored separately.

After an actual user-approved configuration and matching execution manifest
have been prepared, validate them without starting proposal generation:

```powershell
python scripts/run_research_c_runner.py --mode preflight --approved-config <config.json> --execution-manifest <manifest.json>
```

This validates the approved configuration against both repository JSON
Schemas, then checks the contract, manifest hashes, source revision, runtime,
resource profile, and output conflicts. It does not create an output folder,
proposal, SCM, or ledger. The separate `--mode research` command starts
proposal generation immediately after the same checks and must only be used
after approval. Do not use a TEST_ONLY synthetic gate fixture as a research
approval.

For the validated Windows CPython 3.11.15 environment, install the exact
Research C package set with
`python -m pip install -r research/original_objective/research_c_runtime_lock.txt`;
`requirements.txt` declares the direct packages. The runtime fingerprint
records the installed package inventory, including transitive dependencies.

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
starts after recommendations are frozen. The current TEST_ONLY integration
offers `Residual UNRES Abstention Encoding`: residual unresolved pairs remain
in the structural graph and its metric counts, but do not enter the directed
learner DAG. This is an unapproved research-contract candidate, not a paid
repair or resolution, and loses the unresolved edge's directional information.
The prior `GRAPH_INPUT_UNSUPPORTED` behavior remains documented as the earlier
fail-closed state. Errors, no-candidate state, fit/recommendation failure and
GT-evaluation failure are separately represented. Equal selected actions are
asserted to have equal TEST_ONLY regret in the same fixture.

The deterministic fitted-result cache key covers final graph, observation
matrix hash, node order, task, delta, action grid, and Ridge setting. Each
policy record remains present even when the fitted result is shared.

## Gate and remaining execution work

The JSON Schema `research_c_candidate_config.schema.json` records proposed
settings and keeps research execution disabled. The independent multi-fixture
runner uses a SQLite ledger with per-SCM states, domain-separated seed IDs,
atomic result/checksum commits, resume and duplicate/config-conflict checks.
`scripts/run_research_c_fixture_cohort.py` runs the fixed SCM and a separate
hand-specified nondegenerate TEST_ONLY SCM. Use the same output root, run ID,
seed, fixture set and budgets to resume:

```powershell
uv run --python <Python-3.11.15-path> --with-requirements requirements.txt python scripts/run_research_c_fixture_cohort.py --output-root <new-temp-directory> --run-id fixture-cohort-v1 --master-seed 20261124 --budgets 0 1 2 3 4
```

`scripts/run_research_c_generated_fixture.py` also exercises the existing
topology/task proposal → SCM parameters → shared observations → Research C G0
corruption → 17-policy E2E → analytic truth evaluation path on one fixed
eligible proposal plus one fixed structurally rejected proposal. This is
explicitly TEST_ONLY. The legacy proposal/SCM helpers require an internal
`development` RNG namespace; the adapter uses `test-only-` proposal and SCM IDs
in its ledger and outputs, records the generator's internal SCM ID for audit,
and excludes these records from study denominators. The
script does not authorize or start Development or Held-out cohorts.

```powershell
uv run --python <Python-3.11.15-path> --with-requirements requirements.txt python scripts/run_research_c_generated_fixture.py --output-root <new-temp-directory> --run-id generated-fixture-v1 --master-seed 970000 --budgets 0 1 2 3 4
```

Add `--resource-limits-test-only` to run the same fixed proposals in a spawned
SCM worker with a TEST_ONLY timeout, sampled RSS, result/ledger/directory byte
caps, active-time caps and minimum-free-space check. The preset is a harness
for safety testing, not a proposed or approved production resource setting.

The cohort layer and resource-limit profile remain TEST_ONLY. Resource tests
exercise a spawned per-SCM worker, sampled RSS termination, active-time caps,
per-result/SQLite/directory byte caps, minimum free disk, and serialized
single-writer access. These settings are not approved Research C production
limits. The current Research Mode validates the approval/runtime/code binding
and then remains blocked because a production cohort executor and per-stage
checkpoint integration are not complete.

The structural pilot contains topology and G0 corruption only: no SCM
coefficients, observations, interventions, fitted models, actions or regret.
Its measurements are design-feasibility diagnostics, not policy-performance
results.

No Step 4 assets, Step 5/6 raw data, or A/B results are modified by this
candidate.
