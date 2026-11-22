"""Provisional, outcome-blind G0 corruption candidate.

This is a design/fixture utility, not an approved cohort generator.  It takes
an explicit DAG and never receives SCM coefficients, observations, losses, or
regret.  The proposed rates are scenario settings that require approval.
"""
from __future__ import annotations

from hashlib import sha256
import random

from .policy_engine import Config, UNRES, dag, metrics, pair, task_zone

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
    proposals = []
    for p in sorted(truth):
        true_rng = _rng(master_seed, task_id, digest, f"true-adjacency:{p[0]}:{p[1]}")
        if true_rng.random() >= true_corruption_rate:
            continue
        kind = ("FN", "REV", "UNRES")[true_rng.randrange(3)]
        correct = truth[p]
        replacement = None if kind == "FN" else UNRES if kind == "UNRES" else (correct[1], correct[0])
        proposals.append({"pair": p, "kind": kind, "task_zone": p in zone_pairs,
                          "replacement": replacement, "source": "true_adjacency"})

    absent = [pair(a, b) for i, a in enumerate(nodes) for b in nodes[i + 1:]
              if pair(a, b) not in truth]
    for p in absent:
        fp_rng = _rng(master_seed, task_id, digest, f"false-adjacency:{p[0]}:{p[1]}")
        if fp_rng.random() >= false_adjacency_rate:
            continue
        direction = (p[0], p[1]) if fp_rng.randrange(2) == 0 else (p[1], p[0])
        proposals.append({"pair": p, "kind": "FP", "task_zone": set(p) <= zone_nodes,
                          "replacement": direction, "source": "true_nonadjacency"})

    # Do not give canonical node/pair IDs first claim on DAG-compatible slots.
    # The permutation is deterministic for the same bound input but independent
    # of error outcomes and metric scores.
    order_rng = _rng(master_seed, task_id, digest, "dag-acceptance-order")
    order = list(range(len(proposals)))
    order_rng.shuffle(order)
    current = dict(truth)
    rows = [None] * len(proposals)
    for accepted_order, proposal_index in enumerate(order, start=1):
        proposal = proposals[proposal_index]
        p, replacement = proposal["pair"], proposal["replacement"]
        trial = dict(current)
        if replacement is None:
            trial.pop(p, None)
        else:
            trial[p] = replacement
        status = "accepted" if dag(trial) else "rejected_dag"
        if status == "accepted":
            current = trial
        row = {k: v for k, v in proposal.items() if k != "replacement"}
        row.update({"pair": list(p), "proposed_state": ("ABSENT" if replacement is None
                    else UNRES if replacement == UNRES else list(replacement)),
                    "proposed_direction": list(replacement) if isinstance(replacement, tuple) else None,
                    "proposal_status": "proposed", "acceptance_status": status,
                    "acceptance_order": accepted_order})
        rows[proposal_index] = row

    if not dag(current):
        raise AssertionError("corruption candidate emitted a cyclic graph")
    event_stats = metrics(truth, current, action, target, Config(fp_rule="A"))
    realized = {m: {k: event_stats["counts"][m][k] for k in ("FN", "FP", "REV", "UNRES")}
                for m in ("M1", "M2", "M3", "M4")}
    opportunities = {m: {k: {"task_zone": 0, "off_task": 0}
                         for k in ("FN", "FP", "REV", "UNRES")}
                     for m in ("M1", "M2", "M3", "M4")}
    for p in truth:
        task = p in zone_pairs
        for kind in ("FN", "REV", "UNRES"):
            metric = "M4" if task else "M1" if kind == "FN" else "M3"
            opportunities[metric][kind]["task_zone" if task else "off_task"] += 1
    for p in absent:
        task = set(p) <= zone_nodes
        metric = "M4" if task else "M2"
        opportunities[metric]["FP"]["task_zone" if task else "off_task"] += 1
    actual_by_kind_zone = {k: {"task_zone": 0, "off_task": 0} for k in ("FN", "FP", "REV", "UNRES")}
    for p, (_, kind) in event_stats["events"].items():
        metric = event_stats["events"][p][0]
        task = metric == "M4"
        actual_by_kind_zone[kind]["task_zone" if task else "off_task"] += 1

    proposals_by_kind = {k: sum(x["kind"] == k for x in rows) for k in ("FN", "FP", "REV", "UNRES")}
    accepted_by_kind = {k: sum(x["kind"] == k and x["acceptance_status"] == "accepted" for x in rows)
                        for k in ("FN", "FP", "REV", "UNRES")}
    true_edges = len(truth)
    false_pairs = len(absent)
    true_proposals = sum(proposals_by_kind[k] for k in ("FN", "REV", "UNRES"))
    true_accepted = sum(accepted_by_kind[k] for k in ("FN", "REV", "UNRES"))
    fp_accepted = accepted_by_kind["FP"]
    realized_count = sum(sum(v.values()) for v in actual_by_kind_zone.values())
    return {"contract_status": "PROPOSED_NOT_APPROVED",
            "generation_status": "GENERATED" if realized_count else "NO_INITIAL_ERRORS",
            "test_or_cohort_use": "not_authorized",
            "truth_graph_sha256": digest,
            "initial_graph": {"edges": [list(e) for _, e in sorted(current.items()) if e != UNRES],
                             "unresolved": [list(p) for p, e in sorted(current.items()) if e == UNRES]},
            "task_zone_rule": "GT_XY_paths_plus_unconditioned_open_backdoors; FP_Rule_A",
            "task_zone_pairs": [list(p) for p in sorted(zone_pairs)],
            "task_zone_nodes": sorted(zone_nodes),
            "event_opportunities_by_metric_kind_and_zone": opportunities,
            "realized_error_counts_by_metric": realized,
            "realized_error_counts_by_kind_and_zone": actual_by_kind_zone,
            "attempted_events": rows,
            "summary": {"true_adjacencies_considered": true_edges,
                        "false_pairs_considered": false_pairs,
                        "proposed": len(rows),
                        "accepted": sum(x["acceptance_status"] == "accepted" for x in rows),
                        "rejected_dag": sum(x["acceptance_status"] == "rejected_dag" for x in rows),
                        "proposed_by_kind": proposals_by_kind,
                        "accepted_by_kind": accepted_by_kind,
                        "retries": 0},
            "rates": {"configured": {"true_adjacency_corruption": true_corruption_rate,
                                       "false_adjacency": false_adjacency_rate,
                                       "conditional_true_error_mix": {"FN": 1/3, "REV": 1/3, "UNRES": 1/3}},
                      "proposed": {"true_adjacency_corruption": true_proposals / true_edges if true_edges else None,
                                   "false_adjacency": proposals_by_kind["FP"] / false_pairs if false_pairs else None,
                                   "true_error_mix": ({k: proposals_by_kind[k] / true_proposals
                                                       for k in ("FN", "REV", "UNRES")} if true_proposals else None)},
                      "accepted": {"true_adjacency_corruption": true_accepted / true_edges if true_edges else None,
                                   "false_adjacency": fp_accepted / false_pairs if false_pairs else None,
                                   "error_rates_by_metric_kind": {
                                       m: {k: (realized[m][k] /
                                           sum(opportunities[m][k].values())
                                           if sum(opportunities[m][k].values()) else None)
                                           for k in ("FN", "FP", "REV", "UNRES")}
                                       for m in ("M1", "M2", "M3", "M4")}}}}
