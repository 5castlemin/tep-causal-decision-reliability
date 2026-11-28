"""Build public Research E summary/manifest from verified aggregates."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
CODE = [
    "research/budget_adaptive_repair/analyze_e1.py",
    "research/budget_adaptive_repair/run_e2_reconstruction.py",
    "research/budget_adaptive_repair/run_e3_exploratory.py",
    "research/budget_adaptive_repair/adaptive_m4.py",
    "research/budget_adaptive_repair/summarize_e2_e3.py",
    "research/budget_adaptive_repair/build_public_manifest.py",
    "research/budget_adaptive_repair/research_e_contract.json",
]
PUBLIC_OUTPUTS = [
    "adaptive_m4_aggregate.csv", "budget_policy_summary.csv",
    "c_extended_budget_aggregate.csv", "d_final_aggregate_results.csv",
    "e2_decision_saturation.csv", "e2_extended_budget_aggregate.csv",
    "e2_extended_marginal_benefit.csv", "e2_extended_pareto_frontiers.csv",
    "e2_saturation_diagnostics.csv", "e3_adaptive_paired_comparisons.csv",
    "e3_adaptive_pareto.csv", "fixed_and_cross_budget_frontiers.csv",
    "heldout_b4_leave_one_out.csv", "lambda_exact_intervals.csv",
    "lambda_optima.csv", "marginal_benefit.csv", "pareto_bootstrap_stability.csv",
    "pareto_frontiers.csv", "target_sensitivity_aggregate.csv",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    e1 = json.loads((OUT / "e1_summary.json").read_text(encoding="utf-8"))
    e2 = json.loads((OUT / "e2_reconstruction_summary.json").read_text(encoding="utf-8"))
    e3 = json.loads((OUT / "e3_summary.json").read_text(encoding="utf-8"))
    post = json.loads((OUT / "e2_e3_summary.json").read_text(encoding="utf-8"))
    assert e2["status"] == "PASS_HASH_IDENTICAL_RECONSTRUCTION_AND_B0_B4_REPLAY"
    assert e3["status"] == "C_ONLY_EXPLORATORY_COMPLETE_D_ROW_LEVEL_UNAVAILABLE"
    assert e1["rows"] == {"c_development": 5440, "c_heldout": 17000, "d_aggregate": 85}
    assert len(post["figures"]) == 19

    artifacts = {name: sha(OUT / name) for name in PUBLIC_OUTPUTS}
    figures = {p.name: sha(p) for p in sorted((HERE / "figures").glob("*.svg"))}
    assert len(figures) == 19
    summary = {
        "gate": "RESEARCH_E_CORE_COMPLETED_WITH_LIMITATIONS",
        "classification": "POST_HOC_BUDGET_AND_COST_EFFECTIVENESS_EXTENSION",
        "scope": {
            "e1": "C Development/Held-out unit results plus D saved aggregate-only audit",
            "e2": "C original inputs restored hash-identically; B0-B4 replay then B5-Bmax analytic extension",
            "e3": "C-only exploratory Adaptive M4 and target sensitivity",
            "new_scm_or_g0": 0, "new_drf_fits": 0, "new_d_intervention_rows": 0,
        },
        "cohorts": e2["cohorts"],
        "e1_rows": e1["rows"],
        "bootstrap": {"e1_c": e1["bootstrap"], "pareto_stability": post["bootstrap"]},
        "limitations": [
            "D unit-level reaggregation and D E2/E3 unavailable from accessible saved artifacts.",
            "No Research E result is confirmatory; Research C/D frozen conclusions are unchanged.",
            "Atomic edit count is not monetary, labor, safety or deployment cost.",
            "No physical manufacturing intervention validation.",
        ],
        "public_aggregate_sha256": artifacts,
        "public_figure_sha256": figures,
    }
    (HERE / "research_e_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    source = {p: sha(ROOT / p) for p in CODE}
    manifest = {
        "schema": "research-e-integrity-manifest-v1",
        "execution_commit": git("rev-parse", "HEAD"),
        "execution_tree": git("rev-parse", "HEAD^{tree}"),
        "branch": git("branch", "--show-current"),
        "input_sha256": e1["source_hashes"],
        "source_sha256": source,
        "summary_sha256": sha(HERE / "research_e_summary.json"),
        "public_aggregate_sha256": artifacts,
        "public_figure_sha256": figures,
        "local_only_unit_level_outputs": [
            "c_development_unit_results.csv", "c_heldout_unit_results.csv",
            "c_extended_budget_results.csv", "adaptive_m4_unit_results.csv",
            "target_sensitivity_unit_results.csv", "reference_graph_learner_diagnostic.csv",
        ],
        "source_paths": "logical repository-relative identifiers only; no private absolute paths",
    }
    (HERE / "research_e_integrity_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary["gate"], "execution_commit": manifest["execution_commit"],
                      "aggregate_count": len(artifacts), "figure_count": len(figures)}, indent=2))


if __name__ == "__main__":
    main()
