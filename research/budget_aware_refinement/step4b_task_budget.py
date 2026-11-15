"""Structure-only task selection and graph-edit feasibility for Step 4B-1.

This module uses topology, IDs and declared random seeds only. It does not
sample SCM parameters/data or evaluate interventions or regret.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import random

from .step4_topology_generator import directed_paths


@dataclass(frozen=True)
class TaskPairClasses:
    direct_only: tuple[tuple[str, str], ...]
    indirect_only: tuple[tuple[str, str], ...]
    direct_and_indirect: tuple[tuple[str, str], ...]


def derive_stream_seeds(master_seed):
    """Derive stable domain-separated RNG seeds from one fixed master seed."""
    if type(master_seed) is not int or master_seed < 0:
        raise ValueError("master_seed must be a nonnegative integer")
    streams = ("topology", "relabel", "task", "error_injection", "policy_schedule")
    result = {"topology": master_seed}
    for stream in streams[1:]:
        material = f"tep-causal-decision-reliability:step4b1:{master_seed}:{stream}".encode()
        result[stream] = int.from_bytes(sha256(material).digest()[:8], "big")
    return result


def classify_task_pairs(nodes, edges) -> TaskPairClasses:
    """Partition ordered pairs into disjoint structural relation classes."""
    edge_set = set(edges)
    direct_only, indirect_only, both = [], [], []
    for action in nodes:
        for target in nodes:
            if action == target:
                continue
            has_direct = (action, target) in edge_set
            has_indirect = any(len(path) >= 3 for path in directed_paths(nodes, edge_set, action, target))
            if has_direct and has_indirect:
                both.append((action, target))
            elif has_direct:
                direct_only.append((action, target))
            elif has_indirect:
                indirect_only.append((action, target))
    return TaskPairClasses(tuple(direct_only), tuple(indirect_only), tuple(both))


def role_nodes(template, nodes):
    """Return semantic scaffold roles before relabeling; no outcomes involved."""
    if template == "observed_common_cause":
        return {"common_cause": nodes[0], "action": nodes[1],
                "mediator": nodes[2], "target": nodes[-1]}
    if template == "fork_branch":
        return {"action": nodes[0], "branch": nodes[-2], "target": nodes[-1]}
    if template == "chain_mediation":
        return {"action": nodes[0], "target": nodes[-1]}
    if template == "multiple_directed_paths":
        return {"action": nodes[0], "target": nodes[-1],
                "path_a": nodes[1], "path_b": nodes[2]}
    raise ValueError(f"unknown template: {template}")


def relabel_roles(template, nodes, edges, seed):
    """Apply a seeded, outcome-blind bijection to scaffold IDs and return roles."""
    old_roles = role_nodes(template, tuple(nodes))
    rng = random.Random(seed)
    labels = list(nodes)
    rng.shuffle(labels)
    mapping = dict(zip(nodes, labels))
    relabeled_nodes = tuple(sorted(mapping.values()))
    relabeled_edges = frozenset((mapping[a], mapping[b]) for a, b in edges)
    return relabeled_nodes, relabeled_edges, {name: mapping[node] for name, node in old_roles.items()}, mapping


def select_task_pair(nodes, edges, seed, preferred_indirect=None):
    """Select distinct direct and indirect tasks by seeded structural rank.

    Direct is sampled from direct-only pairs. Indirect uses indirect-only
    pairs, except an explicitly declared scaffold-role pair may be both-direct
    and-indirect; the two selected ordered pairs may never be identical.
    """
    classes = classify_task_pairs(nodes, edges)
    chosen = []
    failures = {}
    direct_candidates = list(classes.direct_only)
    indirect_candidates = list(classes.indirect_only)
    preferred_is_indirect = (preferred_indirect in classes.indirect_only or
                             preferred_indirect in classes.direct_and_indirect)
    for kind, candidates in (("direct", direct_candidates),):
        if not candidates:
            failures[kind] = f"no_{kind}_only_task"
            continue
        rng = random.Random(f"{seed}:{kind}")
        ranked = sorted(set(candidates))
        chosen.append((kind, ranked[rng.randrange(len(ranked))]))
    if preferred_is_indirect:
        chosen.append(("indirect", preferred_indirect))
    elif indirect_candidates:
        rng = random.Random(f"{seed}:indirect")
        ranked = sorted(set(indirect_candidates))
        chosen.append(("indirect", ranked[rng.randrange(len(ranked))]))
    else:
        failures["indirect"] = "no_indirect_only_task"
    if len(chosen) == 2 and chosen[0][1] == chosen[1][1]:
        alternatives = [pair for pair in indirect_candidates if pair != chosen[0][1]]
        if alternatives:
            rng = random.Random(f"{seed}:indirect:distinct")
            chosen[1] = ("indirect", sorted(set(alternatives))[rng.randrange(len(set(alternatives)))])
        else:
            failures["indirect"] = "no_distinct_indirect_task"
            chosen = [chosen[0]]
    return {"selected": chosen, "failures": failures,
            "same_pair": len(chosen) == 2 and chosen[0][1] == chosen[1][1],
            "candidate_counts": {"direct_only": len(classes.direct_only),
                                 "indirect_only": len(classes.indirect_only),
                                 "direct_and_indirect": len(classes.direct_and_indirect)}}


def graph_hash(nodes, edges):
    """Hash a directed graph including every immutable node ID."""
    import json
    return sha256(json.dumps({"nodes": sorted(nodes), "edges": sorted(map(list, edges))},
                             sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def operation_opportunities(nodes, truth_edges, initial_edges):
    """Return type-specific correction candidates and DAG-valid corrections."""
    truth, initial = set(truth_edges), set(initial_edges)
    output = {}
    for a, b in combinations(sorted(nodes), 2):
        true_edge = (a, b) if (a, b) in truth else (b, a) if (b, a) in truth else None
        observed = (a, b) if (a, b) in initial else (b, a) if (b, a) in initial else None
        if true_edge and not observed:
            kind, op = "FN", ("FN", *true_edge)
            corrected = initial | {true_edge}
        elif observed and not true_edge:
            kind, op = "FP", ("FP", *observed)
            corrected = initial - {observed}
        elif true_edge and observed and true_edge != observed:
            kind, op = "REV", ("REV", *observed)
            corrected = initial - {observed} | {true_edge}
        else:
            continue
        is_valid = _dag(nodes, corrected)
        output.setdefault(kind, []).append({"operation": op, "dag_valid_correction": is_valid})
    return {kind: {"candidate_count": len(output.get(kind, [])),
                   "dag_valid_count": sum(x["dag_valid_correction"] for x in output.get(kind, [])),
                   "candidates": output.get(kind, [])}
            for kind in ("FN", "FP", "REV")}


def _dag(nodes, edges):
    children = {node: [] for node in nodes}
    indegree = dict.fromkeys(nodes, 0)
    for a, b in edges:
        children[a].append(b)
        indegree[b] += 1
    queue = [node for node in nodes if indegree[node] == 0]
    seen = 0
    while queue:
        node = queue.pop()
        seen += 1
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    return seen == len(nodes)
