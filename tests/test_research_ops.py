import unittest

from scripts.check_research_docs import missing_documents
from src.acquire_reference_data import FILES, COMMIT


class ResearchOpsTest(unittest.TestCase):
    def test_substantive_change_requires_all_three(self):
        self.assertEqual(missing_documents({"src/new.py", "PROJECT_STATUS.md"}),
                         {"PRIORITIES.md", "WORK_LOG.md"})

    def test_document_only_change_is_exempt(self):
        self.assertEqual(missing_documents({"README.md"}), set())

    def test_pinned_inputs(self):
        self.assertEqual(len(COMMIT), 40)
        self.assertEqual(set(FILES), {"datasetTE.csv", "TEGroundTruth.txt"})
        self.assertTrue(all(len(value) == 64 for value in FILES.values()))


if __name__ == "__main__":
    unittest.main()
