import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from audit_manufacturing_validity import histogram_summary,guard_probe

class ManufacturingValidityTests(unittest.TestCase):
    def test_lossy_f1_csv_does_not_erase_discrete_ties(self):
        h=dict(values=[0.,.1194],counts=[9500,500],canonical_values=[0.,8/67],comparison_values=[0,4],comparison_observed=4)
        r=histogram_summary(h,8/67,True)
        self.assertAlmostEqual(r['p'],501/10001);self.assertAlmostEqual(r['p_raw_csv_float'],1/10001)
    def test_legacy_join_guard_is_not_metadata_validation(self):
        p=guard_probe();self.assertTrue(p['different_environment_ids_rejected']);self.assertTrue(p['same_label_and_all_flags_accepted']);self.assertFalse(p['node_clock_controller_reference_hashes_validated'])
    def test_saved_audit(self):
        from validate_manufacturing_validity import validate
        validate()
if __name__=='__main__':unittest.main()
