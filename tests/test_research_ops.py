import unittest

from scripts.check_research_docs import missing_documents
from src.acquire_reference_data import FILES, COMMIT


class ResearchOpsTest(unittest.TestCase):
    def test_substantive_change_requires_live_research_documents(self):
        required = {
            "docs/research_state_current.json",
            "docs/current/PROJECT_STATUS_CURRENT.md",
            "docs/current/PRIORITIES_CURRENT.md",
            "docs/current/WORK_LOG_CURRENT.md",
        }
        self.assertEqual(missing_documents({"src/new.py", "PROJECT_STATUS.md"}), required)
        self.assertEqual(missing_documents({"research/original_objective/policy_engine.py"}), required)
        self.assertEqual(missing_documents({"src/new.py"} | required), set())
        self.assertEqual(missing_documents({"src/new.py", "PROJECT_STATUS.md", "PRIORITIES.md", "WORK_LOG.md"}), required)

    def test_document_only_change_is_exempt(self):
        self.assertEqual(missing_documents({"README.md"}), set())

    def test_pinned_inputs(self):
        self.assertEqual(len(COMMIT), 40)
        self.assertEqual(set(FILES), {"datasetTE.csv", "TEGroundTruth.txt"})
        self.assertTrue(all(len(value) == 64 for value in FILES.values()))


if __name__ == "__main__":
    unittest.main()
