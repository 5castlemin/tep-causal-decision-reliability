"""Provisional, outcome-blind G0 corruption candidate.

This is a design/fixture utility, not an approved cohort generator.  It takes
an explicit DAG and never receives SCM coefficients, observations, losses, or
regret.  The proposed rates are scenario settings that require approval.
"""
from __future__ import annotations

from hashlib import sha256
import random

from .policy_engine import UNRES, dag, pair, task_zone

PROPOSED_TRUE_ADJACENCY_CORRUPTION_RATE = 0.15
PROPOSED_FALSE_ADJACENCY_RATE = 0.05


def _rng(master_seed: int, task_id: str, graph_digest: str, stream: str) -> random.Random:
    payload = f"research-c-g0-candidate-v1|{master_seed}|{task_id}|{graph_digest}|{stream}".encode()
    return random.Random(int.from_bytes(sha256(payload).digest(), "big"))


def corrupt_graph_candidate(truth, *, nodes, action: str, target: str, master_seed: int,
                           task_id: str,
                           true_corruption_rate: float = PROPOSED_TRUE_ADJACENCY_CORRUPTION_RATE,
                           false_adjacency_rate: float = PROPOSED_FALSE_ADJACENCY_RATE) -> dict:
    """Build one deterministic G0 candidate and retain all attempted/rejected events.

    For each true adjacency, independently corrupt with rate q; conditional on
    corruption, FN/REV/UNRES have equal probability. For each true nonadjacency,
    independently attempt an FP with rate r and choose direction fairly. Any
    reversal/addition that makes the current directed graph cyclic is rejected
    and recorded; it is not redrawn. Each unordered pair is visited once.
    """
    nodes = tuple(nodes)
    if (not dag(truth) or len(set(nodes)) != len(nodes)
            or any(n not in set(nodes) for p in truth for n in p)):
        raise ValueError("invalid truth graph or nodes")
    if action not in nodes or target not in nodes or action == target:
        raise ValueError("invalid task")
    if not task_id or type(master_seed) is not int or master_seed < 0:
        raise ValueError("task_id and nonnegative master_seed are required")
    if not 0 <= true_corruption_rate <= 1 or not 0 <= false_adjacency_rate <= 1:
        raise ValueError("rates must be in [0,1]")

    nodes = tuple(sorted(nodes))
    digest = sha256(repr(sorted((p, e) for p, e in truth.items())).encode()).hexdigest()
    zone_pairs, zone_nodes = task_zone(truth, action, target)
    current = dict(truth)
    events = []
    for p in sorted(truth):
        true_rng = _rng(master_seed, task_id, digest, f"true-adjacency:{p[0]}:{p[1]}")
        if true_rng.random() >= true_corruption_rate:
            continue
        kind = ("FN", "REV", "UNRES")[true_rng.randrange(3)]
        correct = truth[p]
        if kind == "FN":
            del current[p]
            events.append({"pair": list(p), "kind": kind, "task_zone": p in zone_pairs, "status": "applied"})
        elif kind == "UNRES":
            current[p] = UNRES
            events.append({"pair": list(p), "kind": kind, "task_zone": p in zone_pairs, "status": "applied"})
        else:
            reversed_edge = (correct[1], correct[0])
            trial = dict(current)
            trial[p] = reversed_edge
            if dag(trial):
                current = trial
                events.append({"pair": list(p), "kind": kind, "task_zone": p in zone_pairs, "status": "applied"})
            else:
                events.append({"pair": list(p), "kind": kind, "task_zone": p in zone_pairs,
                               "status": "rejected_dag"})

    absent = [pair(a, b) for i, a in enumerate(nodes) for b in nodes[i + 1:]
              if pair(a, b) not in truth]
    fp_events = []
    for p in absent:
        fp_rng = _rng(master_seed, task_id, digest, f"false-adjacency:{p[0]}:{p[1]}")
        if fp_rng.random() >= false_adjacency_rate:
            continue
        direction = (p[0], p[1]) if fp_rng.randrange(2) == 0 else (p[1], p[0])
        trial = dict(current)
        trial[p] = direction
        if dag(trial):
            current = trial
            status = "applied"
        else:
            status = "rejected_dag"
        fp_events.append({"pair": list(p), "kind": "FP", "task_zone": set(p) <= zone_nodes,
                          "proposed_direction": list(direction),
                          "status": status})

    if not dag(current):
        raise AssertionError("corruption candidate emitted a cyclic graph")
    applied = [e for e in events + fp_events if e["status"] == "applied"]
    return {"status": "PROPOSED_NOT_APPROVED", "test_or_cohort_use": "not_authorized",
            "truth_graph_sha256": digest, "initial_graph": current,
            "initial_edges": [list(e) for _, e in sorted(current.items()) if e != UNRES],
            "initial_unresolved": [list(p) for p, e in sorted(current.items()) if e == UNRES],
            "task_zone_rule": "GT_XY_paths_plus_unconditioned_open_backdoors; FP_Rule_A",
            "task_zone_pairs": [list(p) for p in sorted(zone_pairs)],
            "task_zone_nodes": sorted(zone_nodes),
            "attempted_events": events + fp_events,
            "summary": {"true_adjacencies_considered": len(truth),
                        "false_pairs_considered": len(absent),
                        "attempted": len(events) + len(fp_events),
                        "applied": len(applied),
                        "rejected_dag": sum(e["status"] == "rejected_dag" for e in events + fp_events),
                        "retries": 0},
            "rates": {"true_corruption": true_corruption_rate,
                      "false_adjacency": false_adjacency_rate,
                      "conditional_true_error_mix": {"FN": 1/3, "REV": 1/3, "UNRES": 1/3}}}
