"""Recording clocks must not be silently treated as identical."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research_runs/tep_dynamics_alignment'))
from analyze_alignment import sampled

class ClockTests(unittest.TestCase):
    def test_hold_is_distinct_from_interpolation(self):
        a=np.zeros((2,54));a[:,0]=[0,2];a[1,1:]=10
        self.assertEqual(sampled(a,np.array([1.]))[0,0],0)
        self.assertEqual(sampled(a,np.array([1.]),'linear')[0,0],5)

    def test_duplicate_timestamp_uses_last_emitted_value(self):
        a=np.zeros((4,54));a[:,0]=[0,2,1,2];a[:,1:]=np.array([0,10,4,20])[:,None]
        np.testing.assert_array_equal(sampled(a,np.array([1.,2.]))[:,0],[4,20])

if __name__=='__main__':unittest.main()
