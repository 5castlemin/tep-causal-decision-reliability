"""Reference-blind local verification policies for Research F-Lite.

This module intentionally has no imports from the cohort ledger, proposal store,
Research C evaluator, or reference graph code. The expert/evaluator boundaries
are represented by separate callables, not OS-level sandboxing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
import math
from typing import Callable, Mapping, Sequence

import numpy as np

NO_EDGE = "NO_EDGE"
UNRESOLVED = "UNRESOLVED"
U_TO_V = "U_TO_V"
V_TO_U = "V_TO_U"
STATES = (NO_EDGE, U_TO_V, V_TO_U)
K_GRID = (-1.0, -0.5, 0.0, 0.5, 1.0)


def pair_order(nodes: Sequence[str]) -> list[tuple[str, str]]:
    """Outcome-independent lexical order over all unordered variable pairs."""
    return list(combinations(sorted(nodes), 2))


def graph_dag(nodes: Sequence[str], relations: Mapping[tuple[str, str], object]) -> bool:
    children = {n: [] for n in nodes}
    indegree = {n: 0 for n in nodes}
    for (u, v), rel in relations.items():
        if rel in (NO_EDGE, UNRESOLVED, None):
            continue
        if not isinstance(rel, tuple) or len(rel) != 2 or rel[0] not in children or rel[1] not in children:
            return False
        children[rel[0]].append(rel[1])
        indegree[rel[1]] += 1
    ready = [n for n in nodes if indegree[n] == 0]
    seen = 0
    while ready:
        u = ready.pop()
        seen += 1
        for v in children[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                ready.append(v)
    return seen == len(nodes)


def effective_relations(relations: Mapping[tuple[str, str], object]) -> dict[tuple[str, str], object]:
    """Existing C bridge omits unresolved adjacencies from the learner graph."""
    return {p: r for p, r in relations.items() if r != UNRESOLVED}


def bic_for_target(data: np.ndarray, nodes: Sequence[str], target: str,
                   parents: Sequence[str]) -> float:
    """Gaussian linear local BIC, using OLS/lstsq with an intercept.

    The tiny variance floor is machine-epsilon scaled and only prevents log(0)
    for numerically exact fits; it is not a score smoothing parameter.
    """
    arr = np.asarray(data, dtype=np.float64)
    if arr.ndim != 2 or arr.shape != (arr.shape[0], len(nodes)) or arr.shape[0] < 3:
        raise ValueError("invalid observational matrix")
    if not np.isfinite(arr).all() or target not in nodes or any(p not in nodes for p in parents):
        raise ValueError("invalid BIC input")
    y = arr[:, nodes.index(target)]
    x = np.ones((len(y), 1 + len(parents)), dtype=np.float64)
    for j, parent in enumerate(parents, 1):
        x[:, j] = arr[:, nodes.index(parent)]
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    rss = float(np.square(y - x @ beta).sum())
    floor = np.finfo(np.float64).eps * max(float(np.square(y - y.mean()).sum()), 1.0)
    rss = max(rss, floor)
    k = x.shape[1] + 1  # regression parameters plus Gaussian variance
    return float(len(y) * math.log(rss / len(y)) + k * math.log(len(y)))


def graph_bic(data: np.ndarray, nodes: Sequence[str], relations: Mapping[tuple[str, str], object]) -> float:
    rels = effective_relations(relations)
    parents = {n: [] for n in nodes}
    for rel in rels.values():
        if isinstance(rel, tuple):
            parents[rel[1]].append(rel[0])
    return sum(bic_for_target(data, nodes, n, sorted(parents[n])) for n in nodes)


def local_states(nodes: Sequence[str], relations: Mapping[tuple[str, str], object],
                 edge_pair: tuple[str, str]) -> list[tuple[str, dict[tuple[str, str], object], float]]:
    u, v = edge_pair
    base = dict(relations)
    current = base.get(edge_pair, NO_EDGE)
    candidates = []
    for state in STATES:
        if state == NO_EDGE:
            value = NO_EDGE
        elif state == U_TO_V:
            value = (u, v)
        else:
            value = (v, u)
        trial = dict(base)
        if value == NO_EDGE:
            trial.pop(edge_pair, None)
        else:
            trial[edge_pair] = value
        if graph_dag(nodes, trial):
            candidates.append((state, trial, 0.0))
    return candidates


def predict_loss(data: np.ndarray, nodes: Sequence[str], relations: Mapping[tuple[str, str], object],
                 action: str, target: str, action_values: Sequence[float], target_value: float,
                 scale: float, fit_model: Callable, response: Callable) -> tuple[float, float, dict[float, float]]:
    if scale <= 0 or not math.isfinite(scale):
        raise ValueError("scale must be finite and positive")
    edges = {tuple(r) for r in effective_relations(relations).values() if isinstance(r, tuple)}
    model = fit_model(np.asarray(data, dtype=np.float64), list(nodes), edges, 1.0)
    losses = {}
    for a in action_values:
        mu = float(response(model, action, float(a))[target])
        losses[float(a)] = ((mu - target_value) / scale) ** 2
    if not all(math.isfinite(x) for x in losses.values()):
        raise ValueError("nonfinite prediction loss")
    chosen = min(losses, key=lambda a: (losses[a], abs(K_GRID[action_values.index(a)]), K_GRID[action_values.index(a)]))
    return float(chosen), float(losses[chosen]), losses


def score_pairs(policy: str, data: np.ndarray, nodes: Sequence[str],
                relations: Mapping[tuple[str, str], object], action: str, target: str,
                action_values: Sequence[float], target_value: float, scale: float,
                fit_model: Callable, response: Callable,
                model_cache: dict | None = None) -> list[dict]:
    if policy not in {"FIT_BASED_VERIFICATION", "SUSPICION_ONLY", "DECISION_IMPACT_ONLY", "DECISION_WEIGHTED_VERIFICATION"}:
        raise ValueError("unsupported scoring policy")
    current_rel = effective_relations(relations)
    model_cache = {} if model_cache is None else model_cache
    def predicted(g):
        key = tuple(sorted((p, r) for p, r in effective_relations(g).items()))
        if key not in model_cache:
            model_cache[key] = predict_loss(data, nodes, g, action, target, action_values,
                                            target_value, scale, fit_model, response)
        return model_cache[key]
    current_action, _current_minloss, _current_losses = predicted(relations)

    def pair_local_bic(g, pair_):
        rels = effective_relations(g)
        total = 0.0
        for node in pair_:
            parents = sorted(a for edge in rels.values() if isinstance(edge, tuple)
                             for a, b in (edge,) if b == node)
            total += bic_for_target(data, nodes, node, parents)
        return total

    current_bic = {p: pair_local_bic(relations, p) for p in pair_order(nodes)}
    records = []
    for p in pair_order(nodes):
        current = relations.get(p, NO_EDGE)
        states = local_states(nodes, relations, p)
        base_pair_bic = current_bic[p]
        bics = [(s, g, pair_local_bic(g, p)) for s, g, _ in states]
        if not bics:
            continue
        min_bic = min(b for _, _, b in bics)
        weights_raw = [math.exp(-0.5 * (b - min_bic)) for _, _, b in bics]
        denom = sum(weights_raw)
        weights = {s: w / denom for (s, _, _), w in zip(bics, weights_raw)}
        effective_state = NO_EDGE if current in (UNRESOLVED, NO_EDGE) else (U_TO_V if current == p else V_TO_U)
        current_state = UNRESOLVED if current == UNRESOLVED else effective_state
        suspicion = 1.0 if current_state == UNRESOLVED else 1.0 - weights.get(current_state, 0.0)
        impacts = []
        for state, trial, _bic in bics:
            if state == effective_state:
                continue
            trial_action, _trial_min, trial_losses = predicted(trial)
            gain = trial_losses[current_action] - trial_losses[trial_action]
            if gain < -1e-10:
                raise ArithmeticError("alternative's selected action does not minimize its predicted loss")
            impacts.append(max(0.0, gain) if gain >= -1e-10 else gain)
        impact = float(np.mean(impacts)) if impacts else 0.0
        fit_gain = max((base_pair_bic - b for s, _, b in bics if s != effective_state), default=0.0)
        score = {"FIT_BASED_VERIFICATION": fit_gain,
                 "SUSPICION_ONLY": suspicion,
                 "DECISION_IMPACT_ONLY": impact,
                 "DECISION_WEIGHTED_VERIFICATION": suspicion * impact}[policy]
        records.append({"pair": p, "current_state": current_state, "suspicion": suspicion,
                        "decision_impact": impact, "fit_gain": float(fit_gain), "score": float(score)})
    return records


@dataclass
class VerificationState:
    nodes: tuple[str, ...]
    relations: dict[tuple[str, str], object]
    queried: set[tuple[str, str]] = field(default_factory=set)
    pending: dict[tuple[str, str], object] = field(default_factory=dict)
    query_count: int = 0
    edits: int = 0
    history: list[dict] = field(default_factory=list)

    def apply_answer(self, edge_pair: tuple[str, str], answer: str) -> None:
        if edge_pair not in pair_order(self.nodes):
            raise ValueError("unknown pair")
        if edge_pair in self.queried:
            raise ValueError("duplicate query")
        if answer not in STATES:
            raise ValueError("invalid expert answer")
        self.queried.add(edge_pair)
        self.query_count += 1
        before = dict(self.relations)
        desired = NO_EDGE if answer == NO_EDGE else edge_pair if answer == U_TO_V else (edge_pair[1], edge_pair[0])
        self._try_apply(edge_pair, desired)
        self.history.append({"pair": edge_pair, "answer": answer, "before": before.get(edge_pair, NO_EDGE),
                             "desired": desired, "error_discovered_at_query": before.get(edge_pair, NO_EDGE) != desired,
                             "pending": edge_pair in self.pending})
        self.retry_pending()

    def _try_apply(self, p: tuple[str, str], desired: object) -> bool:
        trial = dict(self.relations)
        if desired == NO_EDGE:
            trial.pop(p, None)
        else:
            trial[p] = desired
        if not graph_dag(self.nodes, trial):
            self.pending[p] = desired
            return False
        if trial != self.relations:
            self.relations = trial
            self.edits += 1
        self.pending.pop(p, None)
        return True

    def retry_pending(self) -> None:
        for p in sorted(tuple(self.pending)):
            self._try_apply(p, self.pending[p])


def query_once(state: VerificationState, policy: str, budget: int, expert: Callable,
               score_context: dict | None = None, rng: np.random.Generator | None = None) -> list[dict]:
    if budget < 0 or state.query_count > budget:
        raise ValueError("invalid query budget")
    trace = []
    while state.query_count < budget:
        candidates = [p for p in pair_order(state.nodes) if p not in state.queried]
        if not candidates:
            break
        if policy == "RANDOM_VERIFICATION":
            if rng is None:
                raise ValueError("random policy requires explicit RNG")
            p = candidates[int(rng.integers(0, len(candidates)))]
        else:
            scored = score_pairs(policy, **(score_context or {}), relations=state.relations)
            by_pair = {r["pair"]: r for r in scored}
            # Query even a zero-score candidate; deterministic lexical tie-break.
            p = min(candidates, key=lambda pair: (-by_pair.get(pair, {"score": 0.0})["score"], pair))
        answer = expert(p)
        if answer not in STATES:
            raise ValueError("expert returned an invalid relation state")
        state.apply_answer(p, answer)
        trace.append({"pair": p, "answer": answer, "score": next((r["score"] for r in scored if r["pair"] == p), None) if policy != "RANDOM_VERIFICATION" else None})
    return trace
