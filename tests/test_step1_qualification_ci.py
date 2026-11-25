"""Expose Step 1 qualification validators to the repository's root CI discovery."""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = (Path(__file__).resolve().parents[1] / "research" / "external_validation" /
               "qualification" / "validate_qualification.py")
SPEC = importlib.util.spec_from_file_location("step1_qualification_validator", MODULE_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class Step1QualificationCITests(unittest.TestCase):
    def test_step1_pair_and_constant_metadata_remain_validated_by_root_ci(self):
        result = VALIDATOR.validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual((result["unordered_pairs"], result["unordered_nonedges"],
                          result["oriented_fp_candidates"]), (4005, 3863, 7726))
        self.assertFalse(result["response_values_read"])


if __name__ == "__main__":
    unittest.main()
