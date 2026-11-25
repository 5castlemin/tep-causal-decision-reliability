import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import networkx as nx
import pandas as pd

from research.external_validation.inspect_support import (
    chamber_csv, file_record, graph_record, linked_leds_figure, retrieve,
)


class ExternalValidationSupportTest(unittest.TestCase):
    def test_existing_download_requires_matching_hash(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            path = folder / "data.zip"
            path.write_bytes(b"pinned fixture")
            manifest = {"file": path.name, **file_record(path)}
            self.assertEqual(retrieve(manifest, folder, False)[0], path)
            path.write_bytes(b"modified bytes")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch|sha256 mismatch"):
                retrieve(manifest, folder, False)

    def test_strict_paths_exclude_direct_pairs_and_cycles(self):
        graph = nx.DiGraph([("a", "b"), ("b", "c")])
        self.assertEqual(graph_record(graph)["strict_pairs_all_nodes"], [["a", "c"]])
        graph.add_edge("a", "c")
        self.assertEqual(graph_record(graph)["strict_pairs_all_nodes"], [])
        graph.add_edge("c", "b")
        self.assertIsNone(graph_record(graph)["strict_pairs_all_nodes"])

    def test_mk2_has_mediated_current_but_direct_light_edge(self):
        graph = linked_leds_figure()
        self.assertTrue(nx.is_directed_acyclic_graph(graph))
        self.assertTrue(nx.has_path(graph, "green", "current_led_2_uv"))
        self.assertFalse(graph.has_edge("green", "current_led_2_uv"))
        self.assertTrue(graph.has_edge("green", "ir_2"))

    def test_assignment_blocks_and_command_counts_exclude_outcome_values(self):
        frame = pd.DataFrame({
            "flag": [0, 0, 1, 1, 2, 2], "load_in": [.5, .5, .5, .5, .8, .8],
            "pressure_intake": [99111] * 6,
        })
        result = chamber_csv(frame, "wt_bernoulli_v1", "random_loads_intake", {}, None)
        self.assertEqual(result["load_in_assignment_blocks"], {"0.5": 2, "0.8": 1})
        self.assertEqual(result["command_rows"]["load_in"], {"0.5": 4, "0.8": 2})
        self.assertNotIn("99111", str(result))

    def test_pressure_sensor_value_is_excluded_from_assignment(self):
        frame = pd.DataFrame({"flag": [0, 1], "pressure_downwind": [99111, 99112]})
        protocols = {"test": ("pressure_downwind", {"xA": 93000, "xB": 95000, "T": 0, "N": 2})}
        result = chamber_csv(frame, "wt_pc_validate_v1", "test", protocols, None)
        self.assertEqual(result["assignment"]["levels_flag_0_1"], [93000, 95000])
        self.assertNotIn("99111", str(result))
