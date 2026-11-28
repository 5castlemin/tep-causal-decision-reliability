# Research F-Lite final results (post-hoc)

## Evidence grade

`POST_HOC_REFERENCE_BLIND_QUERY_POLICY_EVALUATION`. Existing Research C Development and Held-out SCMs were reused. No new SCMs or observations were drawn. The C Held-out cohort had already informed prior research and was not untouched when F-Lite was designed.

## Main result

At B=4, decision-weighted verification reduces mean regret from S0 by 0.098292 in Development (0.100852 to 0.002560) and 0.077158 in Held-out (0.093439 to 0.016281). It also outperforms random verification on Held-out (paired comparator-minus-proposed +0.064942; 95% SCM bootstrap interval [0.045436, 0.086207]). But it is worse than fit-based verification (difference −0.012511, interval [−0.023669, −0.003856]) and suspicion-only (−0.010220, [−0.019854, −0.002602]). It is nearly tied with impact-only (difference +0.000988; interval [0, 0.002881]; 198/200 SCM ties).

The proposed score's incremental benefit is therefore unsupported. Simple observational fit or suspicion heuristics performed better on this reused Held-out cohort. This does not prove that they will dominate in new SCM populations.

## Effort and benchmarks

The proposed policy made four queries by contract but averaged 0.45 graph edits on Held-out. It left 1.72 mean structural errors and changed the recommended action on 20% of SCMs. Oracle-assisted M4 had 0.001435 mean regret with 0.780 edits; it uses the reference DAG and is not a blind comparator. Graph-free association had 0.038725 regret without graph repair. Neither benchmark is universally dominated across all objectives.

## Simulated expert noise

At 0.9 and 0.8 hypothetical response accuracy, Held-out mean regrets were respectively: Random .092546/.095624, Suspicion-only .021620/.039240, Impact-only .039614/.065565, and Decision-weighted .038087/.060056. Decision-weighted beat Random, but was worse than Suspicion-only at both accuracies (nested paired 95% intervals for suspicion minus proposed: [−.027095, −.007539] and [−.031251, −.011203]). It remained close to Impact-only, particularly at .9. This does not estimate human-expert reliability.

## Expert-noise sensitivity

The core run uses a perfect simulated expert. The optional 0.9/0.8 accuracy sensitivity is a deterministic hypothetical response model with 16 repetitions per SCM/accuracy and B=4. Its repeated trajectories are not new SCMs or real expert observations. See `RESEARCH_F_EXPERT_NOISE_SENSITIVITY.md` and the recovery log for exact completion and caveats.

## Conclusion

F-Lite demonstrates that a small reference-blind query interface can be evaluated against downstream decision loss using existing SCM inputs. It does not show the combined heuristic is best, and it does not validate expert-guided repair in a factory or in a new causal population.
