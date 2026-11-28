# Research C and Research D scientific synthesis

## What Research C showed

Research C's held-out primary compared S0 with Full Greedy at B=2 over 200 independently generated synthetic SCMs. Its paired regret delta was +0.07483636 (95% paired-t interval 0.05089822 to 0.09877450); positive favored Full Greedy. It used the frozen signed-linear SCM contract, analytic GT SCM loss and absolute decision regret. M4 remained a Development-selected secondary policy.

## What Research D adds

The final external semisynthetic robustness evaluation used one DRF-based generator refit to the pinned causalAssembly public semisynthetic sample, Station1's 6-node/7-edge benchmark reference and the exact fixed 512-row Development learner frame. At B=2 its S0−Full Greedy bias-corrected target-tracking-loss contrast was +0.03422490 (95% G0-only 0.02664478–0.04180501; action-MC-only 0.00650999–0.06284998; two-source 0.00617347–0.06535080). The action-MC and combined half-width targets were not met. M4 was within 0.00122956 loss units above Full Greedy on average, two-source interval 0.00000000–0.00391596, with 99% action agreement and 71.1% fewer edits.

## Interpretation

The positive direction appears in both studies, but the numerical effects cannot be compared as estimates of one effect. Research C sampled independent SCMs, measured regret using its analytic GT SCM evaluator and used a different graph population/topology and loss contract. Research D varies graph corruption under one fixed external fitted generator and one training frame, evaluates finite Monte Carlo target-tracking loss, and uses a benchmark-relative reference. D therefore supplies conditional robustness evidence outside the internally designed signed-linear mechanism, not a replication of C's independent-SCM held-out estimate.

The result does not validate a complete physical graph, real interventions, actual controls, process cost, safety or deployment in DAT manufacturing. The action outcomes all fell below target in the finite evaluator sample; this is not population-level target infeasibility. A graph-free observational association rule selected the same lowest-loss action as the first action value, showing that graph repair is not guaranteed to beat direct action association in this setup. The intended broad claim remains limited: under one external DRF-based semisynthetic environment and fixed learner frame, Full Greedy outperformed S0 on the prespecified B=2 contrast, while M4 reached nearly the same decisions at lower edit count.

Neither result says the primary theory must hold in every environment. Adverse or null results elsewhere would be valid evidence. Research D's final status should be archived as conditional external semisynthetic robustness, with the physical validation track deferred.

## Research C mechanism analysis provenance correction

The M1–M4 post-hoc analysis originally entered PR #40 using regenerated ledgers because the author could not access the original SQLite files. A later read-only audit of the original Development and Held-out ledgers confirmed the published policy-by-budget aggregates and the stored action-disagreement cases at their reported precision. The regenerated SCM-keyed raw result database was not retained, so a full key-by-key comparison is unavailable. The analysis remains post-hoc and exploratory. The audit also corrected the case interpretation: five of the six M4-winning Held-out B=2 action disagreements restored a missing X→Y path; case `…000139` already had a path and differed in chosen action direction. See `research/final_integration/ORIGINAL_LEDGER_MECHANISM_AUDIT.md` for source hashes and scope.
