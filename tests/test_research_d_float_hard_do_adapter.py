import unittest

import networkx as nx
import numpy as np

from research.external_validation.semisynthetic_adapter.float_hard_do_adapter import (
    mutilated_graph_for_hard_do,
    sample_hard_do,
)


class ConstantMechanism:
    def __init__(self, value, expected_columns=()):
        self.value = value
        self.expected_columns = list(expected_columns)
        self.seen_columns = []

    def produce_sample(self, newdata, random_state):
        self.seen_columns.append(list(newdata.columns))
        if list(newdata.columns) != self.expected_columns:
            raise AssertionError(f"unexpected parent order: {list(newdata.columns)}")
        if callable(self.value):
            out = self.value(newdata)
        else:
            out = np.full(len(newdata), self.value)
        return np.asarray(out)


class FakeKDE:
    def __init__(self, values=(-1.0, 0.0, 1.0, 2.0)):
        self.dataset = np.asarray([values], dtype=float)

    def resample(self, size, seed):
        draws = seed.choice(self.dataset[0], size=size, replace=True)
        return draws.reshape(1, -1)


class FakeFittedModel:
    def __init__(self, edges, node_order, mechanisms):
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(node_order)
        self.graph.add_edges_from(edges)
        self.nodes = list(node_order)
        self.drf = mechanisms
        self.random_state = np.random.default_rng(19)
        self.mutilated_dags = {}
        self.interventional_drf = {}

    def parents(self, of_node):
        return list(self.graph.predecessors(of_node))

    def sample_from_drf(self, size=1):
        values = {}
        for node in nx.topological_sort(self.graph):
            mechanism = self.drf[node]
            parents = self.parents(node)
            if not parents and hasattr(mechanism, "resample"):
                values[node] = mechanism.resample(size=size, seed=np.random.default_rng(91))[0]
            else:
                frame = __import__("pandas").DataFrame(
                    {parent: values[parent] for parent in parents}, columns=parents
                )
                values[node] = mechanism.produce_sample(frame, np.random.default_rng(91))
        return __import__("pandas").DataFrame(values).reindex(columns=self.nodes)


class FloatHardDoAdapterTests(unittest.TestCase):
    def test_root_intervention_propagates_through_deterministic_chain(self):
        nodes = ["X", "M", "Y"]
        mechanisms = {
            "X": ConstantMechanism(999),
            "M": ConstantMechanism(None, ["X"]),
            "Y": ConstantMechanism(None, ["M"]),
        }
        mechanisms["M"].value = lambda d: 2 * d["X"].to_numpy()
        mechanisms["Y"].value = lambda d: d["M"].to_numpy() + 0.25
        model = FakeFittedModel([("X", "M"), ("M", "Y")], nodes, mechanisms)
        result = sample_hard_do(model, "X", np.float64(0.125), size=4, rng=np.random.default_rng(1))
        self.assertEqual(list(result.columns), nodes)
        np.testing.assert_array_equal(result["X"], [0.125] * 4)
        np.testing.assert_array_equal(result["M"], [0.25] * 4)
        np.testing.assert_array_equal(result["Y"], [0.5] * 4)
        self.assertEqual(mechanisms["M"].seen_columns, [["X"]])
        self.assertEqual(mechanisms["Y"].seen_columns, [["M"]])

    def test_multiple_parent_conditional_preserves_fitted_parent_column_order(self):
        nodes = ["X", "Z", "M", "Y"]
        mechanisms = {
            "X": FakeKDE([0.0]),
            "Z": FakeKDE([2.0]),
            # Edge insertion makes the fitted parent order Z, X, deliberately
            # different from the public node order X, Z, M, Y.
            "M": ConstantMechanism(None, ["Z", "X"]),
            "Y": ConstantMechanism(None, ["M"]),
        }
        mechanisms["M"].value = lambda d: 10 * d["Z"].to_numpy() + d["X"].to_numpy()
        mechanisms["Y"].value = lambda d: d["M"].to_numpy() - 1
        model = FakeFittedModel(
            [("Z", "M"), ("X", "M"), ("M", "Y")], nodes, mechanisms
        )
        result = sample_hard_do(model, "X", 0.125, size=3, rng=np.random.default_rng(41))
        np.testing.assert_array_equal(result["X"], [0.125] * 3)
        np.testing.assert_array_equal(result["Z"], [2.0] * 3)
        np.testing.assert_array_equal(result["M"], [20.125] * 3)
        np.testing.assert_array_equal(result["Y"], [19.125] * 3)
        self.assertEqual(mechanisms["M"].seen_columns, [["Z", "X"]])
        self.assertEqual(mechanisms["Y"].seen_columns, [["M"]])

    def test_nonroot_do_cuts_parent_mechanism_but_keeps_other_mechanisms(self):
        nodes = ["Z", "X", "M", "Y"]
        mechanisms = {
            "Z": FakeKDE([7]),
            "X": ConstantMechanism(None, ["Z"]),
            "M": ConstantMechanism(None, ["X"]),
            "Y": ConstantMechanism(None, ["M"]),
        }
        mechanisms["X"].value = lambda d: 100 + d["Z"].to_numpy()
        mechanisms["M"].value = lambda d: d["X"].to_numpy() + 1
        mechanisms["Y"].value = lambda d: 3 * d["M"].to_numpy()
        model = FakeFittedModel(
            [("Z", "X"), ("X", "M"), ("M", "Y")], nodes, mechanisms
        )
        edges_before = set(model.graph.edges)
        mutilated = mutilated_graph_for_hard_do(model.graph, "X")
        self.assertEqual(set(mutilated.edges), {("X", "M"), ("M", "Y")})
        self.assertEqual(set(model.graph.edges), edges_before)
        mechanism_ids = {key: id(value) for key, value in model.drf.items()}
        result = sample_hard_do(model, "X", 0.375, size=3, rng=np.random.default_rng(2))
        np.testing.assert_array_equal(result["Z"], [7] * 3)
        np.testing.assert_array_equal(result["X"], [0.375] * 3)
        np.testing.assert_array_equal(result["M"], [1.375] * 3)
        np.testing.assert_array_equal(result["Y"], [4.125] * 3)
        self.assertEqual(mechanisms["X"].seen_columns, [])
        self.assertEqual(mechanisms["M"].seen_columns, [["X"]])
        self.assertEqual(mechanisms["Y"].seen_columns, [["M"]])
        self.assertEqual(set(model.graph.edges), edges_before)
        self.assertEqual({key: id(value) for key, value in model.drf.items()}, mechanism_ids)

    def test_non_descendant_uses_its_original_mechanism(self):
        nodes = ["X", "M", "Y", "U"]
        mechanisms = {
            "X": FakeKDE([9]),
            "M": ConstantMechanism(None, ["X"]),
            "Y": ConstantMechanism(None, ["M"]),
            "U": FakeKDE([42]),
        }
        mechanisms["M"].value = lambda d: d["X"].to_numpy() + 1
        mechanisms["Y"].value = lambda d: d["M"].to_numpy() + 1
        model = FakeFittedModel([("X", "M"), ("M", "Y")], nodes, mechanisms)
        first = sample_hard_do(model, "X", 0.2, size=2, rng=np.random.default_rng(3))
        second = sample_hard_do(model, "X", 0.8, size=2, rng=np.random.default_rng(3))
        np.testing.assert_array_equal(first["U"], [42, 42])
        np.testing.assert_array_equal(first["U"], second["U"])
        np.testing.assert_array_equal(first["Y"], [2.2, 2.2])
        np.testing.assert_array_equal(second["Y"], [2.8, 2.8])

    def test_repeated_interventions_and_observational_run_have_no_state_leak(self):
        nodes = ["X", "M"]
        mechanisms = {"X": FakeKDE([9]), "M": ConstantMechanism(None, ["X"])}
        mechanisms["M"].value = lambda d: d["X"].to_numpy() * 10
        model = FakeFittedModel([("X", "M")], nodes, mechanisms)
        original_edges = list(model.graph.edges)
        original_mechanisms = dict(model.drf)
        a = sample_hard_do(model, "X", 0.1, size=2, rng=np.random.default_rng(4))
        b = sample_hard_do(model, "X", 0.7, size=2, rng=np.random.default_rng(4))
        obs = model.sample_from_drf(size=2)
        np.testing.assert_array_equal(a["M"], [1, 1])
        np.testing.assert_array_equal(b["M"], [7, 7])
        np.testing.assert_array_equal(obs["X"], [9, 9])
        np.testing.assert_array_equal(obs["M"], [90, 90])
        self.assertEqual(list(model.graph.edges), original_edges)
        self.assertEqual(model.drf, original_mechanisms)
        self.assertEqual(model.mutilated_dags, {})
        self.assertEqual(model.interventional_drf, {})

    def test_same_seed_reproduces_stochastic_fixture_and_other_seed_runs(self):
        nodes = ["X", "Y", "U"]
        mechanisms = {
            "X": FakeKDE([-1.0, 0.0, 1.0, 2.0]),
            "Y": ConstantMechanism(None, ["X"]),
            "U": FakeKDE([-1.0, 0.0, 1.0, 2.0]),
        }
        mechanisms["Y"].value = lambda d: d["X"].to_numpy() ** 2
        model = FakeFittedModel([("X", "Y")], nodes, mechanisms)
        one = sample_hard_do(model, "X", 0.5, size=10, rng=np.random.default_rng(5))
        repeat = sample_hard_do(model, "X", 0.5, size=10, rng=np.random.default_rng(5))
        other = sample_hard_do(model, "X", 0.5, size=10, rng=np.random.default_rng(6))
        self.assertTrue(one.equals(repeat))
        self.assertFalse(one.equals(other))
        np.testing.assert_array_equal(one["Y"], [0.25] * 10)

    def test_unsmoothed_root_bootstrap_is_seeded_and_samples_with_replacement(self):
        nodes = ["X", "Y", "U"]
        mechanisms = {
            "X": FakeKDE([0]),
            "Y": ConstantMechanism(None, ["X"]),
            "U": FakeKDE([2, 5, 8]),
        }
        mechanisms["Y"].value = lambda d: d["X"].to_numpy() + 1
        model = FakeFittedModel([("X", "Y")], nodes, mechanisms)
        first = sample_hard_do(
            model, "X", 0.75, size=20, rng=np.random.default_rng(29), smoothed=False
        )
        repeat = sample_hard_do(
            model, "X", 0.75, size=20, rng=np.random.default_rng(29), smoothed=False
        )
        self.assertTrue(first.equals(repeat))
        self.assertEqual(set(first["U"]), {2, 5, 8})
        self.assertEqual(first["U"].nunique(), 3)
        np.testing.assert_array_equal(first["Y"], [1.75] * 20)

    def test_rejects_invalid_inputs_and_missing_mechanisms(self):
        model = FakeFittedModel([("X", "Y")], ["X", "Y"], {
            "X": ConstantMechanism(0), "Y": ConstantMechanism(None, ["X"])
        })
        model.drf["Y"].value = lambda d: d["X"].to_numpy()
        bad_values = [
            True, np.bool_(False), "0.5", 1 + 2j, np.complex64(2 + 1j),
            np.nan, np.inf, -np.inf, 10**400,
        ]
        for value in bad_values:
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                sample_hard_do(model, "X", value, size=2, rng=np.random.default_rng(7))
        for size in [0, -1, 1.5, True]:
            with self.subTest(size=size), self.assertRaises(ValueError):
                sample_hard_do(model, "X", 0.5, size=size, rng=np.random.default_rng(7))
        with self.assertRaises(ValueError):
            sample_hard_do(model, "missing", 0.5, size=2, rng=np.random.default_rng(7))
        with self.assertRaises(TypeError):
            sample_hard_do(model, "X", 0.5, size=2, rng=7)
        model.drf.pop("Y")
        with self.assertRaises(ValueError):
            sample_hard_do(model, "X", 0.5, size=2, rng=np.random.default_rng(7))


if __name__ == "__main__":
    unittest.main()
