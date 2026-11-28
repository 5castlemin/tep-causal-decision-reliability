import hashlib
import json

import networkx as nx

from research.supplementary_validation.s7.s7_external_runner import runtime_config, sha_value, task_metrics


def test_strict_indirect_task_metadata_distinguishes_backdoor():
    graph = nx.DiGraph([("U", "X"), ("U", "Y"), ("X", "M"), ("M", "Y")])
    details = task_metrics(graph, "Station2", "X", "Y")
    assert details["shortest_directed_path_length"] == 2
    assert details["full_graph_backdoor_support"] is True


def test_recommendation_content_digest_excludes_digest_field():
    obj = {"schema": "test", "outcomes_read": False}
    obj["content_sha256"] = hashlib.sha256(json.dumps(
        obj, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()).hexdigest()
    assert sha_value(obj) == obj["content_sha256"]


def test_runtime_config_uses_nested_locked_contract_fields():
    config = runtime_config({
        "generator": {
            "fit_seed": 11, "training_seed": 12,
            "g0_count_per_task_stratum": 200, "g0_id_start": 971000,
            "seed_namespace": "locked", "training_rows": 512,
        },
        "evaluation": {
            "response_rows_per_action": 5000,
            "bootstrap_replicates": 10000, "bootstrap_seed": 13,
        },
        "resource_limits": {"wall_seconds_cumulative": 14400},
    })
    assert config["fit_seed"] == 11
    assert config["g0_count"] == 200
    assert config["response_rows_per_action"] == 5000
    assert config["bootstrap_seed"] == 13
    assert config["resource_limits"]["wall_seconds_cumulative"] == 14400
