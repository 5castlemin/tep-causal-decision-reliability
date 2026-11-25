# Research D final uncertainty report

## Primary B=2 contrast

| Source of variation | Paired 95% interval | Half-width | Reporting goal | Met? |
|---|---:|---:|---:|---|
| G0 corruption draw | [0.026645, 0.041805] | 0.007580 | descriptive | — |
| Action Monte Carlo | [0.006510, 0.062850] | 0.028170 | ≤ 0.020 | False |
| Two-source | [0.006173, 0.065351] | 0.029589 | ≤ 0.025 | False |

Point estimate: `0.03422490`; paired G0 count 200; 10,000 percentile bootstrap replicates, chunk size 128. G0s are resampled as paired units. Within each replicate, the independently resampled action loss vectors form one shared action-loss table applied across every G0 and policy. Action draws are independent streams. No final sample size was increased after seeing precision.

Both action-MC and combined half-width goals were missed. Their intervals are above zero in this conditional evaluation, but the unmet precision goals require reporting the wider uncertainty and should not be hidden by the positive point estimate. These intervals do not include uncertainty in the fitted DRF, source semisynthetic data, graph/reference validity, new training frames, physical systems, or manufacturing populations.

## Secondary and action sampling uncertainty

M4−Full Greedy at B=2 was `0.001230` with paired two-source interval `0.000000 to 0.003916`. The paired edit-cost difference interval is reported in the results. No equivalence or noninferiority claim follows from the many identical actions.

The action-specific standard errors in `RESEARCH_D_FINAL_RESULTS.md` use independent response draws under the fixed DRF for each action. The primary uses bias-corrected target-tracking loss of the intervention sample mean, not individual-row MSE. Its finite sample correction is `sample variance / n`, ddof=1, and no negative clipping is applied.

Absolute empirical regret is not a primary result. The minimum loss over the same sampled actions would add a winner-selection uncertainty not needed for the paired policy contrast.
