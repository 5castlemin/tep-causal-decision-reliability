"""Stable entry point for corrected Step 4B-4 v2 calibration.

The historical v1 JSON is immutable; this entry point now writes v2 output.
"""
from .run_step4b4_statistical_calibration_v2 import main

if __name__ == "__main__":
    main()
