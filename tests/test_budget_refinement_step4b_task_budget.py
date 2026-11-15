import unittest
import json
import gzip
from pathlib import Path
from collections import Counter

from research.budget_aware_refinement.step4_topology_generator import (
    TEMPLATES, generate_topology, is_dag,
)
from research.budget_aware_refinement.step4b_task_budget import (
    classify_task_pairs, derive_stream_seeds, operation_opportunities, relabel_roles,
    role_nodes, select_task_pair, graph_hash,
)
from research.budget_aware_refinement.step4b_c_audit import enumerate_mixed_recipes
from research.budget_aware_refinement.step4_error_injection import (
    inject_condition, _has_dag_valid_order, enumerate_c_recipes,
)
from research.budget_aware_refinement.policy_engine import refine


class Step4BTaskBudgetTests(unittest.TestCase):
    def test_feasibility_raw_json_matches_report_and_preserves_denominator(self):
        root = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement"
        data = json.loads(gzip.decompress((root / "step4b_task_budget_feasibility.json.gz").read_bytes()))
        report = (root / "STEP4B_TASK_BUDGET_FEASIBILITY_REPORT.md").read_text(encoding="utf-8")
        self.assertEqual(data["planned_task_condition_attempts"], 600)
        self.assertEqual(len(data["rows"]), 600)
        self.assertEqual(data["accepted_task_conditions"], 569)
        self.assertEqual(data["failed_task_conditions"], 31)
        self.assertEqual(data["policy_execution_count"], 39830)
        self.assertEqual(Counter(r["reason"] for r in data["rows"] if not r["accepted"]),
                         {"no_dag_mixed_related_and_peripheral_recipe": 31})
        self.assertIn("600/600 planned", report)
        self.assertIn("39,830 runs", report)

    def test_critical_audit_report_matches_v3_raw_aggregates(self):
        root = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement"
        data = json.loads(gzip.decompress((root / "step4b_task_budget_feasibility_v3.json.gz").read_bytes()))
        audit = json.loads((root / "step4b1_critical_design_audit_v2.json").read_text(encoding="utf-8"))
        report = (root / "STEP4B1_CRITICAL_DESIGN_AUDIT.md").read_text(encoding="utf-8")
        self.assertEqual(data["planned_task_condition_attempts"], 600)
        self.assertEqual(data["accepted_task_conditions"], 491)
        self.assertEqual(data["failed_task_conditions"], 109)
        self.assertEqual(data["unique_initial_graphs"], 481)
        self.assertEqual(data["policy_execution_count"], 34370)
        self.assertEqual(audit["paired_policy_count"], 17185)
        self.assertEqual(audit["paired_policy_flags"]["same_type_candidate_count_le_1"], 16705)
        self.assertEqual(audit["paired_policy_flags"]["rank_order_diff"], 60)
        self.assertEqual(audit["paired_policy_flags"]["final_graph_diff"], 12)
        self.assertEqual(audit["B_type_strata"]["FN"]["accepted"], 13)
        self.assertEqual(audit["B_type_strata"]["FP"]["accepted"], 67)
        self.assertEqual(audit["B_type_strata"]["REV"]["accepted"], 11)
        self.assertEqual(audit["condition"]["C_mixed"]["accepted"], 200)
        self.assertEqual(len(audit["paired_policy_cross_table"]), 840)
        for fact in ("491 accepted", "109 failed", "16,705", "| 12 | 0.07% |",
                     "| FN | 66 | 13 | 53 |", "| FP | 67 | 67 | 0 |", "| REV | 67 | 11 | 56 |"):
            self.assertIn(fact, report)

    def test_relation_classes_are_disjoint_and_distinguish_overlap(self):
        nodes = ("a", "b", "c", "d")
        edges = {("a", "b"), ("a", "c"), ("c", "b"), ("c", "d")}
        classes = classify_task_pairs(nodes, edges)
        self.assertIn(("a", "b"), classes.direct_and_indirect)
        self.assertIn(("a", "c"), classes.direct_only)
        self.assertIn(("a", "d"), classes.indirect_only)
        all_classes = (classes.direct_only, classes.indirect_only, classes.direct_and_indirect)
        for i, left in enumerate(all_classes):
            for right in all_classes[i + 1:]:
                self.assertFalse(set(left) & set(right))

    def test_common_cause_roles_target_child_not_confounder(self):
        roles = role_nodes("observed_common_cause", tuple(f"V{i:02d}" for i in range(7)))
        self.assertEqual(roles["common_cause"], "V00")
        self.assertEqual(roles["action"], "V01")
        self.assertEqual(roles["target"], "V06")

    def test_relabeling_is_seeded_bijective_and_preserves_dag(self):
        g = generate_topology(8, "observed_common_cause", 12)
        a = relabel_roles(g.template, g.nodes, g.edges, 77)
        b = relabel_roles(g.template, g.nodes, g.edges, 77)
        self.assertEqual(a, b)
        nodes, edges, roles, mapping = a
        self.assertEqual(set(mapping), set(g.nodes))
        self.assertEqual(set(mapping.values()), set(g.nodes))
        self.assertTrue(is_dag(nodes, edges))
        self.assertEqual(roles["action"], mapping["V01"])

    def test_task_selector_reproducible_and_never_double_counts_both(self):
        for template in TEMPLATES:
            g = generate_topology(8, template, 14)
            nodes, edges, _, _ = relabel_roles(template, g.nodes, g.edges, 14)
            first = select_task_pair(nodes, edges, 14)
            second = select_task_pair(nodes, edges, 14)
            self.assertEqual(first, second)
            if first["selected"]:
                self.assertEqual({x[0] for x in first["selected"]}, {"direct", "indirect"})
                self.assertNotEqual(first["selected"][0][1], first["selected"][1][1])
                classes = classify_task_pairs(nodes, edges)
                self.assertIn(first["selected"][0][1], classes.direct_only)
                self.assertIn(first["selected"][1][1], classes.indirect_only)

    def test_common_cause_prefers_scaffold_action_to_target_even_if_overlap(self):
        for n in range(6, 11):
            for seed in range(11, 21):
                g = generate_topology(n, "observed_common_cause", seed)
                nodes, edges, roles, _ = relabel_roles(g.template, g.nodes, g.edges, seed)
                preferred = (roles["action"], roles["target"])
                selected = select_task_pair(nodes, edges, seed, preferred)
                classes = classify_task_pairs(nodes, edges)
                if preferred in classes.indirect_only + classes.direct_and_indirect:
                    self.assertEqual(dict(selected["selected"])["indirect"], preferred)
                    self.assertNotEqual(dict(selected["selected"])["direct"], preferred)

    def test_common_cause_preference_holds_across_seed_and_node_grid(self):
        for n in range(6, 11):
            for seed in range(11, 21):
                g = generate_topology(n, "observed_common_cause", seed)
                nodes, edges, roles, _ = relabel_roles(g.template, g.nodes, g.edges, seed)
                preferred = (roles["action"], roles["target"])
                classes = classify_task_pairs(nodes, edges)
                selected = dict(select_task_pair(nodes, edges, seed, preferred)["selected"])
                self.assertIn(preferred, classes.indirect_only + classes.direct_and_indirect)
                self.assertEqual(selected["indirect"], preferred)
                self.assertNotEqual(selected["direct"], preferred)

    def test_domain_separated_streams_are_reproducible_and_distinct(self):
        a = derive_stream_seeds(14)
        b = derive_stream_seeds(14)
        self.assertEqual(a, b)
        self.assertEqual(set(a), {"topology", "relabel", "task", "error_injection", "policy_schedule"})
        self.assertEqual(len(set(a.values())), len(a))
        self.assertNotEqual(a, derive_stream_seeds(15))

    def test_exhaustive_c_accepts_peripheral_fn_with_related_fp_rev(self):
        nodes = ("V00", "V01", "V02", "V03", "V04", "V05")
        truth = {("V02", "V05"), ("V02", "V04"), ("V00", "V01"), ("V03", "V04")}
        audit = enumerate_mixed_recipes(nodes, truth, "V02", "V05",
                                        require_path_survival=True, require_fn_related=False)
        self.assertTrue(audit["recipes"])
        self.assertTrue(all(x["paths_survive"] for x in audit["recipes"]))
        self.assertTrue(any(any(e[0] == "FN" and e[1:] == ("V00", "V01")
                                for e in row["peripheral_errors"])
                            and any(e[0] in ("FP", "REV") for e in row["related_errors"])
                            for row in audit["recipes"]))

    def test_c_recipe_can_require_nonfixed_atomic_operation_order(self):
        nodes = ("V00", "V01", "V02", "V03", "V04", "V05")
        truth = {("V00", "V01"), ("V01", "V05"), ("V02", "V00"),
                 ("V04", "V03"), ("V05", "V04")}
        operations = (("FN", "V00", "V01"), ("FP", "V03", "V01"),
                      ("REV", "V05", "V01"))
        self.assertTrue(_has_dag_valid_order(nodes, truth, operations))
        current = set(truth)
        for kind, a, b in operations:
            if kind == "FN": current.remove((a, b))
            elif kind == "FP": current.add((a, b))
            else: current.remove((b, a)); current.add((a, b))
            if not is_dag(nodes, current):
                break
        else:
            self.fail("fixture must reject the fixed FN→FP→REV order")

    def test_c_recipe_skips_no_valid_recipe_due_to_fixed_fn_fp_rev_prefix(self):
        nodes = ("A", "B", "C", "D", "E")
        truth = {("A", "B"), ("B", "C"), ("D", "E")}
        operations = (("FN", "D", "E"), ("FP", "C", "A"), ("REV", "B", "A"))
        fixed_prefix = (truth - {("D", "E")}) | {("C", "A")}
        final_graph = (truth - {("D", "E"), ("A", "B")}) | {("B", "A"), ("C", "A")}
        self.assertFalse(is_dag(nodes, fixed_prefix))
        self.assertTrue(is_dag(nodes, final_graph))
        self.assertTrue(_has_dag_valid_order(nodes, truth, operations))

        independent = enumerate_mixed_recipes(nodes, truth, "A", "C")
        self.assertTrue(any(tuple(tuple(op) for op in (item["fn"], item["fp"], item["rev"])) == operations
                            and item["fixed_order_valid"] is False
                            and any(tuple(tuple(op) for op in order) ==
                                    (operations[0], operations[2], operations[1])
                                    for order in item["valid_orders"])
                            for item in independent["recipes"]))
        production, _ = enumerate_c_recipes(nodes, truth, "A", "C")
        self.assertTrue(any(tuple(item["operations"]) == operations for item in production))

    def test_legacy_failed_direct_c_case_becomes_feasible_when_fn_may_be_peripheral(self):
        g = generate_topology(6, "chain_mediation", 11)
        nodes, truth, roles, _ = relabel_roles(g.template, g.nodes, g.edges, 11)
        # This reproduces one legacy direct-task C failure (a unique direct path).
        action, target = "V02", "V00"
        r = inject_condition(nodes, truth, action, target, "C_mixed", seed=11)
        self.assertTrue(r.accepted, r.reason)
        self.assertEqual({x[0] for x in r.errors}, {"FN", "FP", "REV"})
        self.assertTrue(r.relevant_errors)
        self.assertTrue(r.peripheral_errors)

    def test_exhaustive_c_audit_reclassifies_all_31_legacy_failures(self):
        root = Path(__file__).resolve().parents[1] / "research" / "budget_aware_refinement"
        raw = json.loads(gzip.decompress((root / "step4b_task_budget_feasibility.json.gz").read_bytes()))
        failed = [row for row in raw["rows"] if not row["accepted"]]
        counts = Counter()
        for row in failed:
            graph = generate_topology(row["n"], row["template"], row["seed"])
            nodes, truth, _, _ = relabel_roles(row["template"], graph.nodes, graph.edges, row["seed"])
            written = enumerate_mixed_recipes(nodes, truth, row["action"], row["target"])
            self.assertTrue(written["recipes"], (row["n"], row["template"], row["seed"]))
            self.assertTrue(any(recipe["fixed_order_valid"] for recipe in written["recipes"]))
            route_cut = enumerate_mixed_recipes(nodes, truth, row["action"], row["target"],
                                                require_path_survival=True, require_fn_on_path=True)
            peripheral_fn = enumerate_mixed_recipes(nodes, truth, row["action"], row["target"],
                                                    require_path_survival=True, require_fn_related=False)
            counts["route_fn_path_any"] += bool(route_cut["recipes"])
            counts["route_fn_path_fixed"] += route_cut["counts"]["fixed_fn_fp_rev_order_ok"] > 0
            counts["peripheral_fn_path_any"] += bool(peripheral_fn["recipes"])
            counts["peripheral_fn_path_fixed"] += peripheral_fn["counts"]["fixed_fn_fp_rev_order_ok"] > 0
        self.assertEqual(len(failed), 31)
        self.assertEqual(counts["route_fn_path_any"], 8)
        self.assertEqual(counts["route_fn_path_fixed"], 0)
        self.assertEqual(counts["peripheral_fn_path_any"], 31)
        self.assertEqual(counts["peripheral_fn_path_fixed"], 31)

    def test_preassigned_b_type_is_never_replaced_by_another_type(self):
        g = generate_topology(8, "multiple_directed_paths", 19)
        action, target = g.nodes[0], g.nodes[-1]
        for requested in ("FN", "FP", "REV"):
            r = inject_condition(g.nodes, g.edges, action, target, "B_path_survives",
                                 seed=derive_stream_seeds(17)["error_injection"],
                                 requested_b_type=requested)
            if r.accepted:
                self.assertEqual({e[0] for e in r.errors}, {requested})
            else:
                self.assertEqual(r.reason, f"no_path_preserving_task_related_{requested}")

    def test_h2_within_type_competition_fixture_all_three_error_types(self):
        nodes = tuple(f"V{i:02}" for i in range(6))
        scaffold = {("V02", "V05"), ("V02", "V03"), ("V03", "V05")}
        action, target = "V02", "V05"
        cases = {
            "FN": (scaffold | {("V02", "V04"), ("V00", "V01")}, scaffold),
            "FP": (scaffold, scaffold | {("V02", "V04"), ("V00", "V01")}),
            "REV": (scaffold | {("V02", "V04"), ("V00", "V01")},
                    scaffold | {("V04", "V02"), ("V01", "V00")}),
        }
        for kind, (truth, initial) in cases.items():
            outputs = {}
            for mode in ("G", "T"):
                outputs[mode] = refine(
                    node_ids=nodes, initial_edges=initial, reference_edges=truth,
                    allowed_types=(kind,), policy_id=f"{mode}-{kind}", budget=1,
                    gamma=1, action=action, target=target, seed=0)
            self.assertNotEqual(outputs["G"]["edit_sequence"], outputs["T"]["edit_sequence"], kind)
            self.assertNotEqual(outputs["G"]["final_hash"], outputs["T"]["final_hash"], kind)
            self.assertEqual(len(outputs["G"]["edit_sequence"]), 1)
            self.assertEqual(len(outputs["T"]["edit_sequence"]), 1)
            self.assertFalse(any(x["reason"] == "cycle" for x in outputs["G"]["rejected_operations"]))
            self.assertFalse(any(x["reason"] == "cycle" for x in outputs["T"]["rejected_operations"]))

    def test_h2_fixture_task_focused_is_role_stable_under_relabeling(self):
        nodes = tuple(f"V{i:02}" for i in range(6))
        scaffold = {("V02", "V05"), ("V02", "V03"), ("V03", "V05")}
        truth = scaffold | {("V02", "V04"), ("V00", "V01")}
        initial = scaffold
        permutation = {node: node for node in nodes}
        permutation["V00"], permutation["V04"] = "V04", "V00"
        relabel = lambda edges: {(permutation[a], permutation[b]) for a, b in edges}
        before = refine(node_ids=nodes, initial_edges=initial, reference_edges=truth,
                        allowed_types=("FN",), policy_id="T-FN", budget=1, gamma=1,
                        action="V02", target="V05", seed=0)
        after = refine(node_ids=nodes, initial_edges=relabel(initial), reference_edges=relabel(truth),
                       allowed_types=("FN",), policy_id="T-FN", budget=1, gamma=1,
                       action=permutation["V02"], target=permutation["V05"], seed=0)
        mapped_back = {(kind, permutation[a], permutation[b]) for kind, a, b in after["edit_sequence"]}
        self.assertEqual(set(before["edit_sequence"]), mapped_back)

    def test_graph_hash_includes_isolated_nodes_and_ignores_input_order(self):
        edges = [("a", "b"), ("c", "b")]
        self.assertNotEqual(graph_hash(("a", "b", "c"), edges),
                            graph_hash(("a", "b", "c", "isolated"), edges))
        self.assertEqual(graph_hash(("a", "b", "c"), edges),
                         graph_hash(("c", "b", "a"), list(reversed(edges))))

    def test_opportunity_counts_separate_candidates_from_dag_valid_fixes(self):
        nodes = ("a", "b", "c")
        truth = {("a", "b"), ("b", "c")}
        initial = {("b", "a"), ("b", "c"), ("a", "c")}
        counts = operation_opportunities(nodes, truth, initial)
        self.assertEqual(counts["REV"]["candidate_count"], 1)
        self.assertEqual(counts["FP"]["candidate_count"], 1)
        self.assertEqual(counts["FN"]["candidate_count"], 0)
        self.assertLessEqual(counts["REV"]["dag_valid_count"], counts["REV"]["candidate_count"])


if __name__ == "__main__":
    unittest.main()
