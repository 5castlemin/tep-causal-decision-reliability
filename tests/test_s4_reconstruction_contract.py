import json
from pathlib import Path

from research.original_objective import policy_engine as pe
from research.within_task_repair_prioritization.s4_reconstruction import run_s4_reconstruction as runner
from research.within_task_repair_prioritization.s4_completion import run_s4_pilot as pilot


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
