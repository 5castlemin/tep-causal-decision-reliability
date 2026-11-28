# Research D final results

## Scope

This is `CONDITIONAL_EXTERNAL_SEMISYNTHETIC_ROBUSTNESS`: one DRF-based DGP fit to causalAssembly's pinned public semisynthetic sample and the official Station1 benchmark DAG, with the exact fixed Development learner frame. The 200 units are graph-corruption draws under this fixed environment, not independent SCMs. Actions are virtual benchmark hard-do values, not verified manufacturing controls. Results are reference-relative, not evidence against a complete physical GT.

## Primary at B=2

`Δ_D = L(S0) − L(Full Greedy) = 0.034225` standardized tracking-loss units (n=200 paired G0s). Positive favors Full Greedy. The three predeclared intervals are reported in the uncertainty report; the two-source 95% interval is `0.006173 to 0.065351`. Full Greedy changed the S0 action on 56/200 G0s: 56 improved, 144 tied, 0 worsened. This is conditional evidence for this single fitted generator and fixed training frame, not a physical-process result.

## B=2 policy results

| Policy | Mean bias-corrected loss | Mean edit cost | Task-zone edits/G0 | Off-task edits/G0 | No-op rate | Budget unused rate |
|---|---:|---:|---:|---:|---:|---:|
| S0 | 0.823587 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| M1 | 0.822972 | 0.255 | 0.000 | 0.255 | 0.770 | 0.975 |
| M2 | 0.824405 | 0.325 | 0.000 | 0.325 | 0.700 | 0.975 |
| M3 | 0.823587 | 0.440 | 0.000 | 0.440 | 0.625 | 0.935 |
| M4 | 0.790592 | 0.335 | 0.335 | 0.000 | 0.690 | 0.975 |
| M1+M2 | 0.823790 | 0.565 | 0.000 | 0.565 | 0.540 | 0.895 |
| M1+M3 | 0.823587 | 0.675 | 0.000 | 0.675 | 0.480 | 0.845 |
| M1+M4 | 0.790592 | 0.570 | 0.335 | 0.235 | 0.530 | 0.900 |
| M2+M3 | 0.824405 | 0.735 | 0.000 | 0.735 | 0.445 | 0.820 |
| M2+M4 | 0.789362 | 0.655 | 0.340 | 0.315 | 0.465 | 0.880 |
| M3+M4 | 0.789977 | 0.735 | 0.330 | 0.405 | 0.460 | 0.805 |
| M1+M2+M3 | 0.823790 | 0.935 | 0.000 | 0.935 | 0.335 | 0.730 |
| M1+M2+M4 | 0.789362 | 0.865 | 0.340 | 0.525 | 0.355 | 0.780 |
| M1+M3+M4 | 0.789977 | 0.935 | 0.330 | 0.605 | 0.360 | 0.705 |
| M2+M3+M4 | 0.789362 | 0.990 | 0.335 | 0.655 | 0.315 | 0.695 |
| M1+M2+M3+M4 | 0.789362 | 1.160 | 0.335 | 0.825 | 0.240 | 0.600 |
| CANONICAL_ORACLE | 0.798584 | 1.160 | 0.225 | 0.935 | 0.240 | 0.600 |

All 85 policy-by-budget aggregate rows (B=0–4) are retained in `final_summary.json`; all policies, including Canonical Oracle, remain visible. Cost is atomic edge-edit count, not staff time or money.

## M4 secondary

At B=2, M4−Full Greedy mean loss difference was `0.001230` (positive means M4 higher loss), two-source 95% interval `0.000000 to 0.003916`. M4 and Full Greedy selected the same action on 99.0% of G0s, while their repaired graphs matched on 34.5%. The M4 mean edit count was 0.335 vs 1.160, a 71.1% reduction; paired difference M4−Full Greedy `-0.825` (95% interval `-0.925 to -0.730`). M4 had the same loss as Full Greedy on 198/200 G0s and higher loss on 2/200; no case was better.

## Actions, target and graph-free baseline

| Action | Evaluator mean | Standard error | Mean minus target | Bias-corrected loss |
|---:|---:|---:|---:|---:|
| `0.000155911358968` | 14.0688 | 0.0309 | -1.3912 | 0.789362 |
| `0.0001724093665238` | 14.0112 | 0.0322 | -1.4488 | 0.856078 |
| `0.00018679686613765` | 13.9644 | 0.0318 | -1.4956 | 0.912318 |
| `0.00020263502221978` | 14.0040 | 0.0316 | -1.4560 | 0.864628 |
| `0.00022589388613683002` | 13.9980 | 0.0318 | -1.4620 | 0.871766 |

All five sample means were below the fixed training-only target. The graph-free observational association baseline selected the first action and had loss `0.789362`, equal to that action's common evaluator loss. This baseline is not an intervention-effect learner. The fact that all five means are below target in this finite sample does not prove target infeasibility in the population.

## Structure and decisions

There were 48/200 initial error-free graphs, 64/200 with task-zone reference-relative errors, and 136/200 without task-zone errors. For Full Greedy, error counts decreased in 152 G0s; in 96 of those, the action stayed the same. In 56, structure repair changed the action; no cases with reduced counted errors worsened loss relative to S0, and 96 were tied. Structural accuracy and action/loss are related but not interchangeable; the same outcome table assigns loss to all policies that choose the same action.

In the prespecified task-zone-error stratum (64 G0s), mean B=2 S0 loss was 0.896315, while Full Greedy was 0.789362. In the no-task-zone-error stratum (136), both means were 0.789362. This is a descriptive subgroup comparison under the same single DGP; it does not replace the primary contrast.

M4 repairs were entirely task-zone edits on average at B=2; Full Greedy averaged 0.335 task-zone and 0.825 off-task edits/G0. For both policies the recorded opportunity set and all no-op/unused-budget cases remain in the original denominator.
