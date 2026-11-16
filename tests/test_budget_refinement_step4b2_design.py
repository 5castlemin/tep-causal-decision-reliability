import gzip
import json
import unittest
from collections import Counter
from pathlib import Path

from research.budget_aware_refinement.step4b2_population import (
    classify_error_location, competition_recipes, policy_candidate_orders, select_q_recipe,
)
from research.budget_aware_refinement.step4_topology_generator import directed_paths, is_dag
from research.budget_aware_refinement.step4_rng import (
    RNGKey, RNG_PROTOCOL_VERSION, derive_seed, derive_streams,
)
from research.budget_aware_refinement.policy_engine import refine


ROOT = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement"


class Step4B2DesignTests(unittest.TestCase):
    def test_location_tags_overlap_without_claiming_off_path_is_harmless(self):
        nodes = ("C", "X", "M", "Y", "Z", "W")
        truth = {("C", "X"), ("X", "M"), ("M", "Y"), ("Z", "Y")}
        tagged = classify_error_location(nodes, truth, "X", "Y", (
            ("FN", "C", "X"), ("FP", "Z", "Y"), ("REV", "X", "M"),
        ))
        by_error = {tuple(row["error"]): set(row["tags"]) for row in tagged}
        self.assertIn("upstream_of_action", by_error[("FN", "C", "X")])
        self.assertIn("off_path_peripheral", by_error[("FN", "C", "X")])
        self.assertIn("target_adjacent_off_path", by_error[("FP", "Z", "Y")])
        self.assertIn("off_path_peripheral", by_error[("FP", "Z", "Y")])
        self.assertIn("gt_action_target_path", by_error[("REV", "X", "M")])

    def test_q_recipes_require_two_same_type_dag_valid_corrections(self):
        nodes = ("M", "P", "Q", "R", "X", "Y")
        truth = {("X", "Y"), ("X", "M"), ("M", "Y"), ("P", "Q")}
        initials = {
            "FN": truth - {("X", "Y"), ("P", "Q")},
            "FP": truth | {("X", "P"), ("Q", "R")},
            "REV": (truth - {("X", "M"), ("P", "Q")}) | {("M", "X"), ("Q", "P")},
        }
        for kind, initial in initials.items():
            self.assertTrue(is_dag(nodes, initial), kind)
            self.assertTrue(directed_paths(nodes, initial, "X", "Y"), kind)
            recipes = competition_recipes(nodes, truth, "X", "Y", kind)
            self.assertTrue(recipes, kind)
            recipe = select_q_recipe(recipes, "fixed-q-seed")
            self.assertEqual(recipe, select_q_recipe(recipes, "fixed-q-seed"))
            self.assertTrue(is_dag(nodes, recipe["initial_edges"]))
            self.assertTrue(directed_paths(nodes, recipe["initial_edges"], "X", "Y"))
            self.assertEqual(recipe["candidate_count"], 2)
            self.assertTrue(recipe["budget_limits_repairs"])
            self.assertEqual({e[0] for e in recipe["errors"]}, {kind})
            self.assertTrue(all(is_dag(nodes, _correct(nodes, recipe["initial_edges"], e))
                                for e in recipe["errors"]))

    def test_global_id_order_changes_under_role_blind_relabeling(self):
        from itertools import permutations
        roles = ("M", "P", "Q", "X", "Y")
        truth = {("X", "Y"), ("X", "M"), ("M", "Y"), ("P", "Q")}
        initial = truth - {("X", "M"), ("P", "Q")}
        global_first = set()
        task_first = set()
        for labels in permutations(("V00", "V01", "V02", "V03", "V04")):
            mapping = dict(zip(roles, labels))
            inverse = {v: k for k, v in mapping.items()}
            remap = lambda edges: {(mapping[a], mapping[b]) for a, b in edges}
            order = policy_candidate_orders(tuple(sorted(mapping.values())), remap(truth),
                                            remap(initial), mapping["X"], mapping["Y"], "FN")
            global_first.add(tuple(inverse[x] for x in order["global"][0][1:]))
            task_first.add(tuple(inverse[x] for x in order["task_focused"][0][1:]))
        self.assertEqual(global_first, {("X", "M"), ("P", "Q")})
        self.assertEqual(task_first, {("X", "M")})

    def test_rng_keys_are_stable_contextual_and_execution_order_independent(self):
        base = RNGKey(RNG_PROTOCOL_VERSION, "development", 23, "scm-a",
                      "chain_mediation", 8, 0, "node_relabeling")
        self.assertEqual(derive_seed(base), derive_seed(base))
        variants = (
            RNGKey(RNG_PROTOCOL_VERSION, "confirmation", 23, "scm-a", "chain_mediation", 8, 0, "node_relabeling"),
            RNGKey(RNG_PROTOCOL_VERSION, "development", 23, "scm-b", "chain_mediation", 8, 0, "node_relabeling"),
            RNGKey(RNG_PROTOCOL_VERSION, "development", 23, "scm-a", "fork_branch", 8, 0, "node_relabeling"),
            RNGKey(RNG_PROTOCOL_VERSION, "development", 23, "scm-a", "chain_mediation", 9, 0, "node_relabeling"),
            RNGKey(RNG_PROTOCOL_VERSION, "development", 23, "scm-a", "chain_mediation", 8, 1, "node_relabeling"),
            RNGKey(RNG_PROTOCOL_VERSION, "development", 23, "scm-a", "chain_mediation", 8, 0, "task_selection"),
        )
        seeds = [derive_seed(base), *(derive_seed(key) for key in variants)]
        self.assertEqual(len(set(seeds)), len(seeds))
        fields = {"cohort": "development", "master_seed": 23, "scm_id": "scm-a",
                  "topology_template": "chain_mediation", "node_count": 8,
                  "topology_attempt": 0}
        forward = [derive_streams(**fields)[name] for name in
                   ("topology", "node_relabeling", "task_selection", "error_injection")]
        reverse_names = ("error_injection", "task_selection", "node_relabeling", "topology")
        reverse = {name: derive_streams(**fields)[name] for name in reverse_names}
        self.assertEqual(forward, [reverse[name] for name in
                                   ("topology", "node_relabeling", "task_selection", "error_injection")])

    def test_matched_random_replicates_share_type_schedule_not_random_draw_seed(self):
        nodes = ("a", "b", "c", "d")
        truth = {("a", "b"), ("b", "c"), ("c", "d")}
        initial = {("a", "b"), ("c", "d")}
        common = dict(node_ids=nodes, initial_edges=initial, reference_edges=truth,
                      allowed_types=("FN", "FP"), budget=2, gamma=1,
                      action="a", target="d", schedule_seed=0)
        global_log = refine(**common, policy_id="G-FN-FP", seed=0)
        task_log = refine(**common, policy_id="T-FN-FP", seed=0)
        random_logs = [refine(**common, policy_id="RANDOM", seed=s) for s in (0, 6, 12, 18, 24)]
        self.assertEqual(global_log["type_schedule"], task_log["type_schedule"])
        self.assertTrue(all(log["type_schedule"] == global_log["type_schedule"] for log in random_logs))
        self.assertEqual([log["seed"] for log in random_logs], [0, 6, 12, 18, 24])
        self.assertEqual([log["schedule_seed"] for log in random_logs], [0] * 5)

    def test_b2_raw_json_counts_match_report_and_keep_planned_denominators(self):
        raw = json.loads(gzip.decompress((ROOT / "step4b2_population_diagnostics_v1.json.gz").read_bytes()))
        report = (ROOT / "STEP4B2_HYPOTHESIS_POPULATION_DESIGN.md").read_text(encoding="utf-8")
        summary = raw["summary"]
        p = summary["population_P"]
        q = summary["population_Q"]
        self.assertEqual((raw["planned_P_task_cells"], raw["planned_Q_cells"]), (200, 600))
        self.assertEqual(p["c_path_survival"], {"False": 67, "True": 133})
        self.assertEqual(p["h1_b_type_cells"]["FN"]["eligible_tasks"], 35)
        self.assertEqual(p["h1_b_type_cells"]["FP"]["eligible_tasks"], 200)
        self.assertEqual(p["h1_b_type_cells"]["REV"]["eligible_tasks"], 35)
        self.assertEqual(q["accepted_cells_by_type"], {"FN": 33, "FP": 200, "REV": 55})
        self.assertEqual(sum(q["rank_divergent_selected_cells_by_type"].values()), 113)
        self.assertEqual(q["budget_summary"]["1"]["final_graph_diff"], 113)
        self.assertEqual(q["budget_summary"]["2"]["final_graph_diff"], 0)
        self.assertEqual(p["same_seed_same_nodecount_relabel_mapping_equal_pairs"], 150)
        self.assertEqual(p["same_seed_same_nodecount_relabel_mapping_pair_count"], 150)
        self.assertIn("133/200", report)
        self.assertIn("35 / 200", report)
        self.assertIn("288/600", report)
        self.assertIn("113/288", report)
        self.assertIn("150/150 template-pairs", report)
        self.assertEqual(sum(not r["accepted"] for r in summary["q_rows"]), 312)
        v4 = json.loads(gzip.decompress((ROOT / "step4b_task_budget_feasibility_v4.json.gz").read_bytes()))
        c_rows = [r for r in v4["rows"] if r["condition"] == "C_mixed"]
        self.assertEqual(len(c_rows), 200)
        self.assertTrue(all(r["accepted"] for r in c_rows))


def _correct(nodes, graph, error):
    kind, a, b = error
    result = set(graph)
    if kind == "FN":
        result.add((a, b))
    elif kind == "FP":
        result.remove((a, b))
    else:
        result.remove((a, b))
        result.add((b, a))
    return result


if __name__ == "__main__":
    unittest.main()
