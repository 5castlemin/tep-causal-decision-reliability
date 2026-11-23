# Research C Runner 3B — Technical Safety Gate

**Status: IN_PROGRESS**
Base: `cbb71c700a8d47a37655b62b527f197c34d085f1`
Scope: TEST_ONLY qualification only; no Development or Held-out cohort was generated.

## Implemented

- `execution_limits.py` defines a TEST_ONLY resource envelope: per-worker timeout, per-SCM and cohort active-time caps, sampled RSS cap, individual result and SQLite ledger byte caps, total run-directory cap, minimum free disk, failure reserve, and serialized concurrency (`max_concurrent_scms=1`).
- `cohort_runner.py` binds resource settings and Python/platform/NumPy/pandas/NetworkX runtime fingerprint into the run config hash. It executes an SCM fixture in a spawned worker, samples child working set, terminates and joins a worker on timeout/RSS detection, checks storage before execution and result commit, records per-SCM active seconds/RSS/failure code, and conservatively charges the wall gap of an interrupted running SCM on resume.
- `runner.py` requires explicit runtime, RNG, resource, cohort, and output bindings in any approved config; checks config/manifest hashes, commit/tree, code hashes, dependency/runtime fingerprint and source cleanliness before any research proposal factory. The only permitted untracked source exclusion is `.build_reframed/`, which is not hash input and remains untouched.
- The Research Mode entry point remains fail-closed. Even a matching future approval bundle is currently followed by `NotImplementedError`; it does not start a research cohort.

Resource stops preserve a nonzero failure-record reserve and never mark a partial policy vector complete. Storage checks are pre-write guards, not filesystem quotas. RSS enforcement is sampled and may overshoot between polls. The direct spawned worker is joined after termination; the current worker does not create child processes of its own.

## TEST_ONLY qualification

Command:

```powershell
uv run --python 3.11.15 --with-requirements requirements.txt python scripts/run_research_c_generated_fixture.py --output-root C:\DAT_TEST_ONLY\research-c3b-resource-qualification-v3 --run-id c3b-resource-qualification-v3 --master-seed 970000 --budgets 0 1 2 3 4 --resource-limits-test-only
```

The fixed harness processed two topology proposals (one admitted, one structurally ineligible), completed one TEST_ONLY SCM, and recorded 85 policy evaluations. Measured from the runner entry after argument parsing:

| Measure | Observed | TEST_ONLY cap |
|---|---:|---:|
| Runner wall time | 0.797 s | — |
| SCM active worker time | 0.641 s | 120 s |
| Cohort active worker time | 0.641 s | 240 s |
| Sampled worker working set peak | 69,591,040 bytes (about 66.3 MiB) | 512 MiB |
| Result record | completed | 10,000,000 bytes |
| SQLite ledger | 356,352 bytes | 20,000,000 bytes |
| Whole output directory | 356,353 bytes | 30,000,000 bytes |
| Free disk observed | 30,347,288,576 bytes | minimum configured: 0 |

These timings and caps qualify one fixed TEST_ONLY input. They do not establish a tail bound or a production resource setting. The test profile’s zero minimum-free-disk threshold is deliberate for a harmless fixture; it is not a recommended research setting.

Failure tests exercise unit timeout, SCM and cohort time caps, sampled RSS detection, result-size cap, SQLite cap, directory cap, minimum free disk, configuration conflict, and rejection of concurrency above one. Separate subprocess tests terminate during SCM processing and before result commit, then compare resumed hashes to uninterrupted execution. All 53 related tests pass.

## Remaining gate items

1. **No production cohort executor:** Research Mode still validates then raises `NotImplementedError`. TEST_ONLY ledger semantics are not being presented as research execution.
2. **No sub-stage checkpoints/timeouts:** Isolation currently wraps the whole SCM E2E unit. Topology proposal, SCM generation, G0, model fit, recommendation and GT evaluation do not each have separate checkpoint/time accounting.
3. **Cohort time accounting is incomplete for production:** Persisted active time currently accrues around fixture worker units. Proposal-generation, orchestration and database overhead are not charged as separate active stages. Recovery conservatively counts a running attempt’s wall gap, which can overcount downtime.
4. **No approved production resource profile or manifest exists:** TEST_ONLY thresholds cannot be promoted automatically. A future user-approved config must set limits, runtime fingerprint, exact source revision, code/settings hashes, cohort namespace and output root.
5. **Manifest success path not exercised:** No synthetic `USER_APPROVED` bundle was created. The current no-approval path is tested; actual approval and production-entry validation remains untested until a genuine approved bundle exists.

Consequently the execution remains **IN_PROGRESS**, not `TECHNICALLY_READY_FOR_APPROVAL`. The current code protects TEST_ONLY runs and keeps research execution blocked, but the production safety contract is not yet fully connected to a research cohort executor. No scientific contract choice is approved or frozen here.
