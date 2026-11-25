import unittest
import json
from pathlib import Path

import pandas as pd

from research.external_validation.design_resolution.inspect_wt_blocks import inspect_frame
from research.external_validation.design_resolution.preflight import qualify_graph, fixture_checks


class ResearchDDesignPreflightTests(unittest.TestCase):
    def test_wind_tunnel_tasks_are_direct_and_have_no_rule_a_task_fp_support(self):
        result = qualify_graph()
        self.assertEqual((result["nodes"], result["edges"], result["unordered_pairs"]), (32, 42, 496))
        self.assertEqual((result["reference_absent_pairs"], result["oriented_absent_candidates"]), (454, 908))
        for target in ("rpm_in", "pressure_intake"):
            task = result["tasks"][target]
            self.assertTrue(task["reference_direct_edge"])
            self.assertEqual(len(task["zone_pairs"]), 1)
            self.assertEqual(task["task_fp_opportunities_rule_a"], 0)
        self.assertFalse(result["response_values_read"])

    def test_graph_schema_validation_uses_the_intake_experiment(self):
        path = Path(__file__).resolve().parents[1] / "research" / "external_validation" / "inspection_results.json"
        inspection = json.loads(path.read_text(encoding="utf-8"))
        experiments = inspection["chamber"]["wt_bernoulli_v1"]["experiments"]
        expected = set(experiments["random_loads_intake"]["dtypes"])
        self.assertEqual(experiments["random_loads_intake"]["dtypes"], experiments["random_loads_both"]["dtypes"])
        experiments["random_loads_both"]["dtypes"] = []
        result = qualify_graph(inspection)
        self.assertEqual(result["csv_schema_experiment"], "random_loads_intake")
        self.assertTrue(result["all_graph_nodes_in_csv_schema"])
        self.assertEqual(result["csv_variables_outside_graph"], sorted(expected - set(inspection["mk1_graphs"]["wt_standard"]["nodes"])))

    def test_policy_metric_fixture_covers_m1_through_m4(self):
        cases = fixture_checks()["cases"]
        expected = {
            "task_fn": ("M4", "FN"), "task_rev": ("M4", "REV"),
            "task_unres": ("M4", "UNRES"), "task_fp": ("M4", "FP"),
            "off_fn": ("M1", "FN"), "off_rev": ("M3", "REV"),
            "off_unres": ("M3", "UNRES"), "off_fp": ("M2", "FP"),
        }
        for case, (metric, kind) in expected.items():
            self.assertEqual(cases[case][metric][kind], 1, case)

    def test_block_inspector_checks_assignment_not_responses(self):
        frame = pd.DataFrame({
            "timestamp": [*range(100), *range(101, 201)], "config": ["standard"] * 200,
            "counter": list(range(200)), "flag": [0] * 100 + [1] * 100,
            "intervention": [1] + [0] * 99 + [1] + [0] * 99,
            "load_in": [.25] * 100 + [.75] * 100,
            "load_out": [.1] * 200, "hatch": [0] * 200,
        })
        result = inspect_frame(frame)
        self.assertEqual(result["blocks"], 2)
        self.assertEqual(result["block_size_min"], 100)
        self.assertFalse(result["response_values_read"])


if __name__ == "__main__":
    unittest.main()
