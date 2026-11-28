# Research D final contract review and closeout

## Final contract as executed

The approved contract was locked in `final_contract.json`: causalAssembly 1.2.1, upstream `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`, Station1 graph hash `92902ee9d83ba9bae677e9126050d7b647b64e980f78a0bc02948141b7bf72ca`, fixed Development training frame (512 rows), action `Station1_mp_0`, target `Station1_mp_4`, five approved actions, training-only target `15.460000542160238`, scale `1.565469292160237`, 200 new G0 IDs (`703001–703200`), 17 policies × five budgets, 2,500 independent hard-do draws per action and 10,000 chunked bootstrap replicates. No final-training observations were added.

## Review conclusion

The final experiment completed and passed the independent integrity audit. Primary B=2 S0−Full Greedy was +0.034225; its two-source 95% interval was +0.006173 to +0.065351. The action-MC and combined precision half-width goals were missed. M4 was only slightly worse in loss than Full Greedy but used 71.1% fewer edits and recommended the same action 99% of the time. These conclusions are conditional on the fitted DGP, training frame, benchmark DAG and virtual intervention semantics.

## Claims approved for reporting

1. The locked external semisynthetic final evaluation completed without response generation shortfall or integrity failure.
2. Within the fixed generator and training frame, the mean B=2 S0−Full Greedy target-tracking loss contrast was positive, with the reported bootstrap intervals and precision shortfall.
3. M4 and Full Greedy nearly always agreed on the action at lower M4 edit count; this is a conditional efficiency pattern, not universal equivalence.
4. The external DGP did not establish physical manufacturing effects, complete causal truth, independently sampled external SCMs, or deployment benefit.

Claims about real-world intervention effectiveness, absolute manufacturing regret, operating cost/safety, target attainability, or generalization to a manufacturing population are outside this contract.

## Final evaluation readiness decision

**Gate: `EXTERNAL_FINAL_EVALUATION_VERIFIED`.** The Research D final external semisynthetic evaluation is complete; no further external datasets or final samples are authorized or needed for this closeout. The remaining work is publication and team synthesis, with Research C preserved as the completed primary study and the physical external validation track explicitly deferred.
