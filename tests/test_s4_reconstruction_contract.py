import json
import unittest
from pathlib import Path

from research.original_objective import policy_engine as pe
from research.within_task_repair_prioritization.s4_reconstruction import run_s4_reconstruction as runner
from research.within_task_repair_prioritization.s4_completion import run_s4_pilot as pilot
from research.within_task_repair_prioritization.s4_reconstruction.analyze_s4_metric_candidates import choose


HERE = Path(__file__).resolve().parents[1] / "research" / "within_task_repair_prioritization" / "s4_reconstruction"


def test_contract_freezes_independent_development_and_confirmation_design():
    contract = json.loads((HERE / "s4_reconstruction_contract.json").read_text())
    assert contract["development"]["target_scm"] == 80
    assert contract["confirmation"]["target_scm"] == 160
    assert contract["confirmation"]["primary"].startswith("T5_GUIDED_M4 minus FROZEN_M4")
    assert contract["confirmation"]["precision_target"] == 0.01
    assert contract["confirmation"]["sesoi"] is None
    assert contract["development"]["seed_namespace"] != contract["confirmation"]["seed_namespace"]


def test_s4_seed_derivation_is_repeatable_and_phase_separated():
    contract = json.loads((HERE / "s4_reconstruction_contract.json").read_text())
    a = runner.derive(contract["development"]["seed_namespace"], "unit", 4)
    assert a == runner.derive(contract["development"]["seed_namespace"], "unit", 4)
    b = runner.derive(contract["confirmation"]["seed_namespace"], "unit", 4)
    assert a != b


def test_t5_policy_is_explicit_and_includes_all_b1_subsets():
    truth = pe.state([("X", "M"), ("M", "Y")])
    g0 = pe.state([("X", "M")])
    unit = {"scm_id": "fixture", "proposal": {"topology_edges": [["X", "M"], ["M", "Y"]], "action": "X", "target": "Y"},
            "initial_graph": g0, "config": pilot.make_config()}
    states, policies = {}, []
    states, policies = runner.add_t5_state(unit, "general", states, policies)
    keyed = {(row["policy"], row["budget"]) for row in policies}
    assert ("T5_GUIDED_M4", 1) in keyed
    assert ("T_GREEDY_B1:T1+T2+T3+T4+T5+T6", 1) in keyed
    assert len([p for p in policies if p["policy"].startswith("T_GREEDY_B1:")]) == 63
    assert all(pe.dag(row["graph"]) for row in states.values())


def test_private_input_serialization_does_not_publish_live_tuple_key_graph():
    unit = {"scm_id": "fixture", "initial_graph": pe.state([("X", "Y")]), "config": pilot.make_config(),
            "proposal": {"nodes": ["X", "Y"]}}
    serialized = runner.serializable_unit(unit)
    assert serialized["initial_graph"] == {"directed_edges": [["X", "Y"]], "unresolved_pairs": []}
    assert isinstance(serialized["config"], dict)


def test_development_public_outputs_are_aggregate_only_and_complete():
    out = HERE / "outputs" / "development_v1"
    summary = json.loads((out / "analysis_summary.json").read_text())
    manifest = json.loads((out / "integrity_manifest.json").read_text())
    assert summary["n_scm"] == 80
    assert summary["unique_scm_ids"] == 80
    assert summary["t_subset_policy_count_b1"] == 63
    assert summary["t_subset_policy_count_b2"] == 63
    assert summary["initial_m4_candidate_count"]["n_ge_2"] == 23
    assert manifest["raw_unit_records_public"] is False
    assert all("private" not in name for name in manifest["files_sha256"])
class TestRetrospectiveMetricSelector(unittest.TestCase):
    def test_metric_then_m4_then_canonical_order(self):
        rows = [
            {"pair": ["A", "B"], "operation": "delete", "T1_gain": 0.2, "M4_gain": 0.1},
            {"pair": ["C", "D"], "operation": "delete", "T1_gain": 0.1, "M4_gain": 0.9},
        ]
        chosen, fallback, _ = choose(rows, ("T1",))
        self.assertEqual(chosen, 0)
        self.assertFalse(fallback)
        rows[1]["T1_gain"] = 0.2
        chosen, fallback, _ = choose(rows, ("T1",))
        self.assertEqual(chosen, 1)  # M4 secondary tie-break
        self.assertFalse(fallback)
        rows[0]["M4_gain"] = rows[1]["M4_gain"]
        chosen, _, _ = choose(rows, ("T1",))
        self.assertEqual(chosen, 0)  # canonical pair order

    def test_m4_fallback_and_noop(self):
        rows = [
            {"pair": ["A", "B"], "operation": "delete", "T1_gain": 0.0, "M4_gain": 0.3},
            {"pair": ["C", "D"], "operation": "delete", "T1_gain": -0.1, "M4_gain": 0.1},
        ]
        chosen, fallback, _ = choose(rows, ("T1",))
        self.assertEqual(chosen, 0)
        self.assertTrue(fallback)
        rows[0]["M4_gain"] = 0.0
        rows[1]["M4_gain"] = -0.1
        chosen, fallback, _ = choose(rows, ("T1",))
        self.assertIsNone(chosen)
        self.assertTrue(fallback)
