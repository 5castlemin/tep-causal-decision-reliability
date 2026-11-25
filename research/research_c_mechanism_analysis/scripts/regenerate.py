"""Analysis-only regeneration of Research C Dev/Held-out ledgers (NOT an approved research run).
Calls the same pipeline entry point the approved runner calls, with the documented seeds/targets/caps."""
import sys, json, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
from research.original_objective.proposal_pipeline import run_approved_research_proposal_cohort
from research.original_objective.e2e_fixture import _RESEARCH_EXECUTION_CAPABILITY
from research.original_objective.execution_limits import ResourceLimits
def main():
    cohort = sys.argv[2]; out = Path(sys.argv[3])
    spec = {"development": ("development-20261123-seed-2026112301-v1", 2026112301, 64, 386),
            "independent_evaluation": ("independent-evaluation-20261123-seed-2026112303-v1", 2026112303, 200, 1104)}[cohort]
    limits = ResourceLimits(unit_timeout_seconds=600, scm_active_seconds=1200, cohort_active_seconds=36000,
        sampled_rss_bytes=None, max_result_bytes=50_000_000, max_ledger_bytes=2_000_000_000,
        max_cohort_storage_bytes=4_000_000_000, minimum_free_disk_bytes=100_000_000,
        classification="USER_APPROVED_RESEARCH_RESOURCE_PROFILE")
    t=time.time()
    r = run_approved_research_proposal_cohort(out / spec[0], run_id=spec[0], cohort_type=cohort, master_seed=spec[1],
        target_admissions=spec[2], proposal_cap=spec[3], budgets=(0,1,2,3,4), resource_limits=limits,
        _authorization=_RESEARCH_EXECUTION_CAPABILITY)
    r.pop("proposal_outcomes", None)
    print(json.dumps({k: v for k, v in r.items() if k not in ("scms",)}, default=str)[:3000]); print("wall", time.time()-t)
if __name__ == '__main__':
    main()
