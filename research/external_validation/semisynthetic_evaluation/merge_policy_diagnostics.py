"""Fill same-action fields in the compact result summary from locked diagnostics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    diagnostics = json.loads(args.diagnostics.read_text(encoding="utf-8"))
    if summary["recommendation_lock_sha256"] != diagnostics["recommendation_lock_sha256"]:
        raise ValueError("summary and diagnostics are bound to different recommendations")
    lookup = {(row["budget"], row["policy_id"]): row["same_action_fraction_vs_S0"]
              for row in diagnostics["policy_budget_summary"]}
    for row in summary["policy_budget_summary"]:
        row["same_action_fraction"] = lookup[(row["budget"], row["policy_id"])]
    args.summary.write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n",
                            encoding="utf-8")
    print(json.dumps({"status": "PASS", "summary_rows_updated": len(summary["policy_budget_summary"])}))


if __name__ == "__main__":
    main()
