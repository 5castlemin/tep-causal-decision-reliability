"""Exercise proposal-to-regret integration with fixed TEST_ONLY proposal specs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.original_objective.proposal_pipeline import run_test_only_proposal_cohort


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--master-seed", type=int, default=970000)
    parser.add_argument("--budgets", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    args = parser.parse_args(argv)
    specs = [
        {"proposal_id": "test-only-accepted-00", "attempt": 0,
         "template": "chain_mediation", "node_count": 8},
        {"proposal_id": "test-only-reject-chain_mediation-6", "attempt": 0,
         "template": "chain_mediation", "node_count": 6},
    ]
    result = run_test_only_proposal_cohort(
        args.output_root, run_id=args.run_id, master_seed=args.master_seed,
        proposal_specs=specs, budgets=tuple(args.budgets))
    print(json.dumps({k: result[k] for k in (
        "run_id", "classification", "config_sha256", "proposal_counts",
        "completed_scm_count", "complete_policy_evaluations", "all_scm_complete")},
        sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
