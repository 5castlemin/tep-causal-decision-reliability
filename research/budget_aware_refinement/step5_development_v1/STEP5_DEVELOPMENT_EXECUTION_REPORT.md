# Step 5 Development Cohort Execution

## Outcome

The frozen development cohort completed normally. This is the development study only; no Step 6 confirmation data were generated or read. Step 4's protocol and execution contract remain frozen.

## Frozen preflight

- Approved commit: `06cbd7d4e1efbbff45559eef84b280acc9d081ce`
- Approved tree: `661f50e7cd859f5c32d909730f686cb93251cc59`
- Runtime: Windows 10 build 26200, CPython 3.11.15, NumPy 2.4.3, pandas 3.0.1, NetworkX 3.6.1
- Frozen manifest SHA-256: `d712947eec862e4a286f2c89be15e196b77b2262b643e3464f9e21cd2b52e8a1`
- Operational settings SHA-256: `da97f2a7dbd9717179eb4ccc5e6bffee8923a84bb20ffd348447fd55612143a2`
- GitHub Actions run #252 succeeded for the approved commit.
- `assert_production_ready()` passed with the exact expected commit/tree before generation.
- Output root was absent before launch: `C:\DAT_STEP5_RUNS\step5-development-v1`.

## Execution

Portable equivalent for the pinned Python 3.11.15 environment (the original command's user-specific interpreter path is redacted in this public copy; the recorded runtime fingerprint and execution evidence are unchanged):

```powershell
uv run --python 3.11.15 --with-requirements requirements.txt python -X utf8 -m research.budget_aware_refinement.run_step4c2_research_cohort --cohort development --master-seed 20261116 --output-root C:\DAT_STEP5_RUNS\step5-development-v1 --expected-commit 06cbd7d4e1efbbff45559eef84b280acc9d081ce --expected-tree 661f50e7cd859f5c32d909730f686cb93251cc59
```

| Measure | Result |
|---|---:|
| Topology/task proposals | 211 |
| Strict Q-common structural rejections | 145 |
| Pre-admission topology/task failures | 2 |
| Accepted SCM admissions | 64 |
| SCM parameter generation | 64/64 |
| Shared observation generation | 64/64 |
| FN/FP/REV evaluation complete | 64/64 |
| Composite available | 64/64 |
| Post-admission failures / missing | 0 / 0 |
| Fallback uses | 0 |
| Unexpected generator errors | 0 |
| Delta allocation | +1: 32; -1: 32 |
| Resource cap / proposal cap | not reached / not reached |
| Eligible shortfall | 0 |

The two pre-admission failures were `no_indirect_only_task`; structural rejection reason for the 145 was `missing_same_type_two_candidate_support`. All 64 accepted SCMs completed all three error-type evaluations. An admission failure would not have been replaced.

## Raw integrity

Read-only verification found SQLite `integrity_check=ok`, 64 unique accepted SCM ledgers, and 66 files totaling 7,726,714 bytes in the run root. The analysis verifier checked JSONL newline completion, ordered stage events, event/output hashes and cohort/SCM/RNG/config/input bindings. It recomputed each type difference and SCM composite from the logged regrets. Raw file sizes and SHA-256 hashes are recorded in `STEP5_DEVELOPMENT_RAW_INVENTORY.json`; the verifier confirmed that raw files did not change during analysis.

The SCM-level result is descriptive: 64 complete paired SCMs, mean `D_i=0.0146605`, median 0, sample SD 0.0621579, range [-0.0006981, 0.4195602]. No confirmatory superiority or equivalence inference is made. Details and subgroup limitations are in `STEP5_DEVELOPMENT_REGRET_ANALYSIS.md` and the machine-readable summary.
