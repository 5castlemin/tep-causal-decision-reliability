# Draft inquiry to Causal Chamber data/device maintainers

**Not sent.** This draft asks only for evidence that could resolve the remaining Mk2 provenance and alignment blockers.

Subject: Clarification of provenance and timing metadata for `lt_spice_v1` Mk2 archive

Hello,

I am assessing whether the public Light Tunnel Mk2 `lt_spice_v1` archive can support a bounded, outcome-blind external validation study. I have not begun a policy evaluation. Could you clarify, or point me to public records for, the following items?

1. Does the Figure 1 graph apply only to the documented linked-LED configuration, and are any omitted direct effects or latent common causes known? Is the graph intended as a complete DAG, or only a set of known/expected effects?
2. For `exp_1_low_noise` and `exp_2_noisy`, are there physical device identifiers, experiment/session IDs, dates, or configuration records that establish whether these were separate runs or independent devices? Were the 20 blocks within each generated experiment reset, recalibrated, or otherwise separated?
3. In the SDK/protocol semantics, at what event does each `SET` take effect relative to `MSR` acquisition? Does each CSV row represent a measurement after the immediately preceding `SET`, and what does the `intervention` field mark in the archived files?
4. For the linked controller, what is the acquisition/update order among `ir_1`, controller computation, LED actuation, and `current_led_2_uv` measurement? Is there a row-level actuation or acquisition timestamp available?
5. What settling/wait protocol was used, and is there evidence that the 8-second waits or 1-second inter-block waits are sufficient for equilibrium? Were any resets or settling periods omitted from the public generator/archive?

Even partial documentation or a pointer to firmware/protocol logs would help. We will treat undocumented items as unresolved and will not infer them from response trends.

Thank you,

Research D feasibility audit
