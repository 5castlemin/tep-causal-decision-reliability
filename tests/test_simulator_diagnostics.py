"""Catch state/observation clock conflation in numerical comparisons."""
import importlib.util
import unittest
from pathlib import Path

import numpy as np

path=Path(__file__).resolve().parents[1]/'experiments/simulator/diagnostics/analyze_diagnostics.py'
spec=importlib.util.spec_from_file_location('diagnostic_analysis',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ClockTests(unittest.TestCase):
    def test_measurements_match_evaluation_clock_not_state_clock(self):
        a=np.array([[0,0,0],[30,29,29],[31,30,30]],float)
        b=np.array([[0,0,0],[30,29.5,29.5],[30.5,30,30]],float)
        self.assertEqual(module.difference(a,b,1,2)['max_abs'],0)
        self.assertEqual(module.difference(a,b,0,2)['max_abs'],.5)

    def test_no_matching_time_is_failure(self):
        with self.assertRaises(ValueError):
            module.difference(np.array([[1,1,1.]]),np.array([[2,2,2.]]),0,2)


if __name__=='__main__':unittest.main()
