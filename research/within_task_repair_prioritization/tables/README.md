# S3 result table versions

The top-level `s3_*.csv` files are historical first-run exploratory outputs and remain unchanged. They are not the corrected selectors. The corrected replay based on contract commit `b832001c701f8183cb7ddb53ba02950785a36a9a` and executed code revision `616ec21499eb4cd4b43139423240cd380a643d86` is stored under `correction_v1/`. Public tables contain only cohort-level aggregates; SCM-keyed unit outputs are not published. Do not merge rows across the historical and corrected versions.
