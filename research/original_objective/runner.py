"""Independent execution entry points for Research C.

Fixture mode runs only the repository's explicit TEST_ONLY SCM through the
existing G0, policy, fit/recommendation and analytic GT evaluation code.
Research mode remains fail-closed until a separately approved contract and
matching execution manifest exist; cohort orchestration is a later stage.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

from . import policy_engine as pe
from .e2e_fixture import run_fixed_fixture
from .fixed_fixture_data import make_fixed_fixture
from .g0_candidate import corrupt_graph_candidate
from research.budget_aware_refinement.step3_adapter import K


ROOT = Path(__file__).resolve().parents[2]
CODE_BINDING_FILES = (
    "research/original_objective/runner.py",
    "research/original_objective/e2e_fixture.py",
    "research/original_objective/policy_engine.py",
    "research/original_objective/g0_candidate.py",
    "research/original_objective/fixed_fixture_data.py",
    "research/original_objective/unresolved_abstention.py",
    "research/budget_aware_refinement/step4c1_scm.py",
    "research/budget_aware_refinement/step3_adapter.py",
    "research/budget_aware_refinement/step4c1_gt.py",
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


def run_fixture_mode(output_path: Path, *, g0_seed: int = 44017,
                     task_id: str = "fixed-test-only-task",
                     budgets=(0, 1, 2, 3, 4)) -> dict:
    """Run one fixed TEST_ONLY SCM and atomically persist policy outcomes."""
    output_path = Path(output_path).expanduser().resolve()
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing result: {output_path}")
    fixture, metadata = make_fixed_fixture()
    truth = pe.state(fixture.truth_spec["edges"])
    g0 = corrupt_graph_candidate(truth, nodes=fixture.truth_spec["nodes"],
                                 action=fixture.action, target=fixture.target,
                                 master_seed=g0_seed, task_id=task_id)
    initial = pe.state(g0["initial_graph"]["edges"],
                       unresolved=g0["initial_graph"]["unresolved"])
    fixture = replace(fixture, initial_graph=initial, test_only=True)

    code_hashes = _code_hashes(ROOT)
    input_binding = _input_binding(fixture)
    config = {
        "mode": "FIXTURE_TEST_ONLY", "budgets": list(budgets),
        "g0_seed": g0_seed, "task_id": task_id,
        "g0_rates": g0["rates"]["configured"],
        "policy_ids": ["S0", *["+".join(s) for s in pe.catalog()], "CANONICAL_ORACLE"],
        "repair_config": pe.Config().__dict__,
        "unresolved_encoding": "Residual UNRES Abstention Encoding",
    }
    config_hash = _digest({"config": config, "code_sha256": code_hashes})
    result = run_fixed_fixture(fixture, budgets=tuple(budgets), config=pe.Config())

    for budget_result in result["budgets"]:
        for policy in budget_result["policies"]:
            policy["shared_input_sha256"] = _digest(input_binding)
            policy["shared_observations_sha256"] = input_binding["observations_sha256"]
            policy["shared_action_candidates"] = input_binding["action_candidates"]
    payload = {
        "schema": "research-c-fixture-runner-v1",
        "classification": "TEST_ONLY_NOT_RESEARCH_COHORT",
        "test_only": True,
        "research_cohort_generated": False,
        "research_regret_result": False,
        "config": config,
        "config_sha256": config_hash,
        "code_sha256": code_hashes,
        "source_revision": _git_revision(ROOT),
        "input_binding": input_binding,
        "input_sha256": _digest(input_binding),
        "g0_generation": g0,
        "fixture_metadata": metadata,
        "e2e_result": result,
    }
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
            "config_sha256": config_hash, "input_sha256": payload["input_sha256"],
            "policy_evaluation_count": sum(len(row["policies"]) for row in result["budgets"]),
            "all_policy_vectors_complete": all(row["policy_vector_status"] == "COMPLETE"
                                                for row in result["budgets"]),
            "classification": payload["classification"]}


def run_research_mode(*, approved_config_path: Path | None,
                      execution_manifest_path: Path | None,
                      fixture_factory=make_fixed_fixture):
    """Fail closed before invoking any data/SCM factory.

    This first-stage runner intentionally has no research-cohort executor. A
    valid future approval bundle will still require the later cohort runner.
    """
    if approved_config_path is None or execution_manifest_path is None:
        raise ResearchModeBlocked("approved config and matching execution manifest are required")
    try:
        config = json.loads(Path(approved_config_path).read_text(encoding="utf-8"))
        manifest = json.loads(Path(execution_manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchModeBlocked("approval config/manifest is missing or invalid") from exc
    if (config.get("contract_status") != "USER_APPROVED"
            or config.get("research_cohort_execution_enabled") is not True):
        raise ResearchModeBlocked("research contract is not explicitly user-approved and enabled")
    if manifest.get("approval_status") != "USER_APPROVED":
        raise ResearchModeBlocked("execution manifest lacks USER_APPROVED status")
    if manifest.get("config_sha256") != _digest(config):
        raise ResearchModeBlocked("execution manifest config hash mismatch")
    raise NotImplementedError(
        "approval bundle validated, but multi-SCM production orchestration is a later implementation stage")
