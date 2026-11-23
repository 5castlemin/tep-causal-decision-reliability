"""Run Research C's fixed fixture or check the fail-closed research gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.original_objective.runner import run_fixture_mode, run_research_mode
from research.original_objective.runner import ResearchModeBlocked


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("fixture", "preflight", "research"), required=True)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "research/original_objective/test_outputs/runner_fixture_v1.json")
    parser.add_argument("--approved-config", type=Path)
    parser.add_argument("--execution-manifest", type=Path)
    args = parser.parse_args(argv)
    if args.mode in {"research", "preflight"}:
        try:
            result = run_research_mode(
                approved_config_path=args.approved_config,
                execution_manifest_path=args.execution_manifest,
                validate_only=args.mode == "preflight")
        except ResearchModeBlocked as exc:
            label = "RESEARCH_PREFLIGHT_BLOCKED" if args.mode == "preflight" else "RESEARCH_MODE_BLOCKED"
            parser.exit(2, f"{label}: {exc}\n")
        except NotImplementedError as exc:
            parser.exit(2, f"RESEARCH_MODE_NOT_IMPLEMENTED: {exc}\n")
        if args.mode == "preflight":
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.approved_config is not None or args.execution_manifest is not None:
        parser.error("approval files are only accepted with --mode research")
    result = run_fixture_mode(args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
