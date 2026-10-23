import copy
import unittest

from scripts.check_research_state import render
from src.reproduce_step6 import checked


class AssetRecoveryTests(unittest.TestCase):
    def test_unverified_zip_bytes_rejected(self):
        with self.assertRaises(ValueError):
            checked(b"not the original archive", "0" * 64)

    def test_duplicate_workstream_rejected(self):
        item = dict(id="SIM-01", status="BLOCKED", evidence="source", depends_on=[])
        with self.assertRaises(ValueError):
            render(dict(workstreams=[item, copy.deepcopy(item)]))

    def test_unknown_dependency_rejected(self):
        item = dict(id="SIM-01", status="BLOCKED", evidence="source", depends_on=["missing"])
        with self.assertRaises(ValueError):
            render(dict(workstreams=[item]))
