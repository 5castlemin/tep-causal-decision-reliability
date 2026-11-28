# Research S7 — Environment and Task Selection

| Station task stratum | Nodes / within-station edges | Strict-indirect task pairs | Locked action → target | Station-local path | Full-graph backdoor support |
|---|---:|---:|---|---:|---|
| Station2 | 34 / 77 | 57 | `Station2_mp_13 → Station2_mp_33` | 2 edges | None detected under locked directed-backdoor check |
| Station3 | 16 / 11 | 6 | `Station3_mp_43 → Station3_mp_45` | 2 edges | None detected under locked directed-backdoor check |

The eligibility computation uses the official Station subgraph for task locality and the complete 98-node/485-edge DAG to determine the intervention-generating model and backdoor support. The station-local pair selection rule and selected tasks are fixed in the contract. No task was selected by policy loss, G0 result, or action response.

Both task strata share the same fitted full-line DGP and 512-row training frame. Their 200 G0 draws each are paired task-specific corruption draws conditional on that one fitted DGP; they are not independent SCMs and cannot support environment-population inference. The use of two station tasks extends task-location coverage within the same official semisynthetic benchmark, with the dependence stated explicitly.
