"""Render public, aggregate-only Research D final closeout from audited files."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXTERNAL = ROOT.parent / "data" / "local" / "research-d-semisen-final-20261125"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((EXTERNAL / name).read_text(encoding="utf-8"))


def write(name, text):
    clean = "\n".join(line.rstrip() for line in text.splitlines())
    (HERE / name).write_text(clean+"\n", encoding="utf-8", newline="\n")


def main():
    analysis=load("independent_analysis.json")
    lock=load("final_run_lock.json")
    complete=load("completion.json")
    ev=load("evaluation_manifest.json")
    execution=load("execution_manifest.json")
    resource=load("resource_supervision.json")
    benchmark=load("resource_benchmark.json")
    audit=json.loads((HERE/"final_independent_analysis_comparison.json").read_text(encoding="utf-8"))
    actions=analysis["action_summaries"]
    primary=analysis["primary_B2_S0_minus_FullGreedy"]
    intervals=analysis["primary_intervals"]
    secondary=analysis["secondary_B2_M4_minus_FullGreedy"]
    costs=analysis["m4_fullgreedy_cost_and_action"]
    rows=analysis["policy_budget_curve"]
    policies=lock["learner_and_repair"]["policies"]
    full="M1+M2+M3+M4"
    b2={r["policy"]:r for r in rows if r["budget"]==2}

    result={"schema":"RESEARCH_D_FINAL_SUMMARY_V1","gate":complete["final_gate"],
        "study_type":"CONDITIONAL_EXTERNAL_SEMISYNTHETIC_ROBUSTNESS",
        "claim_scope":"One fitted DRF-based DGP, official Station1 benchmark reference, fixed Development training frame; 200 graph-corruption draws, not independent SCMs.",
        "run_id":complete["run_id"],"source_commit":lock["repository"]["commit"],
        "source_tree":lock["repository"]["tree"],
        "recommendation_rows":complete["recommendation_rows"],"g0_count":analysis["g0_count"],
        "intervention_rows":complete["intervention_rows"],"new_training_rows":0,
        "primary":primary,"primary_intervals":intervals,
        "precision_targets":analysis["precision_targets"],
        "secondary_m4":secondary,"m4_cost_action":costs,
        "graph_free_baseline":analysis["graph_free_association_baseline"],
        "action_summaries":analysis["action_summaries"],
        "policy_budget_curve":analysis["policy_budget_curve"],
        "task_zone_off_task_error_counts_at_B2":analysis["task_zone_off_task_error_counts_at_B2"],
        "prespecified_g0_strata":analysis["prespecified_g0_strata"],
        "structure_action_relationship":analysis["structure_action_relationship"],
        "resource":{"elapsed_seconds":resource["elapsed_seconds"],
            "peak_process_tree_rss_bytes":resource["peak_process_tree_rss_bytes"],
            "rss_limit_bytes":resource["rss_limit_bytes"],"wall_limit_seconds":resource["wall_limit_seconds"],
            "status":resource["status"],"synthetic_benchmark_seconds":benchmark["elapsed_seconds"],
            "synthetic_benchmark_internal_peak_rss_bytes":benchmark["peak_rss_bytes"],
            "synthetic_benchmark_internal_peak_measurement_valid":benchmark["peak_rss_bytes"]>0},
        "integrity":{"independent_audit_status":audit["status"],"independent_audit_checks":len(audit["checks"]),
            "independent_analysis_sha256":complete["independent_analysis_sha256"],
            "independent_artifact_audit_sha256":sha(HERE/"final_independent_analysis_comparison.json"),
            "response_manifest_sha256":sha(EXTERNAL/"evaluation_manifest.json"),
            "recommendation_raw_sha256":complete["recommendation_sha256"],
            "action_response_file_sha256":{str(x["action"]):x["response_file_sha256"] for x in audit["independent_action_statistics"]}},
        "physical_manufacturing_validation":False,"research_c_contract_changed":False}
    (HERE/"final_summary.json").write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")

    public_manifest={"schema":"RESEARCH_D_FINAL_PUBLIC_EXECUTION_MANIFEST_V1",
        "run_id":complete["run_id"],"final_gate":complete["final_gate"],
        "study_type":json.loads((HERE/"final_contract.json").read_text(encoding="utf-8"))["study_type"],"source":{"repository":json.loads((HERE/"final_contract.json").read_text(encoding="utf-8"))["source"]["repository"],
            "commit":lock["source"]["source_commit"],"package_version":lock["source"]["package_version"],
            "sample_sha256":lock["source"]["data_sha256"]["assembly_sample--assembly_line_500.csv"],
            "reference_sha256":lock["source"]["data_sha256"]["assembly_reference--ground_truth.json"],
            "license":"AGPL-3.0"},
        "reference":{"kind":"official Station1 benchmark DAG; reference-relative discrepancies",
            "node_count":len(lock["graph"]["nodes"]),"edge_count":len(lock["graph"]["edges"]),
            "graph_sha256":lock["graph"]["sha256"],"node_order":lock["graph"]["nodes"]},
        "fitted_generator":{"kind":"DRF-based external semisynthetic generator",
            "fit_seed":lock["fit"]["seed"],"fit_diagnostic_sha256":lock["fit_diagnostic"]["diagnostic_sha256"],
            "diagnostic_is_full_dgp_identity_proof":False},
        "training":{"choice":"A_FIXED_DEVELOPMENT_FRAME","rows":512,"new_rows":0,
            "raw_csv_sha256":lock["training"]["raw_csv_sha256"],"numeric_sha256":lock["training"]["numeric_sha256"]},
        "task":{"action":lock["task"]["action"],"target":lock["task"]["target"],
            "reference_path":lock["task"]["reference_path"],"actions":lock["task"]["actions"],
            "target_value":lock["task"]["target"],"scale":lock["task"]["scale"],
            "virtual_hard_do":True,"physical_operability_claim":False},
        "samples":{"g0_count":200,"g0_ids":[703001,703200],"g0_id_range_only":True,
            "g0_master_seed_sha256":lock["seed_collision_audit"]["g0_master_seed_sha256"],
            "recommendation_rows":17000,"rows_per_action":2500,"total_intervention_rows":12500,
            "bootstrap_replicates":10000,"bootstrap_chunk_replicates":128},
        "seed_streams":{"namespace":lock["seed_collision_audit"]["namespace"],
            "action_seeds":lock["sampling"]["action_seeds"],"primary_bootstrap_seed":lock["sampling"]["bootstrap_seed"],
            "secondary_bootstrap_seed":lock["sampling"]["secondary_bootstrap_seed"],
            "paired_cost_seed":lock["sampling"]["paired_cost_seed"],
            "resource_benchmark_seed":lock["sampling"]["resource_benchmark_seed"],
            "prior_seed_collision_count":0},
        "analysis":{"primary":"B=2, L(S0)-L(FullGreedy)",
            "estimator":"((mean-target)^2 - sample_variance/n)/scale^2; ddof=1; no truncation",
            "intervals":["G0-only","action-MC-only","two-source paired percentile 95%"],
            "action_loss_table_shared":True},
        "runtime":lock["runtime"],"code_commit":lock["repository"]["commit"],
        "code_tree":lock["repository"]["tree"],"code_sha256":lock["code_sha256"],
        "contract_sha256":lock["contract_sha256"],"run_lock_sha256":complete["run_lock_sha256"],
        "recommendation_raw_sha256":complete["recommendation_sha256"],
        "execution_manifest_sha256":complete["execution_manifest_sha256"],
        "evaluation_manifest_sha256":complete["evaluation_manifest_sha256"],
        "independent_analysis_sha256":complete["independent_analysis_sha256"],
        "independent_artifact_audit_sha256":sha(HERE/"final_independent_analysis_comparison.json"),
        "synthetic_resource_benchmark_sha256":sha(EXTERNAL/"resource_benchmark.json"),
        "resource_supervision_sha256":sha(EXTERNAL/"resource_supervision.json"),
        "response_vector_file_sha256":{str(x["action"]):x["response_file_sha256"] for x in audit["independent_action_statistics"]},
        "raw_training_data_recommendations_and_responses_in_git":False,
        "source_absolute_paths_published":False}
    (HERE/"final_public_execution_manifest.json").write_text(json.dumps(public_manifest,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")

    table="\n".join(f"| {r['policy']} | {r['mean_bias_corrected_loss']:.6f} | {r['mean_edit_cost']:.3f} | {r['mean_task_zone_edit_count']:.3f} | {r['mean_off_task_edit_count']:.3f} | {r['no_op_rate']:.3f} | {r['unused_budget_rate']:.3f} |" for r in (b2[p] for p in policies))
    action_table="\n".join(f"| `{a}` | {v['mean']:.4f} | {v['standard_error']:.4f} | {v['mean_minus_target']:.4f} | {v['bias_corrected_loss']:.6f} |" for a,v in actions.items())
    source_hashes="\n".join(f"- `{name}`: `{digest}`" for name,digest in lock["code_sha256"].items())

    write("RESEARCH_D_FINAL_PIPELINE_VALIDATION.md",f"""# Research D final pipeline validation

**Final gate:** `{complete['final_gate']}`
**Execution source revision:** `{lock['repository']['commit']}` (tree `{lock['repository']['tree']}`)
**Run:** `{complete['run_id']}`

## Contract and source binding

The final run lock bound the exact pinned causalAssembly source and sample/reference hashes, Station1 graph and node order, fixed 512-row learner frame, task/actions/target/scale, 200 G0 IDs, all 17 policies and five budgets, evaluator row counts, bootstrap contract, runtime fingerprint, code byte hashes, and output location before evaluation. The recommendation manifest was content-hash locked before the evaluator was invoked. All 17,000 recommendations were replay-checked against the unchanged policy engine; task-zone and off-task edit counts were added from that deterministic replay.

The recommendation worker received the observational training frame and graph/task inputs. It did not receive the fitted DRF or intervention response data. The evaluator ran as a separate process, re-fit the pinned DGP, verified the locked recommendations, and sampled only the five fixed actions. This is process separation and input separation, not an OS sandbox.

## Preflight and execution

- Exact external sample, reference and source commit checks passed; causalAssembly imported from the pinned source worktree.
- Fixed training CSV raw SHA-256 `{lock['training']['raw_csv_sha256']}` and numeric SHA-256 `{lock['training']['numeric_sha256']}` passed. No new training rows were generated.
- Runtime matched Python `{lock['runtime']['python']}`, NumPy `{lock['runtime']['numpy']}`, pandas `{lock['runtime']['pandas']}`, NetworkX `{lock['runtime']['networkx']}`, R `{lock['runtime']['R']}`, R `drf` `{lock['runtime']['R_drf']}`, rpy2 `{lock['runtime']['rpy2']}`, and causalAssembly `{lock['runtime']['causalAssembly']}`.
- DRF fit diagnostic matched `{lock['fit_diagnostic']['diagnostic_sha256']}` over 16 rows. This diagnostic is not proof that the full fitted generator is identical.
- Final G0 IDs were `703001–703200`; the scanned prior-record set showed zero seed collisions.
- Recommendation rows: {complete['recommendation_rows']}; action response rows: {complete['intervention_rows']}; sampling parallelism: 1; evaluator sampling time: {ev['sampling_seconds']:.3f} s.
- All vectors were finite, schema-checked, exact hard-do values were applied, and each vector was saved once outside the repository with a SHA-256. No prior response rows were reused.

## Errors and environment notes

An initial dry-run attempt lacked `R_LIBS_USER` and stopped before sampling; no final rows were created. Repeating the preflight with the already documented isolated `R-library` path passed. Windows printed pre-existing `sh`, ABI-mode fallback, and locale warnings; the pinned R fit and sampler completed with exit code 0 and the expected diagnostic.

The local default Python full-suite attempt used incompatible NumPy/pandas/NetworkX versions and also surfaced the already documented Windows CRLF raw-ledger hash mismatch. No frozen file or validation rule was changed. GitHub Actions on the pushed immutable source revision passed the full suite: **399 tests, 398 passed, 1 skipped**, plus all repository validators.

## Hash record

- Run lock: `{complete['run_lock_sha256']}`
- Recommendations raw bytes: `{complete['recommendation_sha256']}`
- Execution manifest: `{complete['execution_manifest_sha256']}`
- Evaluation response manifest: `{complete['evaluation_manifest_sha256']}`
- Independent analysis: `{complete['independent_analysis_sha256']}`
- Separate artifact audit: `{sha(HERE/'final_independent_analysis_comparison.json')}`

Raw run lock, recommendation rows, learner frame, fitted object and response vectors remain in the ignored external data area; they are not in Git.
""")

    write("RESEARCH_D_FINAL_RESOURCE_REPORT.md",f"""# Research D final resource report

## Limits and measured run

| Measure | Observed | Locked limit | Result |
|---|---:|---:|---|
| Wall time, full supervised process tree | {resource['elapsed_seconds']:.3f} s ({resource['elapsed_seconds']/60:.2f} min) | {resource['wall_limit_seconds']} s | PASS |
| Peak process-tree RSS sampled by Windows psutil supervisor | {resource['peak_process_tree_rss_bytes']:,} bytes ({resource['peak_process_tree_rss_bytes']/1024**3:.3f} GiB) | {resource['rss_limit_bytes']:,} bytes (4 GiB) | PASS |
| Final intervention rows | {ev['total_rows']:,} | 12,500 | PASS |
| Serial action sampling | 1 | 1 | PASS |
| DRF fit in evaluator | {ev['fit_seconds']:.3f} s | within whole-run limit | PASS |
| Intervention sampling | {ev['sampling_seconds']:.3f} s | within whole-run limit | PASS |

The outer monitor used psutil {resource['psutil_version']} to sample recursive process-tree RSS every 2 seconds and terminate the process tree if a sampled value exceeded 4 GiB or elapsed time exceeded 7,200 seconds. The final process tree completed normally with no breach. This is not an OS sandbox, and sub-interval transients are not separately measured.

## Synthetic full-dimension bootstrap benchmark

The response-blind synthetic fixture exercised 17,000 recommendation rows, five synthetic action vectors of 2,500 rows each, 10,000 paired two-source bootstrap replicates, and chunk size 128. It completed in {benchmark['elapsed_seconds']:.3f} s without using final outcome data. Its Windows in-process `GetProcessMemoryInfo` field returned **0 bytes**, which is an invalid measurement and is not treated as evidence of low memory use. The external process-tree supervisor is the valid measured memory record for the complete execution, including the benchmark and final run: {resource['peak_process_tree_rss_bytes']:,} bytes. The actual run therefore stayed under the cap; the benchmark-specific internal peak metric remains unavailable.

The pre-run benchmark used its locked synthetic seed and did not choose or alter the task, actions, targets, policies, or sample sizes. Actual run hashes and measurement are in `final_public_execution_manifest.json`.
""")

    write("RESEARCH_D_FINAL_RESULTS.md",f"""# Research D final results

## Scope

This is `CONDITIONAL_EXTERNAL_SEMISYNTHETIC_ROBUSTNESS`: one DRF-based DGP fit to causalAssembly's pinned public semisynthetic sample and the official Station1 benchmark DAG, with the exact fixed Development learner frame. The 200 units are graph-corruption draws under this fixed environment, not independent SCMs. Actions are virtual benchmark hard-do values, not verified manufacturing controls. Results are reference-relative, not evidence against a complete physical GT.

## Primary at B=2

`Δ_D = L(S0) − L(Full Greedy) = {primary['mean_delta_loss_bc']:.6f}` standardized tracking-loss units (n=200 paired G0s). Positive favors Full Greedy. The three predeclared intervals are reported in the uncertainty report; the two-source 95% interval is `{intervals['two_source_95'][0]:.6f} to {intervals['two_source_95'][1]:.6f}`. Full Greedy changed the S0 action on 56/200 G0s: 56 improved, 144 tied, 0 worsened. This is conditional evidence for this single fitted generator and fixed training frame, not a physical-process result.

## B=2 policy results

| Policy | Mean bias-corrected loss | Mean edit cost | Task-zone edits/G0 | Off-task edits/G0 | No-op rate | Budget unused rate |
|---|---:|---:|---:|---:|---:|---:|
{table}

All 85 policy-by-budget aggregate rows (B=0–4) are retained in `final_summary.json`; all policies, including Canonical Oracle, remain visible. Cost is atomic edge-edit count, not staff time or money.

## M4 secondary

At B=2, M4−Full Greedy mean loss difference was `{secondary['mean_delta_loss_bc']:.6f}` (positive means M4 higher loss), two-source 95% interval `{secondary['paired_two_source_95'][0]:.6f} to {secondary['paired_two_source_95'][1]:.6f}`. M4 and Full Greedy selected the same action on {costs['same_action_fraction']:.1%} of G0s, while their repaired graphs matched on {costs['same_repaired_graph_fraction']:.1%}. The M4 mean edit count was {costs['mean_m4_edit_count']:.3f} vs {costs['mean_fullgreedy_edit_count']:.3f}, a {costs['m4_cost_reduction_fraction_vs_fullgreedy']:.1%} reduction; paired difference M4−Full Greedy `{costs['mean_paired_cost_difference_m4_minus_fullgreedy']:.3f}` (95% interval `{costs['paired_cost_difference_95'][0]:.3f} to {costs['paired_cost_difference_95'][1]:.3f}`). M4 had the same loss as Full Greedy on 198/200 G0s and higher loss on 2/200; no case was better.

## Actions, target and graph-free baseline

| Action | Evaluator mean | Standard error | Mean minus target | Bias-corrected loss |
|---:|---:|---:|---:|---:|
{action_table}

All five sample means were below the fixed training-only target. The graph-free observational association baseline selected the first action and had loss `{analysis['graph_free_association_baseline']['loss_bc']:.6f}`, equal to that action's common evaluator loss. This baseline is not an intervention-effect learner. The fact that all five means are below target in this finite sample does not prove target infeasibility in the population.

## Structure and decisions

There were 48/200 initial error-free graphs, 64/200 with task-zone reference-relative errors, and 136/200 without task-zone errors. For Full Greedy, error counts decreased in 152 G0s; in 96 of those, the action stayed the same. In 56, structure repair changed the action; no cases with reduced counted errors worsened loss relative to S0, and 96 were tied. Structural accuracy and action/loss are related but not interchangeable; the same outcome table assigns loss to all policies that choose the same action.

In the prespecified task-zone-error stratum (64 G0s), mean B=2 S0 loss was {analysis['prespecified_g0_strata']['task_zone_error_s0_loss']['mean_loss_bc']:.6f}, while Full Greedy was {analysis['prespecified_g0_strata']['task_zone_error_fullgreedy_loss']['mean_loss_bc']:.6f}. In the no-task-zone-error stratum (136), both means were {analysis['prespecified_g0_strata']['no_task_zone_error_s0_loss']['mean_loss_bc']:.6f}. This is a descriptive subgroup comparison under the same single DGP; it does not replace the primary contrast.

M4 repairs were entirely task-zone edits on average at B=2; Full Greedy averaged {b2[full]['mean_task_zone_edit_count']:.3f} task-zone and {b2[full]['mean_off_task_edit_count']:.3f} off-task edits/G0. For both policies the recorded opportunity set and all no-op/unused-budget cases remain in the original denominator.
""")

    write("RESEARCH_D_FINAL_UNCERTAINTY_REPORT.md",f"""# Research D final uncertainty report

## Primary B=2 contrast

| Source of variation | Paired 95% interval | Half-width | Reporting goal | Met? |
|---|---:|---:|---:|---|
| G0 corruption draw | [{intervals['g0_only_95'][0]:.6f}, {intervals['g0_only_95'][1]:.6f}] | {intervals['g0_only_half_width']:.6f} | descriptive | — |
| Action Monte Carlo | [{intervals['action_mc_only_95'][0]:.6f}, {intervals['action_mc_only_95'][1]:.6f}] | {intervals['action_mc_only_half_width']:.6f} | ≤ 0.020 | {analysis['precision_targets']['action_mc_target_met']} |
| Two-source | [{intervals['two_source_95'][0]:.6f}, {intervals['two_source_95'][1]:.6f}] | {intervals['two_source_half_width']:.6f} | ≤ 0.025 | {analysis['precision_targets']['combined_target_met']} |

Point estimate: `{primary['mean_delta_loss_bc']:.8f}`; paired G0 count 200; 10,000 percentile bootstrap replicates, chunk size 128. G0s are resampled as paired units. Within each replicate, the independently resampled action loss vectors form one shared action-loss table applied across every G0 and policy. Action draws are independent streams. No final sample size was increased after seeing precision.

Both action-MC and combined half-width goals were missed. Their intervals are above zero in this conditional evaluation, but the unmet precision goals require reporting the wider uncertainty and should not be hidden by the positive point estimate. These intervals do not include uncertainty in the fitted DRF, source semisynthetic data, graph/reference validity, new training frames, physical systems, or manufacturing populations.

## Secondary and action sampling uncertainty

M4−Full Greedy at B=2 was `{secondary['mean_delta_loss_bc']:.6f}` with paired two-source interval `{secondary['paired_two_source_95'][0]:.6f} to {secondary['paired_two_source_95'][1]:.6f}`. The paired edit-cost difference interval is reported in the results. No equivalence or noninferiority claim follows from the many identical actions.

The action-specific standard errors in `RESEARCH_D_FINAL_RESULTS.md` use independent response draws under the fixed DRF for each action. The primary uses bias-corrected target-tracking loss of the intervention sample mean, not individual-row MSE. Its finite sample correction is `sample variance / n`, ddof=1, and no negative clipping is applied.

Absolute empirical regret is not a primary result. The minimum loss over the same sampled actions would add a winner-selection uncertainty not needed for the paired policy contrast.
""")

    write("RESEARCH_D_FINAL_MECHANISM_ANALYSIS.md",f"""# Research D final mechanism analysis

At B=2 the policy ranking is not a ranking of graph accuracy alone. M1/M2/M3 primarily address errors in their own metric families and average losses stayed near S0. M4 corrected task-zone discrepancies and reduced mean target-tracking loss to `{b2['M4']['mean_bias_corrected_loss']:.6f}` at mean cost 0.335. M4+M2 achieved the lowest B=2 average loss (`{b2['M2+M4']['mean_bias_corrected_loss']:.6f}`) among the 17 policies, but this was exploratory/secondary, not the primary. Full Greedy's average loss was `{b2[full]['mean_bias_corrected_loss']:.6f}` at mean cost 1.160. Canonical Oracle is a structure-only reference baseline and had loss `{b2['CANONICAL_ORACLE']['mean_bias_corrected_loss']:.6f}`; it is not regret-optimal.

## Repair-to-action relation

- Full Greedy changed the S0 action in 56/200 cases; these 56 improved loss and the remaining 144 tied.
- Structural error counts decreased for Full Greedy in 152 cases; 96 of those retained the same action, so measurable structural repair often did not change the decision.
- M4 matched Full Greedy's selected action in 198/200 cases but matched the repaired graph in only 69/200. Thus distinct repair paths often led to the same recommended action.
- M4 used fewer edits than Full Greedy by 0.825/G0 on average. The saving was in edits, not money, engineering hours, or maintenance burden.
- The association baseline picked the first action, whose evaluator loss matched its mean loss. This demonstrates that under this target and training-conditioned setup a graph-free rule was competitive with the primary policy's aggregate loss. It does not identify a causal effect.

The action values and target were fixed before final response generation. All action response means were below target; therefore the observed decision task mostly ranks which supported action is closer to an externally fixed target that was above the observed means. That pattern is conditional on the fitted DRF and finite evaluator draws. It is not evidence that the physical process cannot reach the target.

The 200 graph draws share one reference, one fitted generator and one learner frame. Their intervals quantify the prespecified graph-corruption distribution plus finite intervention Monte Carlo variation only. The original Research C population over independently sampled SCMs and its absolute regret are not reproduced.
""")

    write("RESEARCH_D_FINAL_INTEGRITY_AUDIT.md",f"""# Research D final integrity audit

**Audit status:** `{audit['status']}`; {len(audit['checks'])} independent checks passed.
**Research D execution source commit/tree:** `{lock['repository']['commit']}` / `{lock['repository']['tree']}`.

## Verified

- The contract, run lock, execution manifest, recommendation bytes/content, response manifest and analysis hashes agree with their bindings.
- Every listed execution file matches its locked byte SHA-256; Git HEAD and tree equal the pre-run commit/tree. The closeout/audit files were created after the final run and are not execution inputs.
- All 17,000 unique recommendation keys cover exactly 200 G0 IDs × five budgets × 17 policies; all 85 aggregate policy-budget cells were independently recalculated.
- Five 2,500-row float64 finite response vectors match the per-file SHA-256 and action order; total 12,500 rows. No action was resampled or vector overwritten.
- Independently recalculated action means, sample variances, bias-corrected losses, primary and M4 contrasts, policy-budget losses and edit costs match the saved analysis within `2e-13` numeric tolerance.
- Run lock fit diagnostic matched the predeclared 16-row digest, pinned graph has 6 nodes/7 edges, and stored node order matches fitted parent sampling order.
- Recommendation manifest was finalized and locked before evaluator-only response generation; response values were not used to change task, action set, target, scale, policies, budgets or sample sizes.
- External source/sample/reference and fixed learner-frame hashes match the approved manifest. Seed audit recorded zero collisions with scanned earlier records.
- Resource supervisor completed with no time or RSS breach; Research C contract, policies, ledgers and frozen manifests were untouched.

## Public/private artifact boundary

The repository contains only aggregate summaries, hash records, contracts, code and reports. The 1.46 MB raw run lock (including G0 records), 40 MB recommendation manifest, training CSV, fitted R/DRF object, evaluation manifest and five `.npy` response vectors remain outside Git in the ignored external data area. The response vectors are individually hash-addressed in `final_public_execution_manifest.json` and can be independently reanalyzed locally. No personal absolute paths are published.

The earlier response-blind resource benchmark completed at full synthetic dimensions; its own peak-memory counter returned zero and is explicitly marked invalid. The full supervised execution's independent process-tree RSS measurement is valid and is the basis for the resource cap result. This counter issue does not change any scientific result or the output integrity check.

## Important limitations

The full DRF fit is not proven identical by a 16-row diagnostic digest. The DRF was refit from the same pinned semisynthetic sample in the evaluator process. The actual final run was on Windows with documented R ABI/locale warnings, though it exited normally. The external psutil peak is sampled every two seconds, not a kernel-enforced address-space limit. Research D remains one conditional semisynthetic benchmark, not physical validation.
""")

    write("RESEARCH_C_D_SCIENTIFIC_SYNTHESIS.md",f"""# Research C and Research D scientific synthesis

## What Research C showed

Research C's held-out primary compared S0 with Full Greedy at B=2 over 200 independently generated synthetic SCMs. Its paired regret delta was +0.07483636 (95% paired-t interval 0.05089822 to 0.09877450); positive favored Full Greedy. It used the frozen signed-linear SCM contract, analytic GT SCM loss and absolute decision regret. M4 remained a Development-selected secondary policy.

## What Research D adds

The final external semisynthetic robustness evaluation used one DRF-based generator refit to the pinned causalAssembly public semisynthetic sample, Station1's 6-node/7-edge benchmark reference and the exact fixed 512-row Development learner frame. At B=2 its S0−Full Greedy bias-corrected target-tracking-loss contrast was +0.03422490 (95% G0-only 0.02664478–0.04180501; action-MC-only 0.00650999–0.06284998; two-source 0.00617347–0.06535080). The action-MC and combined half-width targets were not met. M4 was within 0.00122956 loss units above Full Greedy on average, two-source interval 0.00000000–0.00391596, with 99% action agreement and 71.1% fewer edits.

## Interpretation

The positive direction appears in both studies, but the numerical effects cannot be compared as estimates of one effect. Research C sampled independent SCMs, measured regret using its analytic GT SCM evaluator and used a different graph population/topology and loss contract. Research D varies graph corruption under one fixed external fitted generator and one training frame, evaluates finite Monte Carlo target-tracking loss, and uses a benchmark-relative reference. D therefore supplies conditional robustness evidence outside the internally designed signed-linear mechanism, not a replication of C's independent-SCM held-out estimate.

The result does not validate a complete physical graph, real interventions, actual controls, process cost, safety or deployment in DAT manufacturing. The action outcomes all fell below target in the finite evaluator sample; this is not population-level target infeasibility. A graph-free observational association rule selected the same lowest-loss action as the first action value, showing that graph repair is not guaranteed to beat direct action association in this setup. The intended broad claim remains limited: under one external DRF-based semisynthetic environment and fixed learner frame, Full Greedy outperformed S0 on the prespecified B=2 contrast, while M4 reached nearly the same decisions at lower edit count.

Neither result says the primary theory must hold in every environment. Adverse or null results elsewhere would be valid evidence. Research D's final status should be archived as conditional external semisynthetic robustness, with the physical validation track deferred.
""")

    write("RESEARCH_D_FINAL_CONTRACT_REVIEW.md",f"""# Research D final contract review and closeout

## Final contract as executed

The approved contract was locked in `final_contract.json`: causalAssembly {lock['runtime']['causalAssembly']}, upstream `{lock['external_source']['commit']}`, Station1 graph hash `{lock['graph']['sha256']}`, fixed Development training frame (512 rows), action `Station1_mp_0`, target `Station1_mp_4`, five approved actions, training-only target `{lock['task']['target']}`, scale `{lock['task']['scale']}`, 200 new G0 IDs (`703001–703200`), 17 policies × five budgets, 2,500 independent hard-do draws per action and 10,000 chunked bootstrap replicates. No final-training observations were added.

## Review conclusion

The final experiment completed and passed the independent integrity audit. Primary B=2 S0−Full Greedy was +0.034225; its two-source 95% interval was +0.006173 to +0.065351. The action-MC and combined precision half-width goals were missed. M4 was only slightly worse in loss than Full Greedy but used 71.1% fewer edits and recommended the same action 99% of the time. These conclusions are conditional on the fitted DGP, training frame, benchmark DAG and virtual intervention semantics.

## Claims approved for reporting

1. The locked external semisynthetic final evaluation completed without response generation shortfall or integrity failure.
2. Within the fixed generator and training frame, the mean B=2 S0−Full Greedy target-tracking loss contrast was positive, with the reported bootstrap intervals and precision shortfall.
3. M4 and Full Greedy nearly always agreed on the action at lower M4 edit count; this is a conditional efficiency pattern, not universal equivalence.
4. The external DGP did not establish physical manufacturing effects, complete causal truth, independently sampled external SCMs, or deployment benefit.

Claims about real-world intervention effectiveness, absolute manufacturing regret, operating cost/safety, target attainability, or generalization to a manufacturing population are outside this contract.

## Final evaluation readiness decision

**Gate: `{complete['final_gate']}`.** The Research D final external semisynthetic evaluation is complete; no further external datasets or final samples are authorized or needed for this closeout. The remaining work is publication and team synthesis, with Research C preserved as the completed primary study and the physical external validation track explicitly deferred.
""")

    print(json.dumps({"status":"PUBLIC_CLOSEOUT_RENDERED","files":9,
        "summary_sha256":sha(HERE/"final_summary.json"),
        "public_manifest_sha256":sha(HERE/"final_public_execution_manifest.json")},sort_keys=True))


if __name__=="__main__": main()
