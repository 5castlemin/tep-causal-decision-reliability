"""Exercise proposal-to-regret integration with fixed TEST_ONLY proposal specs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.original_objective.proposal_pipeline import run_test_only_proposal_cohort
from research.original_objective.execution_limits import ResourceLimits


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--master-seed", type=int, default=970000)
    parser.add_argument("--budgets", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--resource-limits-test-only", action="store_true",
                        help="enable the fixed TEST_ONLY worker/resource qualification profile")
    args = parser.parse_args(argv)
    specs = [
        {"proposal_id": "test-only-accepted-00", "attempt": 0,
         "template": "chain_mediation", "node_count": 8},
        {"proposal_id": "test-only-reject-chain_mediation-6", "attempt": 0,
         "template": "chain_mediation", "node_count": 6},
    ]
    wall_started = time.monotonic()
    result = run_test_only_proposal_cohort(
        args.output_root, run_id=args.run_id, master_seed=args.master_seed,
        proposal_specs=specs, budgets=tuple(args.budgets),
        resource_limits=(ResourceLimits(
            unit_timeout_seconds=60, scm_active_seconds=120,
            cohort_active_seconds=240, sampled_rss_bytes=512 * 1024 * 1024,
            max_result_bytes=10_000_000, max_ledger_bytes=20_000_000,
            max_cohort_storage_bytes=30_000_000, minimum_free_disk_bytes=0)
            if args.resource_limits_test_only else None))
    summary = {k: result[k] for k in (
        "run_id", "classification", "config_sha256", "proposal_counts",
        "completed_scm_count", "complete_policy_evaluations", "all_scm_complete",
        "cohort_stop_reason", "cumulative_active_seconds", "resource_metrics")}
    summary["runner_wall_seconds"] = time.monotonic() - wall_started
    summary["scm_resources"] = [{k: row.get(k) for k in
                                 ("scm_id", "status", "active_seconds",
                                  "sampled_rss_peak_bytes", "failure_code")}
                                for row in result["scms"]]
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
