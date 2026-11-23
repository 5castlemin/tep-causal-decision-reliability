"""Independent execution entry points for Research C.

Fixture mode runs explicit TEST_ONLY inputs. Research mode validates an
approved contract/manifest before invoking the same proposal, SCM/G0, policy,
fit/recommendation, analytic GT and durable cohort orchestration path.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import platform
from importlib import metadata

from . import policy_engine as pe
from .e2e_fixture import (run_fixed_fixture, _RESEARCH_EXECUTION_CAPABILITY)
from .fixed_fixture_data import make_fixed_fixture
from .g0_candidate import corrupt_graph_candidate
from research.budget_aware_refinement.step3_adapter import K


ROOT = Path(__file__).resolve().parents[2]
CODE_BINDING_FILES = (
    "research/original_objective/runner.py",
    "research/original_objective/cohort_runner.py",
    "research/original_objective/proposal_pipeline.py",
    "research/original_objective/cohort_ledger_test_only.py",
    "research/original_objective/execution_limits.py",
    "research/original_objective/research_c_approved_execution.schema.json",
    "research/original_objective/research_c_candidate_config.schema.json",
    "research/original_objective/research_c_runtime_lock.txt",
    "requirements.txt",
    "scripts/run_research_c_runner.py",
    "scripts/run_research_c_generated_fixture.py",
    "research/original_objective/e2e_fixture.py",
    "research/original_objective/policy_engine.py",
    "research/original_objective/g0_candidate.py",
    "research/original_objective/fixed_fixture_data.py",
    "research/original_objective/unresolved_abstention.py",
    "research/budget_aware_refinement/step4c1_scm.py",
    "research/budget_aware_refinement/step4c1_proposal.py",
    "research/budget_aware_refinement/step4_rng.py",
    "research/budget_aware_refinement/step4_topology_generator.py",
    "research/budget_aware_refinement/step4b_task_budget.py",
    "research/budget_aware_refinement/step4b2_population.py",
    "research/budget_aware_refinement/step3_adapter.py",
    "research/budget_aware_refinement/step4c1_gt.py",
    "research/budget_aware_refinement/step4b4_mock_runner.py",
    "src/integrated_pilot.py",
    "src/decision_mvp.py",
)


class ResearchModeBlocked(PermissionError):
    """Raised before any research input is generated or loaded."""


def _canonical(value) -> bytes:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _jsonable(value):
    if isinstance(value, dict):
        return {(json.dumps(list(key), ensure_ascii=False) if isinstance(key, tuple) else str(key)):
                _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _digest(value) -> str:
    return sha256(value if isinstance(value, bytes) else _canonical(value)).hexdigest()


def _code_hashes(root: Path) -> dict[str, str]:
    return {name: sha256((root / name).read_bytes()).hexdigest()
            for name in CODE_BINDING_FILES}


def _git_revision(root: Path) -> dict[str, str | None]:
    def get(ref):
        try:
            return subprocess.check_output(["git", "rev-parse", ref], cwd=root,
                                           text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    return {"commit": get("HEAD"), "tree": get("HEAD^{tree}")}


def _runtime_fingerprint() -> dict:
    versions = {}
    for distribution in metadata.distributions():
        name = distribution.metadata.get("Name")
        if name:
            normalized = re.sub(r"[-_.]+", "-", name).lower()
            versions[normalized] = distribution.version
    versions = dict(sorted(versions.items()))
    return {"python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "dependencies": versions}


def _git_clean_except_build_artifacts(root: Path) -> bool:
    try:
        rows = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            cwd=root, stderr=subprocess.DEVNULL).decode("utf-8", errors="strict").split("\0")
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        return False
    for row in rows:
        if not row:
            continue
        path = row[3:]
        if path == ".build_reframed" or path.startswith(".build_reframed/"):
            continue
        return False
    return True


def _validate_supported_research_contract(config: dict) -> None:
    """Reject approved bundles whose scientific settings are not implemented here."""
    from research.budget_aware_refinement.step4_topology_generator import TEMPLATES
    from research.budget_aware_refinement.step3_adapter import K
    expected = {
        "population": {
            "topology_source": "existing_step4_topology_generator_new_research_c_rng_namespace",
            "templates": list(TEMPLATES), "node_counts": [6, 7, 8, 9, 10],
            "target_edge_density": [0.2, 0.4],
            "task_rule": "uniform_over_all_strict_indirect_only_pairs; require_no_direct_X_to_Y_edge",
        },
        "scm": {
            "family": "signed_linear_acyclic", "coefficient_abs_range": [0.25, 0.8],
            "sign_probability": "independent_fair_sign",
            "noise": {"family": "independent_centered_gaussian", "sd_range": [0.8, 1.2]},
            "observations": {"n": 512, "shared_across_policies": True,
                "training": "common_observational_sample",
                "evaluation": "analytic_GT_no_heldout_observational_loss"},
        },
        "task": {"action": "preselected_uniform_eligible_pair",
            "target": "preselected_uniform_eligible_pair",
            "delta": "alternating_by_admission_ordinal_within_new_cohort",
            "action_grid": list(K), "loss": "squared_standardized_target_mean_error_on_shared_grid"},
        "g0": {"true_adjacency_corruption_rate": 0.15, "false_adjacency_rate": 0.05,
            "true_error_mix": {"FN": 1/3, "REV": 1/3, "UNRES": 1/3},
            "fp_orientation": "fair_direction_draw; reject_if_cyclic",
            "dag_invalid": "record_and_reject_without_redraw", "retry_limit": 0},
        "repair": {"metric_subsets": "all_15_nonempty_subsets_plus_S0",
            "canonical_oracle": "separate_same_information_candidate_cost_budget_DAG_constraints",
            "normalization": "G0_fixed_opportunity; sensitivity_initial_error_count",
            "metric_weights": "equal_selected_metric_weights",
            "m4_beta": "equal_active_FN_FP_REV_UNRES_components",
            "fp_rule": "A_primary_B_sensitivity",
            "edit_costs": {"add": 1, "delete": 1, "orient": 1, "resolve": 1,
                           "delete_unresolved": 1}, "budgets": [0, 1, 2, 3, 4]},
        "evaluation": {"recommendation_input": "shared_observations_and_repaired_graph_only",
            "gt_evaluator": "analytic_hard_do_after_recommendation_frozen",
            "regret": "GT_selected_candidate_loss_minus_best_loss_on_same_grid",
            "research_result_gate": "APPROVED_PREREGISTERED_EXECUTION"},
    }
    for section, value in expected.items():
        if config.get(section) != value:
            raise ResearchModeBlocked(f"approved {section} settings differ from implemented contract candidate")


def _validate_approved_config_schema(config: dict) -> None:
    """Validate the approval instance against both repository JSON Schemas."""
    schema_dir = ROOT / "research" / "original_objective"
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource

        approved_schema = json.loads((schema_dir / "research_c_approved_execution.schema.json")
                                     .read_text(encoding="utf-8"))
        candidate_schema = json.loads((schema_dir / "research_c_candidate_config.schema.json")
                                      .read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(approved_schema)
        Draft202012Validator.check_schema(candidate_schema)
        registry = Registry().with_resource(
            candidate_schema["$id"], Resource.from_contents(candidate_schema))
        errors = sorted(Draft202012Validator(
            approved_schema, registry=registry).iter_errors(config),
            key=lambda error: (list(map(str, error.absolute_path)), error.message))
    except Exception as exc:
        raise ResearchModeBlocked(
            f"approved configuration schema validation is unavailable or invalid: {exc}") from exc
    if errors:
        first = errors[0]
        location = ".".join(map(str, first.absolute_path)) or "<root>"
        raise ResearchModeBlocked(
            f"approved configuration fails JSON Schema at {location}: {first.message}")


def _input_binding(fixture) -> dict:
    data = fixture.observations
    graph = [[*p, *(list(edge) if edge != pe.UNRES else [pe.UNRES])]
             for p, edge in sorted(fixture.initial_graph.items())]
    return {
        "truth_spec_sha256": _digest(dict(fixture.truth_spec)),
        "observations_sha256": sha256(data.tobytes(order="C")).hexdigest(),
        "initial_structural_graph_sha256": pe.graph_hash(fixture.initial_graph),
        "action": fixture.action, "target": fixture.target, "delta": fixture.delta,
        "nodes": list(fixture.truth_spec["nodes"]),
        "action_candidates": list(K),
        "initial_graph_edges": graph,
    }


def execute_fixture_input(fixture, *, metadata: dict, g0_seed: int,
                          task_id: str, budgets=(0, 1, 2, 3, 4),
                          apply_g0_generator: bool = True,
                          _research_authorized: bool = False,
                          _timing_sink: dict | None = None) -> dict:
    """Execute one explicit TEST_ONLY fixture without writing a result file."""
    if fixture.test_only is not True and not _research_authorized:
        raise PermissionError("non-fixture execution requires the approved research runner")
    truth = pe.state(fixture.truth_spec["edges"])
    if apply_g0_generator:
        g0 = corrupt_graph_candidate(truth, nodes=fixture.truth_spec["nodes"],
                                     action=fixture.action, target=fixture.target,
                                     master_seed=g0_seed, task_id=task_id)
        initial = pe.state(g0["initial_graph"]["edges"],
                           unresolved=g0["initial_graph"]["unresolved"])
        fixture = replace(fixture, initial_graph=initial, test_only=True)
    else:
        g0 = {"classification": "TEST_ONLY_FIXED_G0", "g0_seed_binding": g0_seed,
              "task_id": task_id, "initial_graph": {
                  "edges": [list(edge) for edge in fixture.initial_graph.values()
                            if edge != pe.UNRES],
                  "unresolved": [list(pair) for pair, edge in fixture.initial_graph.items()
                                 if edge == pe.UNRES]},
              "retries": 0}

    code_hashes = _code_hashes(ROOT)
    input_binding = _input_binding(fixture)
    config = {
        "mode": "FIXTURE_TEST_ONLY" if fixture.test_only else "APPROVED_RESEARCH_COHORT",
        "budgets": list(budgets),
        "g0_seed": g0_seed, "task_id": task_id,
        "g0_rates": g0.get("rates", {}).get("configured",
                     "EXPLICIT_TEST_ONLY_G0" if fixture.test_only else "RESEARCH_G0_CONFIGURED"),
        "policy_ids": ["S0", *["+".join(s) for s in pe.catalog()], "CANONICAL_ORACLE"],
        "repair_config": pe.Config().__dict__,
        "unresolved_encoding": "Residual UNRES Abstention Encoding",
    }
    config_hash = _digest({"config": config, "code_sha256": code_hashes})
    result = run_fixed_fixture(
        fixture, budgets=tuple(budgets), config=pe.Config(),
        _authorization=_RESEARCH_EXECUTION_CAPABILITY if _research_authorized else None,
        _timing_sink=_timing_sink)
    classification = ("TEST_ONLY_NOT_RESEARCH_COHORT" if fixture.test_only
                      else "RESEARCH_COHORT_RESULT")

    for budget_result in result["budgets"]:
        for policy in budget_result["policies"]:
            policy["shared_input_sha256"] = _digest(input_binding)
            policy["shared_observations_sha256"] = input_binding["observations_sha256"]
            policy["shared_action_candidates"] = input_binding["action_candidates"]
    return {
        "schema": "research-c-fixture-runner-v1",
        "classification": classification,
        "test_only": fixture.test_only,
        "research_cohort_generated": not fixture.test_only,
        "research_regret_result": not fixture.test_only,
        "config": config,
        "config_sha256": config_hash,
        "code_sha256": code_hashes,
        "source_revision": _git_revision(ROOT),
        "runtime_fingerprint": _runtime_fingerprint(),
        "input_binding": input_binding,
        "input_sha256": _digest(input_binding),
        "g0_generation": g0,
        "fixture_metadata": metadata,
        "e2e_result": result,
    }


def run_fixture_mode(output_path: Path, *, g0_seed: int = 44017,
                     task_id: str = "fixed-test-only-task",
                     budgets=(0, 1, 2, 3, 4)) -> dict:
    """Run one fixed TEST_ONLY SCM and atomically persist policy outcomes."""
    output_path = Path(output_path).expanduser().resolve()
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing result: {output_path}")
    fixture, metadata = make_fixed_fixture()
    payload = execute_fixture_input(fixture, metadata=metadata, g0_seed=g0_seed,
                                    task_id=task_id, budgets=budgets)
    wrapper = {"payload": payload, "payload_sha256": _digest(payload)}
    encoded = json.dumps(_jsonable(wrapper), ensure_ascii=False, sort_keys=True,
                         indent=2, allow_nan=False).encode("utf-8") + b"\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(f".{output_path.name}.{os.getpid()}.tmp")
    try:
        with temp_path.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        # A hard-link publishes the complete fsynced file atomically and fails
        # if another process has already created the destination.
        try:
            os.link(temp_path, output_path)
        except FileExistsError:
            raise FileExistsError(f"refusing to overwrite existing result: {output_path}")
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return {"output_path": str(output_path), "payload_sha256": wrapper["payload_sha256"],
            "config_sha256": payload["config_sha256"], "input_sha256": payload["input_sha256"],
            "policy_evaluation_count": sum(len(row["policies"])
                                            for row in payload["e2e_result"]["budgets"]),
            "all_policy_vectors_complete": all(
                row["policy_vector_status"] == "COMPLETE"
                for row in payload["e2e_result"]["budgets"]),
            "classification": payload["classification"]}


def run_research_mode(*, approved_config_path: Path | None,
                      execution_manifest_path: Path | None,
                      fixture_factory=make_fixed_fixture,
                      _test_only_gate_orchestrator=None,
                      validate_only: bool = False):
    """Validate an approved bundle; optionally stop before any proposal generation.

    ``validate_only`` is exposed by the CLI as ``--mode preflight``. It uses
    the same fail-closed checks as Research Mode and returns a summary without
    creating output directories, ledgers, proposals, or SCMs.
    """
    if (_test_only_gate_orchestrator is not None
            and (not callable(_test_only_gate_orchestrator)
                 or getattr(_test_only_gate_orchestrator,
                            "__test_only_approval_gate_hook__", False) is not True)):
        raise PermissionError("injected approval-gate orchestration is TEST_ONLY-only")
    if approved_config_path is None or execution_manifest_path is None:
        raise ResearchModeBlocked("approved config and matching execution manifest are required")
    try:
        config = json.loads(Path(approved_config_path).read_text(encoding="utf-8"))
        manifest = json.loads(Path(execution_manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchModeBlocked("approval config/manifest is missing or invalid") from exc
    _validate_approved_config_schema(config)
    if (config.get("contract_status") != "USER_APPROVED"
            or config.get("research_cohort_execution_enabled") is not True):
        raise ResearchModeBlocked("research contract is not explicitly user-approved and enabled")
    if config.get("preregistration_status") != "PREREGISTERED":
        raise ResearchModeBlocked("research contract must be explicitly preregistered")
    required = {"configuration_version", "preregistration_status", "cohort_type", "run_id", "output_root",
                "population", "scm", "task", "g0", "repair", "evaluation",
                "rng_protocol", "resource_limits", "runtime_fingerprint",
                "target_admissions", "proposal_cap", "budgets"}
    if not required.issubset(config):
        raise ResearchModeBlocked(f"approved config missing fields: {sorted(required - set(config))}")
    if config.get("configuration_version") != "research-c-execution-v1":
        raise ResearchModeBlocked("unsupported research configuration version")
    if config.get("cohort_type") not in {"development", "independent_evaluation"}:
        raise ResearchModeBlocked("config cohort_type must be development or independent_evaluation")
    _validate_supported_research_contract(config)
    if not isinstance(config.get("resource_limits"), dict) or not config["resource_limits"]:
        raise ResearchModeBlocked("approved config must bind nonempty production resource limits")
    if not isinstance(config["budgets"], list) or config["budgets"] != [0, 1, 2, 3, 4]:
        raise ResearchModeBlocked("approved config must explicitly bind the five existing budgets")
    if type(config["target_admissions"]) is not int or config["target_admissions"] <= 0:
        raise ResearchModeBlocked("approved config must bind a positive target_admissions")
    if type(config["proposal_cap"]) is not int or config["proposal_cap"] < config["target_admissions"]:
        raise ResearchModeBlocked("approved config must bind proposal_cap >= target_admissions")
    from research.budget_aware_refinement.step4c1_proposal import ATTEMPT_CAPS
    generator_cohort = ("development" if config["cohort_type"] == "development"
                        else "confirmation")
    if config["proposal_cap"] > ATTEMPT_CAPS[generator_cohort]:
        raise ResearchModeBlocked("proposal_cap exceeds the structural proposal generator cap")
    rng = config["rng_protocol"]
    if not isinstance(rng, dict) or type(rng.get("master_seed")) is not int:
        raise ResearchModeBlocked("rng_protocol must bind an integer master_seed")
    if rng.get("cohort_namespace") != config["cohort_type"]:
        raise ResearchModeBlocked("RNG namespace must match the declared cohort")
    if rng.get("protocol_version") != "step4-rng-v1":
        raise ResearchModeBlocked("unsupported RNG protocol")
    if not isinstance(config["run_id"], str) or not config["run_id"]:
        raise ResearchModeBlocked("run_id must be a nonempty string")
    expected_run_prefix = "development-" if config["cohort_type"] == "development" else "independent-evaluation-"
    if not str(config["run_id"]).startswith(expected_run_prefix):
        raise ResearchModeBlocked("run_id must use a cohort-specific namespace")
    if config.get("runtime_fingerprint") != _runtime_fingerprint():
        raise ResearchModeBlocked("runtime fingerprint differs from approved configuration")
    if not _git_clean_except_build_artifacts(ROOT):
        raise ResearchModeBlocked("tracked or non-build untracked source changes block research execution")
    if manifest.get("approval_status") != "USER_APPROVED":
        raise ResearchModeBlocked("execution manifest lacks USER_APPROVED status")
    if manifest.get("manifest_version") != "research-c-execution-manifest-v1":
        raise ResearchModeBlocked("unsupported execution manifest version")
    if manifest.get("config_sha256") != _digest(config):
        raise ResearchModeBlocked("execution manifest config hash mismatch")
    if manifest.get("cohort_type") != config["cohort_type"]:
        raise ResearchModeBlocked("execution manifest cohort type mismatch")
    if manifest.get("runtime_fingerprint") != _runtime_fingerprint():
        raise ResearchModeBlocked("execution manifest runtime fingerprint mismatch")
    if manifest.get("excluded_untracked_paths") != [".build_reframed/"]:
        raise ResearchModeBlocked("manifest must explicitly exclude only .build_reframed/ artifacts")
    if manifest.get("source_revision") != _git_revision(ROOT):
        raise ResearchModeBlocked("execution manifest commit/tree mismatch")
    if manifest.get("code_sha256") != _code_hashes(ROOT):
        raise ResearchModeBlocked("execution manifest code hash mismatch")
    if manifest.get("configuration_version") != config["configuration_version"]:
        raise ResearchModeBlocked("execution manifest configuration version mismatch")
    if manifest.get("contract_sha256") != _digest({
            key: config[key] for key in ("configuration_version", "contract_status",
                "preregistration_status", "population", "scm", "task", "g0", "repair", "evaluation")}):
        raise ResearchModeBlocked("execution manifest scientific contract hash mismatch")
    if manifest.get("resource_limits_sha256") != _digest(config["resource_limits"]):
        raise ResearchModeBlocked("execution manifest resource limit hash mismatch")
    if manifest.get("run_id") != config["run_id"]:
        raise ResearchModeBlocked("execution manifest run ID mismatch")
    output_root = Path(config["output_root"]).expanduser().resolve()
    if manifest.get("output_root") != str(output_root):
        raise ResearchModeBlocked("execution manifest output root mismatch")

    # The profile is constructed only after the genuine USER_APPROVED bundle
    # and all source/runtime bindings have passed validation.
    from .execution_limits import ResourceLimits
    from .proposal_pipeline import run_approved_research_proposal_cohort
    try:
        resource_config = dict(config["resource_limits"])
        if "classification" in resource_config:
            raise ValueError("classification is assigned by the validated runner")
        limits = ResourceLimits(
            **resource_config,
            classification="USER_APPROVED_RESEARCH_RESOURCE_PROFILE")
    except (TypeError, ValueError) as exc:
        raise ResearchModeBlocked(f"invalid approved resource profile: {exc}") from exc
    if output_root == ROOT or ROOT in output_root.parents:
        raise ResearchModeBlocked("research output must be outside the source checkout")
    if (output_root / "research_c_fixture_cohort.sqlite").exists():
        raise ResearchModeBlocked("research output root contains a TEST_ONLY cohort ledger")
    if (output_root / "research_c_fixture_proposals.sqlite").exists():
        raise ResearchModeBlocked("research output root contains a TEST_ONLY proposal ledger")
    proposal_db = output_root / "research_c_proposal_stage.sqlite"
    if proposal_db.exists():
        try:
            with sqlite3.connect(proposal_db) as db:
                proposal_runs = db.execute(
                    "SELECT run_id,cohort_type FROM proposal_stage_runs").fetchall()
        except sqlite3.Error as exc:
            raise ResearchModeBlocked("research proposal ledger is unreadable") from exc
        if any(existing_id != config["run_id"] or cohort != config["cohort_type"]
               for existing_id, cohort in proposal_runs):
            raise ResearchModeBlocked("research output root is bound to another proposal run/cohort")
    research_db = output_root / "research_c_cohort.sqlite"
    if research_db.exists():
        try:
            with sqlite3.connect(research_db) as db:
                existing_runs = db.execute("SELECT run_id,cohort_type FROM runs").fetchall()
        except sqlite3.Error as exc:
            raise ResearchModeBlocked("research output ledger is unreadable") from exc
        if any(existing_id != config["run_id"] or cohort != "RESEARCH_COHORT"
               for existing_id, cohort in existing_runs):
            raise ResearchModeBlocked("research output root is already bound to another run/cohort")
    if validate_only:
        return {
            "classification": "RESEARCH_BUNDLE_PREFLIGHT_ONLY",
            "validated": True,
            "proposal_generation_started": False,
            "scm_generation_started": False,
            "cohort_type": config["cohort_type"],
            "run_id": config["run_id"],
            "target_admissions": config["target_admissions"],
            "proposal_cap": config["proposal_cap"],
            "budgets": list(config["budgets"]),
            "output_root": str(output_root),
            "configuration_sha256": _digest(config),
            "source_revision": _git_revision(ROOT),
            "runtime_fingerprint": _runtime_fingerprint(),
            "manifest_status": "USER_APPROVED_BUNDLE_VALIDATED",
        }
    if _test_only_gate_orchestrator is not None:
        # Test injection is deliberately absent from the production CLI. It is
        # invoked only after every real config, manifest, source and runtime
        # binding above has passed; tests route it to a TEST_ONLY output store.
        return _test_only_gate_orchestrator(
            config=config, manifest=manifest, output_root=output_root,
            resource_limits=limits)
    return run_approved_research_proposal_cohort(
        output_root, run_id=config["run_id"], cohort_type=config["cohort_type"],
        master_seed=rng["master_seed"], target_admissions=config["target_admissions"],
        proposal_cap=config["proposal_cap"], budgets=tuple(config["budgets"]),
        resource_limits=limits, _authorization=_RESEARCH_EXECUTION_CAPABILITY)
