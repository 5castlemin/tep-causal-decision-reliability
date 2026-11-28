# Research D–S5 Integrated Synthesis

Historical Research D and S5 are distinct evaluations. Research D's earlier final run used its own fixed training frame, action grid, target, and response vectors. Those private raw vectors were not available to this continuation, and this report does not combine the two sets of point estimates or intervals.

S5 is a new conditional external semisynthetic reconstruction: causalAssembly 1.2.1, pinned source commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`, official Station1 reference (6 nodes, 7 edges), one DRF DGP fit, one 512-row training frame, and 200 graph-corruption draws. At B=2 the primary mean `loss(No-repair) − loss(M4)` was +0.00685. The G0-only interval was above zero, while action-MC-only and two-source intervals crossed zero. T5 and M4 made the same first edit in every draw, and only five draws had at least two initial legal M4 candidates.

This provides limited evidence that the repair comparison can be evaluated in an external semisynthetic generator, while showing that candidate scarcity and Monte Carlo uncertainty constrain inference. It is not 200 independent SCMs, an exact reproduction of Research D, a new manufacturing line, or physical intervention validation. Graph-free association matched or slightly outperformed repair policies on the observed average loss while incurring zero edge edits; this cost measure omits model fitting and validation.

For Study 3, preserve Research D as the historical conditional semisynthetic evaluation and S5 as a separately seeded reconstruction. Their outcomes should be narrated side-by-side with their differing contracts, not pooled.
