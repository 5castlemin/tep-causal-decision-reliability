"""Run the predeclared topology/G0-only feasibility pilot (no SCM or regret)."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.original_objective.structural_pilot import run_structural_pilot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=Path,
                        default=ROOT / "research/original_objective/structural_pilot_design_v1.json")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "research/original_objective/test_outputs/structural_feasibility_pilot_v1.json")
    args = parser.parse_args()
    design_bytes = args.design.read_bytes()
    design = json.loads(design_bytes)
    if design.get("status") != "STRUCTURE_ONLY_PILOT_DESIGN_NOT_STUDY_CONTRACT":
        raise SystemExit("pilot design must remain explicitly unapproved")
    if design.get("execution_enabled_for_research_cohorts") is not False:
        raise SystemExit("research execution cannot be enabled by pilot design")
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {args.output}")
    result = run_structural_pilot(
        replicates_per_stratum=design["replicates_per_template_node_stratum"],
        topology_master_seed=design["topology_seed"]["master"],
        task_master_seed=design["task_seed"]["master"],
        g0_master_seed=design["g0_seed"]["master"],
        true_corruption_rate=design["g0_rates"]["true_adjacency_corruption"],
        false_adjacency_rate=design["g0_rates"]["false_adjacency"])
    # Keep the reproducible artifact reviewable: retain every topology/G0
    # record and aggregate all policy diagnostics, but omit the 17 x 5
    # per-policy trajectory rows for each case. The exact design and seeds
    # reproduce those rows when needed.
    for case in result["cases"]:
        case.pop("policy_runs", None)
    result["artifact_detail"] = (
        "case-level topology/G0 records plus aggregate policy diagnostics; "
        "per-policy trajectory rows omitted and reproducible from this design")
    result["design_file_sha256"] = sha256(design_bytes).hexdigest()
    result["design_file"] = str(args.design.relative_to(ROOT))
    wrapper = {"payload": result, "payload_sha256": sha256(json.dumps(
        result, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("ascii")).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(wrapper, sort_keys=True, ensure_ascii=True, indent=2,
                         allow_nan=False).encode("ascii") + b"\n"
    with args.output.open("xb") as stream:
        stream.write(encoded); stream.flush()
        import os
        os.fsync(stream.fileno())
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "output_sha256": sha256(encoded).hexdigest(),
                      "design_sha256": result["design_file_sha256"],
                      "summary": result["summary"]}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
