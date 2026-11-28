"""Run a small, durable TEST_ONLY fixture cohort; never a research cohort."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.original_objective.cohort_runner import run_test_only_cohort
from research.original_objective.fixed_fixture_data import (
    make_fixed_fixture, make_nondegenerate_fixture,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--master-seed", type=int, required=True)
    parser.add_argument("--budgets", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    args = parser.parse_args(argv)
    result = run_test_only_cohort(
        args.output_root, run_id=args.run_id, master_seed=args.master_seed,
        fixtures={"fixed-scm": make_fixed_fixture,
                  "nondegenerate-scm": {"factory": make_nondegenerate_fixture,
                                        "apply_g0_generator": False}},
        budgets=tuple(args.budgets))
    print(json.dumps({k: result[k] for k in (
        "run_id", "cohort_type", "config_sha256", "counts",
        "completed_scm_count", "complete_policy_evaluations", "all_scm_complete")},
        sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
