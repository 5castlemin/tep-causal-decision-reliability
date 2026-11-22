"""Research C structural repair engine. No SCM outcomes enter this module.

All numeric defaults are provisional fixture settings, not a preregistration.
Unresolved edges are stored as an unordered pair; directed edges as (source,target).
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from typing import Mapping

UNRES = "UNRES"
METRICS = ("M1", "M2", "M3", "M4")
KINDS = ("FN", "FP", "REV", "UNRES")


def pair(u: str, v: str) -> tuple[str, str]:
    if u == v:
        raise ValueError("Self edge")
    return tuple(sorted((u, v)))


def state(edges=(), unresolved=()) -> dict[tuple[str, str], tuple[str, str] | str]:
    result = {}
    for u, v in edges:
        p = pair(u, v)
        if p in result:
            raise ValueError("Duplicate adjacency")
        result[p] = (u, v)
    for u, v in unresolved:
        p = pair(u, v)
        if p in result:
            raise ValueError("Duplicate adjacency")
        result[p] = UNRES
    if not dag(result):
        raise ValueError("Directed cycle")
    return result


def dag(g: Mapping[tuple[str, str], tuple[str, str] | str]) -> bool:
    edges = [e for e in g.values() if e != UNRES]
    nodes = {n for e in edges for n in e}
    children = {n: [] for n in nodes}
    indeg = {n: 0 for n in nodes}
    for u, v in edges:
        children[u].append(v)
        indeg[v] += 1
    queue = [n for n in nodes if indeg[n] == 0]
    seen = 0
    while queue:
        u = queue.pop()
        seen += 1
        for v in children[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return seen == len(nodes)


def graph_hash(g) -> str:
    rows = [[*p, *(list(e) if e != UNRES else [UNRES])] for p, e in sorted(g.items())]
    return sha256(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def task_zone(truth, action: str, target: str) -> tuple[set[tuple[str, str]], set[str]]:
    """Directed X-Y paths plus open, unconditioned backdoor paths in GT DAG."""
    if action == target:
        raise ValueError("Action and target must differ")
    edges = set(truth.values())
    adj = {n: set() for e in edges for n in e}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    if action not in adj or target not in adj:
        return set(), {action, target}
    selected = set()

    def visit(path):
        u = path[-1]
        if u == target:
            directed = all((a, b) in edges for a, b in zip(path, path[1:]))
            backdoor = (path[1], action) in edges and all(
                not ((path[i - 1], path[i]) in edges and (path[i + 1], path[i]) in edges)
                for i in range(1, len(path) - 1)
            )
            if directed or backdoor:
                selected.update(pair(a, b) for a, b in zip(path, path[1:]))
            return
        for v in sorted(adj[u] - set(path)):
            visit(path + [v])

    visit([action])
    return selected, {n for p in selected for n in p} | {action, target}


@dataclass(frozen=True)
class Config:
    fp_rule: str = "A"
    normalization: str = "fixed_opportunity"
    costs: tuple[tuple[str, float], ...] = (("add", 1), ("delete", 1), ("orient", 1), ("resolve", 1), ("delete_unresolved", 1))
    beta: tuple[float, float, float, float] = (1, 1, 1, 1)
    weights: tuple[float, float, float, float] = (1, 1, 1, 1)
    task_multiplier: float = 1
    route_relevant_fp: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        if self.fp_rule not in ("A", "B") or self.normalization not in ("fixed_opportunity", "initial_error_count"):
            raise ValueError("Unknown provisional configuration")
        if any(v <= 0 for _, v in self.costs) or any(v < 0 for v in self.beta + self.weights) or self.task_multiplier < 0:
            raise ValueError("Invalid costs or weights")


@dataclass(frozen=True)
class Edit:
    metric: str
    kind: str
    pair: tuple[str, str]
    operation: str
    replacement: tuple[str, str] | None

    @property
    def key(self):
        return (self.metric, self.pair, self.operation)


def classify(truth, estimate, action, target, config: Config):
    zone, nodes = task_zone(truth, action, target)
    route = {pair(*p) for p in config.route_relevant_fp}
    events = {}
    for p in sorted(set(truth) | set(estimate)):
        t, e = truth.get(p), estimate.get(p)
        if t is None:
            if e is None:
                continue
            in_zone = set(p) <= nodes or (config.fp_rule == "B" and len(set(p) & nodes) == 1 and p in route)
            events[p] = ("M4" if in_zone else "M2", "FP")
        elif e is None:
            events[p] = ("M4" if p in zone else "M1", "FN")
        elif e == UNRES:
            events[p] = ("M4" if p in zone else "M3", "UNRES")
        elif e != t:
            events[p] = ("M4" if p in zone else "M3", "REV")
    return events, zone, nodes


def metrics(truth, estimate, action, target, config: Config):
    events, zone, nodes = classify(truth, estimate, action, target, config)
    counts = {m: {k: 0 for k in KINDS} for m in METRICS}
    for m, k in events.values():
        counts[m][k] += 1
    off_true = [p for p in truth if p not in zone]
    off_pred = [p for p in estimate if (p in truth and p not in zone) or (p not in truth and events[p][0] == "M2")]
    off_matched = [p for p in off_true if p in estimate]
    correct = sum(estimate[p] == truth[p] for p in off_matched)
    oriented = correct + counts["M3"]["REV"]
    task_true = [p for p in truth if p in zone]
    task_pred = [p for p in estimate if (p in truth and p in zone) or (p not in truth and events[p][0] == "M4")]
    support = {
        "M1": len(off_true), "M2": len(off_pred), "M3": len(off_true),
        "M4": {"FN": len(task_true), "FP": len(task_pred),
               "REV": sum(p in estimate and estimate[p] != UNRES for p in task_true),
               "UNRES": sum(p in estimate for p in task_true)},
    }
    def rate(n, d):
        return {"numerator": n, "denominator": d, "value": n / d if d else None,
                "na_reason": None if d else "zero_denominator"}
    report = {
        "M1": rate(counts["M1"]["FN"], support["M1"]),
        "M2": rate(counts["M2"]["FP"], support["M2"]),
        "M3_accuracy": rate(correct, oriented),
        "M3_unresolved": rate(counts["M3"]["UNRES"], len(off_matched)),
        "M4": {k: rate(counts["M4"][k], support["M4"][k]) for k in KINDS},
    }
    return {"events": events, "counts": counts, "support": support, "report": report,
            "zone_pairs": sorted(zone), "zone_nodes": sorted(nodes)}


def candidates(truth, estimate, action, target, config):
    result = []
    for p, (m, k) in metrics(truth, estimate, action, target, config)["events"].items():
        if k == "FN":
            op, replacement = "add", truth[p]
        elif k == "FP":
            op, replacement = "delete", None
        elif k == "UNRES":
            op, replacement = "resolve", truth[p]
        else:
            op, replacement = "orient", truth[p]
        result.append(Edit(m, k, p, op, replacement))
    return tuple(sorted(result, key=lambda e: (METRICS.index(e.metric), e.pair, e.operation)))


def apply(estimate, edit):
    result = dict(estimate)
    if edit.replacement is None:
        result.pop(edit.pair)
    else:
        result[edit.pair] = edit.replacement
    return result


def burden(stats, initial, subset, config):
    if not subset:
        return 0.0
    terms = []
    for m in subset:
        if m != "M4":
            k = {"M1": ("FN",), "M2": ("FP",), "M3": ("REV", "UNRES")}[m]
            numerator = sum(stats["counts"][m][x] for x in k)
            denom = initial["support"][m] if config.normalization == "fixed_opportunity" else sum(initial["counts"][m][x] for x in k)
            terms.append(numerator / denom if denom else 0.0)
        else:
            active = []
            for i, k in enumerate(KINDS):
                denom = initial["support"][m][k] if config.normalization == "fixed_opportunity" else initial["counts"][m][k]
                if initial["counts"][m][k] and denom:
                    active.append((config.beta[i], stats["counts"][m][k] / denom))
            mass = sum(w for w, _ in active)
            terms.append(sum(w * x for w, x in active) / mass if mass else 0.0)
    return sum(terms) / len(terms)


def common_penalty(stats, config):
    total = 0.0
    for m in METRICS:
        for i, k in enumerate(KINDS):
            total += stats["counts"][m][k] * config.weights[i] * (config.task_multiplier if m == "M4" else 1)
    return total


def catalog():
    return ((),) + tuple(s for size in range(1, 5) for s in combinations(METRICS, size))


def run(truth, estimate, action, target, budget, subset, config=Config(), canonical=False):
    if budget < 0 or not set(subset) <= set(METRICS) or len(set(subset)) != len(subset):
        raise ValueError("Invalid budget or subset")
    if not dag(truth) or not dag(estimate):
        raise ValueError("Graph must be DAG")
    initial = metrics(truth, estimate, action, target, config)
    pool = candidates(truth, estimate, action, target, config)
    current, spent, log, applied, dag_rejects = dict(estimate), 0.0, [], set(), 0
    reason = "no_edit_policy" if not subset and not canonical else "candidate_pool_exhausted"
    while subset or canonical:
        if spent >= budget:
            reason = "budget_exhausted"
            break
        available = [e for e in pool if e.key not in applied and (canonical or e.metric in subset)]
        if not available:
            break
        scored = []
        for e in available:
            if current.get(e.pair) == e.replacement:
                continue
            cost = dict(config.costs)[e.operation]
            if cost > budget - spent:
                continue
            trial = apply(current, e)
            if not dag(trial):
                dag_rejects += 1
                continue
            before = metrics(truth, current, action, target, config)
            after = metrics(truth, trial, action, target, config)
            direct = before["events"].get(e.pair) == (e.metric, e.kind) and e.pair not in after["events"]
            gain = burden(before, initial, subset, config) - burden(after, initial, subset, config) if subset else 0
            if direct and (canonical or gain > 1e-12):
                scored.append((e, cost, gain / cost, trial, after))
        if not scored:
            reason = "dag_invalid_candidate" if dag_rejects else ("no_feasible_candidate" if any(dict(config.costs)[e.operation] > budget-spent for e in available) else "no_positive_gain")
            break
        scored.sort(key=lambda row: (-(row[2] if not canonical else 0), METRICS.index(row[0].metric), row[0].pair, row[0].operation))
        e, cost, score, trial, after = scored[0]
        previous_hash = graph_hash(current)
        current = trial
        spent += cost
        applied.add(e.key)
        log.append({"order": len(log)+1, "metric": e.metric, "error_type": e.kind,
                    "task_zone": e.metric == "M4", "pair": e.pair, "operation": e.operation,
                    "cost": cost, "cumulative_cost": spent, "remaining_budget": budget-spent,
                    "score": None if canonical else score, "normalization": config.normalization,
                    "before_hash": previous_hash, "after_hash": graph_hash(current)})
    final = metrics(truth, current, action, target, config)
    return {"policy_id": "CANONICAL_ORACLE" if canonical else ("S0" if not subset else "+".join(subset)),
            "budget": budget, "initial_hash": graph_hash(estimate), "final_hash": graph_hash(current),
            "final_edges": sorted(e for e in current.values() if e != UNRES),
            "final_unresolved": sorted(p for p, e in current.items() if e == UNRES),
            "edits": log, "total_cost": spent, "unused_budget": budget-spent,
            "dag_rejects": dag_rejects, "stop_reason": reason,
            "initial_metrics": initial["report"], "final_metrics": final["report"],
            "initial_counts": initial["counts"], "final_counts": final["counts"],
            "P_S": burden(final, initial, subset, config) if subset else None,
            "P_all": common_penalty(final, config), "normalization": config.normalization,
            "evaluation": evaluation_record()}


def run_catalog(truth, estimate, action, target, budget, config=Config()):
    return {"strategies": [run(truth, estimate, action, target, budget, s, config) for s in catalog()],
            "canonical_oracle": run(truth, estimate, action, target, budget, METRICS, config, canonical=True)}


def save_json(path, result):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")


def evaluation_record(predicted_losses: Mapping[str, float] | None = None):
    """Outcome firewall: only predicted action losses can populate margin here."""
    margin = None
    if predicted_losses:
        values = sorted(predicted_losses.values())
        if len(values) >= 2:
            margin = values[1] - values[0]  # ties yield zero
    return {"selected_action": None, "gt_selected_loss": None, "gt_best_loss": None,
            "decision_regret": None, "regret_vs_s0": None, "same_action": None,
            "regret_tie": None, "decision_margin": margin}
