"""실제 TEP 점수를 생성하지 않는 작은 선형 Ridge 규약 검사."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pilot_fit import design, fit_ridge  # noqa: E402


class PilotFitTest(unittest.TestCase):
    def test_root_and_parent_lag(self):
        data = np.arange(10, dtype=float).reshape(5, 2)
        rows = np.array([1, 2, 3])
        actual = design(data, rows, [("X1", 1)], {"X1": 0, "X2": 1})
        np.testing.assert_array_equal(actual[:, 0], [0, 2, 4])
        beta, intercept = fit_ridge(np.empty((3, 0)), np.array([1., 2., 3.]), 0.1)
        self.assertEqual(len(beta), 0)
        self.assertEqual(intercept, 2.0)

    def test_ridge_penalty_and_intercept(self):
        X = np.array([[0.], [1.], [2.]])
        y = np.array([1., 3., 5.])
        beta, intercept = fit_ridge(X, y, 0.1)
        self.assertTrue(0 < beta[0] < 2)
        self.assertAlmostEqual(intercept + beta[0], 3.0)


if __name__ == "__main__":
    unittest.main()
