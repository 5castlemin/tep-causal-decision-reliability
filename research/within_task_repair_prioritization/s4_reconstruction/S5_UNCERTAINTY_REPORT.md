# S5 Uncertainty Report

Loss estimator: `((mean(Y)-target)^2 - sample_variance(Y)/n) / scale^2`, sample variance `ddof=1`, no negative clipping. Each action's evaluation vector is shared across all G0s and policies selecting that action. Bootstrap uses 10,000 replicates and chunked draws.

For primary `loss(S0) − loss(M4)`, B=2:

| Component | 95% interval | Half-width | Includes zero? |
|---|---:|---:|---|
| G0-only | [0.0048631, 0.0090237] | 0.0020803 | No |
| Action-MC-only | [−0.0088964, 0.0231993] | 0.0160478 | Yes |
| Two-source | [−0.0092609, 0.0227350] | 0.0159980 | Yes |

The action-MC half-width target of 0.020 and two-source target of 0.025 were met. Meeting precision targets does not imply a nonzero effect: both intervals that include action sampling uncertainty cross zero. G0-only uncertainty alone is conditional on the five observed action-loss estimates. These are pointwise intervals, not simultaneous intervals.

The inferential unit is one of 200 corruption draws from one fixed fitted DGP and training frame. Generator-fit uncertainty, source-data uncertainty, training-frame variability, and manufacturing-population uncertainty are not represented. The all-action sample means (14.01–14.10) fell below the chosen target 15.596 in this finite sample; this does not establish population target infeasibility.
