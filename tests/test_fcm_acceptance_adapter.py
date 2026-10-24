"""Local guard/reconstruction tests; do not load or execute the external candidate."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('adapter',Path(__file__).resolve().parents[1]/'src/fcm_acceptance_adapter.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class AdapterTests(unittest.TestCase):
    def test_modified_source_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'candidate.py';p.write_text('raise AssertionError("must not import")',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'SOURCE_HASH_MISMATCH'):m.load_pinned_module(p)

    def test_wrong_observation_mechanism_detected(self):
        import numpy as np
        import pandas as pd
        noise={'u_R':np.array([1.,2.]),'u_A':np.array([.5,-.5]),'u_M':np.array([.1,.2]),'u_Y':np.array([.01,.02])}
        frame=pd.DataFrame(dict(R=[1.,2.],A=[2.5,3.5],M=[7.6,10.7],Y=[8.61,12.72]))
        self.assertLess(max(m.reconstruction(frame,noise).values()),1e-10)
        frame['Y']+=1
        self.assertAlmostEqual(m.reconstruction(frame,noise)['Y'],1)

    def test_hard_do_does_not_require_removed_noise(self):
        import numpy as np
        import pandas as pd
        noise={'u_R':np.array([1.,2.]),'u_M':np.array([.1,.2]),'u_Y':np.array([.01,.02])}
        frame=pd.DataFrame(dict(R=[1.,2.],A=[.1,.1],M=[.4,.5],Y=[1.41,2.52]))
        self.assertLess(max(m.reconstruction(frame,noise,action=.1).values()),1e-10)
        frame.loc[0,'A']=.2
        self.assertAlmostEqual(m.reconstruction(frame,noise,action=.1)['A'],.1)
