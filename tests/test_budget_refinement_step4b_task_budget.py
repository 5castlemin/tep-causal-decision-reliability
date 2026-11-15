import unittest
import json
import gzip
from pathlib import Path
from collections import Counter

from research.budget_aware_refinement.step4_topology_generator import (
    TEMPLATES, generate_topology, is_dag,
)
from research.budget_aware_refinement.step4b_task_budget import (
    classify_task_pairs, operation_opportunities, relabel_roles,
    role_nodes, select_task_pair,
)


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
        g = generate_topology(8, "observed_common_cause", 17)
        nodes, edges, roles, _ = relabel_roles(g.template, g.nodes, g.edges, 17)
        preferred = (roles["action"], roles["target"])
        selected = select_task_pair(nodes, edges, 17, preferred)
        self.assertEqual(selected["selected"][1][1], preferred)
        self.assertNotEqual(selected["selected"][0][1], preferred)
        self.assertIn(preferred, classify_task_pairs(nodes, edges).indirect_only +
                      classify_task_pairs(nodes, edges).direct_and_indirect)

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
