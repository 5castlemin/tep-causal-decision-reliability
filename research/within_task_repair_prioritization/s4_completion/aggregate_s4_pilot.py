"""Create public aggregate-only tables from the private, locked S4 pilot outputs."""
from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from research.original_objective import policy_engine as pe
from research.within_task_repair_prioritization import s3_analysis as s3
import run_s4_pilot as pilot

PRIVATE = Path(os.environ.get("S4_PILOT_OUTPUT", r"C:\DAT_RESEARCH\research-s4\pilot-20261127-v1"))
PUBLIC = Path(os.environ.get("S4_PILOT_AGGREGATE_OUTPUT",
                            str(Path(__file__).resolve().parent / "outputs_pilot_v2")))


def load(name):
    return json.loads((PRIVATE / name).read_text(encoding="utf-8"))


def write_csv(name, rows):
    if not rows:
        raise ValueError(f"empty aggregate: {name}")
    fields = list(rows[0])
    with (PUBLIC / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def summarize_values(values):
    x = np.asarray(values, dtype=float)
    return {"n": int(x.size), "mean": float(x.mean()), "median": float(np.median(x)),
            "sd": float(x.std(ddof=1)) if x.size > 1 else None,
            "q10": float(np.quantile(x, .1)), "q90": float(np.quantile(x, .9))}


def main():
    PUBLIC.mkdir(parents=True, exist_ok=False)
    summary = load("pilot_summary_private.json")
    policies = load("policy_results_private.json")
    candidates = load("candidate_values_private.json")
    interactions = load("interaction_values_private.json")
    units = load("unit_results_private.json")
    inputs = load("pilot_inputs_private.json")
    unit_by_key = {(u["cohort"], u["scm_id"]): u for u in inputs}

    # The runner aggregate is authoritative for complete policy/budget estimates.
    write_csv("policy_aggregates.csv", summary["policy_aggregates"])
    cgroups = defaultdict(list)
    for row in candidates:
        unit = unit_by_key[(row["cohort"], row["scm_id"])]
        truth = pe.state([tuple(e) for e in unit["proposal"]["topology_edges"]])
        cfg = pilot.make_config()
        _, zone, path_edges, backdoor_edges = s3.structural_sets(
            truth, unit["proposal"]["action"], unit["proposal"]["target"], cfg)
        pair = tuple(json.loads(row["pair"]))
        norm = pe.pair(*pair)
        path_pairs = {pe.pair(*e) for e in path_edges}
        backdoor_pairs = {pe.pair(*e) for e in backdoor_edges}
        in_path, in_backdoor = norm in path_pairs, norm in backdoor_pairs
        role = ("path_and_backdoor" if in_path and in_backdoor else "causal_path" if in_path
                else "backdoor" if in_backdoor else "other_task_zone")
        row["structural_role"] = role
        cgroups[(row["cohort"], row["kind"], role)].append(row)
    candidate_agg = []
    for (cohort, kind, role), rows in sorted(cgroups.items()):
        row = {"cohort": cohort, "edit_kind": kind, "structural_role": role, "candidate_count": len(rows),
               "scm_count": len({r["scm_id"] for r in rows}),
               "mean_regret_gain": float(np.mean([r["regret_gain"] for r in rows])),
               "median_regret_gain": float(np.median([r["regret_gain"] for r in rows])),
               "positive_regret_gain_count": sum(r["regret_gain"] > 1e-12 for r in rows),
               "negative_regret_gain_count": sum(r["regret_gain"] < -1e-12 for r in rows),
               "zero_regret_gain_count": sum(abs(r["regret_gain"]) <= 1e-12 for r in rows),
               "mean_M4_gain": float(np.mean([r["M4_gain"] for r in rows])),
               "action_change_count": sum(bool(r["action_changed"]) for r in rows)}
        for metric in ("T1", "T2", "T3", "T4", "T5", "T6"):
            row[f"mean_{metric}_gain"] = float(np.mean([r[f"{metric}_gain"] for r in rows]))
        candidate_agg.append(row)
    write_csv("single_edit_aggregates.csv", candidate_agg)

    interaction_agg = []
    for cohort in sorted({r["cohort"] for r in interactions}):
        rows = [r for r in interactions if r["cohort"] == cohort]
        vals = [r["interaction"] for r in rows]
        interaction_agg.append({"cohort": cohort, **summarize_values(vals),
                                "positive_count": sum(x > 1e-12 for x in vals),
                                "negative_count": sum(x < -1e-12 for x in vals),
                                "zero_count": sum(abs(x) <= 1e-12 for x in vals),
                                "unique_scm_count": len({r["scm_id"] for r in rows}),
                                "unit_of_analysis": "ordered feasible edit pair nested within SCM; descriptive"})
    write_csv("two_edit_interaction_aggregates.csv", interaction_agg)

    unit_summary = {}
    for cohort in sorted({r["cohort"] for r in units}):
        rows = [r for r in units if r["cohort"] == cohort]
        unit_summary[cohort] = {
            "n_scm": len(rows),
            "initial_m4_candidates": summarize_values([r["initial_m4_candidates"] for r in rows]),
            "feasible_two_edit_orders": summarize_values([r["n_feasible_two_edit_orders"] for r in rows]),
            "expost_le2_regret": summarize_values([r["expost_le2_regret"] for r in rows]),
            "m4_b2_regret": summarize_values([r["m4_b2_regret"] for r in rows]),
            "m4_b2_minus_expost_le2_mean": float(np.mean([r["m4_b2_regret"] - r["expost_le2_regret"] for r in rows])),
            "m4_b2_exactly_matches_le2_optimum_count": sum(abs(r["m4_b2_regret"] - r["expost_le2_regret"]) <= 1e-12 for r in rows)}

    # Every structural-gain subset is kept; this ranks observed pilot outputs without selection.
    subset_rows = [r for r in summary["policy_aggregates"] if r["policy"].startswith("T_GREEDY:")]
    subset_rows.sort(key=lambda r: (r["cohort"], r["budget"], r["policy"]))
    write_csv("all_63_T_subset_aggregates.csv", subset_rows)

    output = {"status": "PILOT_ANALYTIC_EVALUATION_COMPLETED_WITH_LIMITATIONS",
              "classification": "post-hoc exploratory development pilot",
              "generation_counts": {"new_scm": summary["new_scm"],
                  "new_g0_screening_draws": summary["new_g0_screening_draws"],
                  "new_observation_rows": summary["new_observation_rows"],
                  "new_sampled_intervention_rows": 0,
                  "proposal_attempts": sum(v["screening_attempts"] for v in summary["cohorts"].values())},
              "cohorts": summary["cohorts"], "unit_summaries": unit_summary,
              "paired_bootstrap": summary["paired_bootstrap"],
              "candidate_aggregate_groups": len(candidate_agg), "candidate_rows_private": len(candidates),
              "ordered_interaction_rows_private": len(interactions), "policy_rows_private": len(policies),
              "public_artifacts": ["policy_aggregates.csv", "single_edit_aggregates.csv",
                                   "two_edit_interaction_aggregates.csv", "all_63_T_subset_aggregates.csv"],
              "limitations": ["pilot only, not confirmatory", "opportunity-rich cohort is structurally selected",
                  "single signed-linear Gaussian SCM family", "tasks vary by accepted proposal",
                  "analytic GT means, no intervention response samples", "no matched corruption variants",
                  "candidate rows are nested within SCM and are not independent",
                  "no causal effect of edit type or role identified", "Research D unit artifacts unavailable"]}
    (PUBLIC / "aggregate_summary.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
