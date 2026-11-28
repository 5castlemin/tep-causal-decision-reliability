"""Small hand DAGs only: no SCM, intervention, or research regret."""
import tempfile
import unittest
from pathlib import Path

from research.original_objective.policy_engine import (
    Config, UNRES, apply, candidates, catalog, classify, dag, evaluation_record,
    graph_hash, metrics, pair, run, run_catalog, save_json, state, task_zone,
)


class PolicyEngineTests(unittest.TestCase):
    def setUp(self):
        self.gt = state([("X", "A"), ("A", "Y"), ("X", "B"), ("B", "Y"), ("T", "U"), ("P", "Q")])
        self.g0 = state([("A", "Y"), ("X", "B"), ("B", "Y"), ("Q", "P"), ("R", "S")])

    def test_fixture_metrics_and_denominator_illusion(self):
        s = metrics(self.gt, self.g0, "X", "Y", Config())
        self.assertEqual(s["report"]["M1"]["value"], .5)
        self.assertEqual(s["report"]["M2"]["value"], .5)
        self.assertEqual(s["report"]["M3_accuracy"]["value"], 0)
        self.assertEqual(s["counts"]["M4"]["FN"], 1)
        op = next(e for e in candidates(self.gt, self.g0, "X", "Y", Config()) if e.metric == "M1")
        after = metrics(self.gt, apply(self.g0, op), "X", "Y", Config())
        self.assertEqual(after["report"]["M2"]["numerator"], 1)
        self.assertEqual(after["report"]["M2"]["denominator"], 3)

    def test_catalog_and_budget(self):
        self.assertEqual(len(catalog()), 16)
        for budget in range(5):
            result = run_catalog(self.gt, self.g0, "X", "Y", budget)
            self.assertEqual(len(result["strategies"]), 16)
            for r in result["strategies"] + [result["canonical_oracle"]]:
                self.assertLessEqual(r["total_cost"], budget)
                self.assertEqual(len({tuple(e["pair"]) for e in r["edits"]}), len(r["edits"]))
        self.assertEqual(run(self.gt, self.g0, "X", "Y", 1, (), Config())["final_hash"], graph_hash(self.g0))
        self.assertEqual(run(self.gt, self.g0, "X", "Y", 1, ("M1",), Config())["final_hash"],
                         run(self.gt, self.g0, "X", "Y", 1, ("M1", "M2", "M3", "M4"), Config())["final_hash"])

    def test_cost_and_dag_rejection(self):
        cfg = Config(costs=(("add", 2), ("delete", 1), ("orient", 3), ("resolve", 1), ("delete_unresolved", 1)))
        self.assertEqual(run(self.gt, self.g0, "X", "Y", 1, ("M1",), cfg)["total_cost"], 0)
        gt, g0 = state([("A", "B")]), state([("B", "C"), ("C", "A")])
        r = run(gt, g0, "A", "B", 1, ("M4",))
        self.assertEqual(r["stop_reason"], "dag_invalid_candidate")
        self.assertEqual(r["total_cost"], 0)
        self.assertTrue(dag(g0))

    def test_unresolved_and_task_vector(self):
        gt = state([("A", "B"), ("C", "D")])
        wrong = state([("B", "A"), ("C", "D")])
        unclear = state([("C", "D")], [("A", "B")])
        a = metrics(gt, wrong, "A", "Z", Config())
        b = metrics(gt, unclear, "A", "Z", Config())
        self.assertEqual(a["report"]["M3_accuracy"]["value"], .5)
        self.assertEqual(b["report"]["M3_accuracy"]["value"], 1)
        self.assertEqual(b["report"]["M3_unresolved"]["value"], .5)
        self.assertEqual(a["counts"]["M3"]["REV"], 1)
        self.assertEqual(b["counts"]["M3"]["UNRES"], 1)
        gt4 = state([("X", "M"), ("M", "Y"), ("X", "A"), ("A", "Y"), ("Z", "X"), ("Z", "Y"), ("W", "M")])
        est4 = state([("M", "Y"), ("Y", "A"), ("Z", "X"), ("Z", "Y"), ("W", "M"), ("X", "Y"), ("W", "X")], [("X", "M")])
        a4 = metrics(gt4, est4, "X", "Y", Config())
        b4 = metrics(gt4, est4, "X", "Y", Config(fp_rule="B", route_relevant_fp=(("W", "X"),)))
        self.assertEqual(a4["counts"]["M4"], {"FN": 1, "FP": 1, "REV": 1, "UNRES": 1})
        self.assertEqual(b4["counts"]["M4"]["FP"], 2)

    def test_normalization_and_no_outcome_access(self):
        r1 = run(self.gt, self.g0, "X", "Y", 1, ("M1", "M2", "M3", "M4"), Config(normalization="initial_error_count"))
        r2 = run(self.gt, self.g0, "X", "Y", 1, ("M1", "M2", "M3", "M4"), Config())
        self.assertEqual(r1["edits"][0]["metric"], "M1")
        self.assertEqual(r2["edits"][0]["metric"], "M1")
        self.assertIsNone(r1["evaluation"]["decision_regret"])
        self.assertEqual(evaluation_record({"a": 1, "b": 1})["decision_margin"], 0)

    def test_empty_graph_zero_denominator_and_stability(self):
        empty = state()
        stats = metrics(empty, empty, "X", "Y", Config())
        self.assertIsNone(stats["report"]["M1"]["value"])
        self.assertEqual(stats["report"]["M1"]["na_reason"], "zero_denominator")
        self.assertEqual(run(empty, empty, "X", "Y", 3, ("M1",))["stop_reason"], "candidate_pool_exhausted")
        self.assertEqual(run(self.gt, self.g0, "X", "Y", 2, ("M1", "M2")),
                         run(self.gt, self.g0, "X", "Y", 2, ("M1", "M2")))

    def test_multiple_candidates_cost_order_and_serialization(self):
        gt = state([("X", "M"), ("M", "Y"), ("A", "B"), ("C", "D")])
        g0 = state([("X", "M"), ("M", "Y")])
        r = run(gt, g0, "X", "Y", 2, ("M1",))
        self.assertEqual([e["pair"] for e in r["edits"]], [("A", "B"), ("C", "D")])
        self.assertEqual(r["total_cost"], 2)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "result.json"
            save_json(p, r)
            self.assertIn('"decision_regret": null', p.read_text(encoding="utf-8"))

    def test_task_zone_open_backdoor_vs_collider(self):
        gt = state([("X", "M"), ("M", "Y"), ("Z", "X"), ("Z", "Y"), ("X", "C"), ("Y", "C")])
        zone, nodes = task_zone(gt, "X", "Y")
        self.assertIn(pair("Z", "X"), zone)
        self.assertIn(pair("Z", "Y"), zone)
        self.assertNotIn(pair("X", "C"), zone)
        self.assertNotIn(pair("Y", "C"), zone)


if __name__ == "__main__":
    unittest.main()
