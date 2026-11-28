import hashlib
import json

import networkx as nx

from research.supplementary_validation.s7.s7_external_runner import sha_value, task_metrics


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
