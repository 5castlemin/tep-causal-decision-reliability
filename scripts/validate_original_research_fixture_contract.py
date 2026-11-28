"""Deterministic hand-DAG checks for the unapproved original-research contract.

Fixture-only: creates no SCM coefficients, observations, interventions, regret, or
estimated cost weights. Run: python scripts/validate_original_research_fixture_contract.py
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

UNRES = "UNRESOLVED"
NODES = ("X", "A", "B", "Y", "T", "U", "P", "Q", "R", "S")
GT = {("X", "A"), ("A", "Y"), ("X", "B"), ("B", "Y"), ("T", "U"), ("P", "Q")}
INITIAL = {("A", "Y"), ("X", "B"), ("B", "Y"), ("Q", "P"), ("R", "S")}
TASK_PAIRS = {frozenset(e) for e in (("X", "A"), ("A", "Y"), ("X", "B"), ("B", "Y"))}
TASK_NODES = {"X", "A", "B", "Y"}
ORDER = ("M1", "M2", "M3", "M4")


def pair(u: str, v: str) -> frozenset[str]:
    return frozenset((u, v))


def estimate_state(edges: set[tuple[str, str]]) -> dict[frozenset[str], tuple[str, str] | str]:
    return {pair(u, v): (u, v) for u, v in edges}


def is_dag(edges: set[tuple[str, str]]) -> bool:
    nodes = {n for edge in edges for n in edge}
    indegree = {n: 0 for n in nodes}
    children = {n: [] for n in nodes}
    for u, v in edges:
        if u == v:
            return False
        children[u].append(v)
        indegree[v] += 1
    queue = [n for n, d in indegree.items() if d == 0]
    visited = 0
    while queue:
        u = queue.pop()
        visited += 1
        for v in children[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    return visited == len(nodes)


def directed_edges(states: dict[frozenset[str], tuple[str, str] | str]) -> set[tuple[str, str]]:
    return {state for state in states.values() if state != UNRES}


def fp_is_task(fp: frozenset[str], rule: str, task_nodes: set[str], route_relevant: set[frozenset[str]]) -> bool:
    internal = fp <= task_nodes
    if rule == "A":
        return internal
    if rule == "B":
        return internal or (len(fp & task_nodes) == 1 and fp in route_relevant)
    raise ValueError(rule)


def calculate(gt: set[tuple[str, str]], states: dict[frozenset[str], tuple[str, str] | str],
              task_pairs: set[frozenset[str]], task_nodes: set[str], rule: str = "A",
              route_relevant: set[frozenset[str]] | None = None) -> dict[str, object]:
    route_relevant = route_relevant or set()
    gt_by_pair = {pair(u, v): (u, v) for u, v in gt}
    all_pairs = set(gt_by_pair) | set(states)
    buckets: list[str] = []
    off_true = 0
    off_pred = 0
    m1_fn = m2_fp = m3_rev = m3_unres = m3_correct = 0
    m4 = {"FN": 0, "FP": 0, "REV": 0, "UNRES": 0}
    m4_support = {"FN": 0, "FP": 0, "REV": 0, "UNRES": 0}
    event_assignments: dict[frozenset[str], str] = {}
    for p in all_pairs:
        truth = gt_by_pair.get(p)
        estimate = states.get(p)
        task_true = p in task_pairs
        if estimate is not None and not task_true:
            if truth is not None or not fp_is_task(p, rule, task_nodes, route_relevant):
                off_pred += 1
        if truth is not None:
            if not task_true:
                off_true += 1
            else:
                m4_support["FN"] += 1
                if estimate is not None:
                    m4_support["FP"] += 1
            if estimate is None:
                bucket = "M4-FN" if task_true else "M1-FN"
                if task_true:
                    m4["FN"] += 1
                else:
                    m1_fn += 1
            elif estimate == UNRES:
                bucket = "M4-UNRES" if task_true else "M3-UNRES"
                if task_true:
                    m4["UNRES"] += 1
                    m4_support["UNRES"] += 1
                else:
                    m3_unres += 1
            elif estimate == truth:
                if task_true:
                    m4_support["REV"] += 1
                    m4_support["UNRES"] += 1
                else:
                    m3_correct += 1
                continue
            else:
                bucket = "M4-REV" if task_true else "M3-REV"
                if task_true:
                    m4["REV"] += 1
                    m4_support["REV"] += 1
                    m4_support["UNRES"] += 1
                else:
                    m3_rev += 1
            buckets.append(bucket)
            event_assignments[p] = bucket
        elif estimate is not None:
            task_fp = fp_is_task(p, rule, task_nodes, route_relevant)
            if task_fp:
                m4["FP"] += 1
                m4_support["FP"] += 1
                buckets.append("M4-FP")
                event_assignments[p] = "M4-FP"
            else:
                m2_fp += 1
                buckets.append("M2-FP")
                event_assignments[p] = "M2-FP"
        else:
            continue
    m3_oriented = m3_correct + m3_rev
    m3_matched = m3_oriented + m3_unres
    return {
        "M1": (m1_fn, off_true),
        "M2": (m2_fp, off_pred),
        "M3_acc": (m3_correct, m3_oriented),
        "M3_unresolved": (m3_unres, m3_matched),
        "M3_error_count": m3_rev + m3_unres,
        "M4": m4,
        "M4_support": m4_support,
        "buckets": buckets,
        "event_assignments": event_assignments,
    }


@dataclass(frozen=True)
class Edit:
    name: str
    metric: str
    p: frozenset[str]
    target_state: tuple[str, str] | str | None
    cost: int


def apply_edit(states: dict[frozenset[str], tuple[str, str] | str], edit: Edit) -> dict[frozenset[str], tuple[str, str] | str]:
    updated = dict(states)
    if edit.target_state is None:
        updated.pop(edit.p, None)
    else:
        updated[edit.p] = edit.target_state
    return updated


def residuals(stats: dict[str, object], initial: dict[str, object], beta: tuple[float, float, float, float] | None = None) -> dict[str, float]:
    counts = stats["M4"]
    initial_counts = initial["M4"]
    active = [kind for kind in ("FN", "FP", "REV", "UNRES") if initial_counts[kind] > 0]
    if len(active) == 1:
        m4_remaining = counts[active[0]] / initial_counts[active[0]]
    elif not active:
        m4_remaining = 0.0
    elif beta is None:
        raise ValueError("M4 has multiple active event components; a user-approved beta is required")
    else:
        weights = dict(zip(("FN", "FP", "REV", "UNRES"), beta))
        active_weight = sum(weights[k] for k in active)
        if active_weight <= 0:
            raise ValueError("M4 active component beta mass must be positive")
        m4_remaining = sum((weights[k] / active_weight) * counts[k] / initial_counts[k] for k in active)
    return {
        "M1": stats["M1"][0] / initial["M1"][0] if initial["M1"][0] else 0.0,
        "M2": stats["M2"][0] / initial["M2"][0] if initial["M2"][0] else 0.0,
        "M3": stats["M3_error_count"] / initial["M3_error_count"] if initial["M3_error_count"] else 0.0,
        "M4": m4_remaining,
    }


def fixed_opportunity_gains(before: dict[str, object], after: dict[str, object], beta: tuple[float, float, float, float] | None = None) -> dict[str, float]:
    # Denominators are captured at G0 and held fixed for scheduler utility.
    active = [kind for kind in ("FN", "FP", "REV", "UNRES") if before["M4"][kind] > 0]
    if len(active) == 1:
        kind = active[0]
        denom = before["M4_support"][kind]
        m4_gain = (before["M4"][kind] - after["M4"][kind]) / denom if denom else 0.0
    elif not active:
        m4_gain = 0.0
    elif beta is None:
        raise ValueError("M4 has multiple active event components; a user-approved beta is required")
    else:
        weights = dict(zip(("FN", "FP", "REV", "UNRES"), beta))
        active_weight = sum(weights[k] for k in active)
        if active_weight <= 0:
            raise ValueError("M4 active component beta mass must be positive")
        m4_gain = sum((weights[k] / active_weight) * (before["M4"][k] - after["M4"][k]) / before["M4_support"][k] for k in active if before["M4_support"][k])
    return {
        "M1": (before["M1"][0] - after["M1"][0]) / before["M1"][1] if before["M1"][1] else 0.0,
        "M2": (before["M2"][0] - after["M2"][0]) / before["M2"][1] if before["M2"][1] else 0.0,
        "M3": (before["M3_error_count"] - after["M3_error_count"]) / before["M1"][1] if before["M1"][1] else 0.0,
        "M4": m4_gain,
    }


def candidate_gain(current: dict[frozenset[str], tuple[str, str] | str], edit: Edit, gt: set[tuple[str, str]],
                   task_pairs: set[frozenset[str]], task_nodes: set[str], initial_stats: dict[str, object],
                   beta: tuple[float, float, float, float] | None, subset: tuple[str, ...]) -> tuple[float, bool]:
    updated = apply_edit(current, edit)
    if not is_dag(directed_edges(updated)):
        return 0.0, False
    now = calculate(gt, updated, task_pairs, task_nodes)
    before_u = residuals(calculate(gt, current, task_pairs, task_nodes), initial_stats, beta)
    after_u = residuals(now, initial_stats, beta)
    return sum(before_u[m] - after_u[m] for m in subset) / len(subset), True


def select_candidate(current: dict[frozenset[str], tuple[str, str] | str], candidates: tuple[Edit, ...],
                     score, cost_left: int) -> tuple[Edit | None, tuple[str, ...]]:
    feasible = []
    rejected = []
    for op in candidates:
        trial = apply_edit(current, op)
        if not is_dag(directed_edges(trial)):
            rejected.append(op.name)
            continue
        if op.cost > cost_left:
            continue
        gain = score(op, trial)
        if gain > 0:
            feasible.append((gain / op.cost, op.name, op))
    return (max(feasible, key=lambda row: (row[0], row[1]))[2] if feasible else None, tuple(rejected))


def policy_candidates() -> tuple[Edit, ...]:
    return (
        Edit("add:T->U", "M1", pair("T", "U"), ("T", "U"), 1),
        Edit("delete:R-S", "M2", pair("R", "S"), None, 1),
        Edit("orient:Q->P", "M3", pair("Q", "P"), ("P", "Q"), 1),
        Edit("add:X->A", "M4", pair("X", "A"), ("X", "A"), 1),
    )


def schedule_a(subset: tuple[str, ...], budget: int, costs: dict[str, int]) -> tuple[str, ...]:
    if not subset or budget == 0:
        return ()
    base, rem = divmod(budget, len(subset))
    quota = {m: base for m in subset}
    for m in ORDER:
        if m in quota and rem:
            quota[m] += 1
            rem -= 1
    available_cost = budget
    selected = []
    for m in ORDER:
        if quota.get(m, 0) and costs[m] <= available_cost:
            selected.append(m)
            available_cost -= costs[m]
    return tuple(selected)


def schedule_b(subset: tuple[str, ...], budget: int, costs: dict[str, int], gains: dict[str, float]) -> tuple[str, ...]:
    left = set(subset)
    selected = []
    spent = 0
    while left:
        candidates = [m for m in ORDER if m in left and costs[m] + spent <= budget and gains[m] > 0]
        if not candidates:
            break
        best = max(candidates, key=lambda m: (gains[m] / costs[m], -ORDER.index(m)))
        selected.append(best)
        spent += costs[best]
        left.remove(best)
    return tuple(selected)


def trajectory(metrics: tuple[str, ...], states: dict[frozenset[str], tuple[str, str] | str], edits: dict[str, Edit]) -> tuple[frozenset[tuple[str, str]], ...]:
    current = dict(states)
    path = [frozenset(directed_edges(current))]
    for m in metrics:
        current = apply_edit(current, edits[m])
        path.append(frozenset(directed_edges(current)))
    return tuple(path)


def main() -> None:
    initial_states = estimate_state(INITIAL)
    initial = calculate(GT, initial_states, TASK_PAIRS, TASK_NODES)
    assert initial["M1"] == (1, 2)
    assert initial["M2"] == (1, 2)
    assert initial["M3_acc"] == (0, 1)
    assert initial["M3_unresolved"] == (0, 1)
    assert initial["M4"] == {"FN": 1, "FP": 0, "REV": 0, "UNRES": 0}
    assert calculate(GT, apply_edit(initial_states, policy_candidates()[0]), TASK_PAIRS, TASK_NODES)["M2"] == (1, 3)

    # Real unresolved state: reverse one edge, then change only that state to UNRES.
    gt_c = {("A", "B"), ("C", "D")}
    states_c = {pair("A", "B"): ("B", "A"), pair("C", "D"): ("C", "D")}
    before = calculate(gt_c, states_c, set(), set())
    states_c[pair("A", "B")] = UNRES
    after = calculate(gt_c, states_c, set(), set())
    assert before["M3_acc"] == (1, 2) and before["M3_unresolved"] == (0, 2)
    assert after["M3_acc"] == (1, 1) and after["M3_unresolved"] == (1, 2)
    resolved_states = dict(states_c)
    resolved_states[pair("A", "B")] = ("A", "B")
    resolved = calculate(gt_c, resolved_states, set(), set())
    assert resolved["M3_acc"] == (2, 2) and resolved["M3_unresolved"] == (0, 2)
    deleted_states = dict(states_c)
    deleted_states.pop(pair("A", "B"))
    deleted = calculate(gt_c, deleted_states, set(), set())
    assert deleted["M1"][0] == 1 and deleted["M3_unresolved"] == (0, 1)

    # M4 input calculator: internal FP, REV, UNRES, plus a boundary FP under A/B.
    gt4 = {("X", "M"), ("M", "Y"), ("X", "A"), ("A", "Y"), ("Z", "X"), ("Z", "Y"), ("W", "M")}
    task4 = {pair("X", "M"), pair("M", "Y"), pair("X", "A"), pair("A", "Y"), pair("Z", "X"), pair("Z", "Y")}
    task_nodes4 = {"X", "M", "Y", "A", "Z"}
    est4 = estimate_state({("X", "M"), ("M", "Y"), ("Y", "A"), ("Z", "X"), ("Z", "Y"), ("W", "M"), ("X", "Y"), ("W", "X")})
    est4[pair("X", "M")] = UNRES
    route_fp = {pair("W", "X")}  # hand-checked open X<-W->M->Y boundary backdoor
    a4 = calculate(gt4, est4, task4, task_nodes4, "A", route_fp)
    b4 = calculate(gt4, est4, task4, task_nodes4, "B", route_fp)
    assert a4["M4"] == {"FN": 1, "FP": 1, "REV": 1, "UNRES": 1}
    assert b4["M4"] == {"FN": 1, "FP": 2, "REV": 1, "UNRES": 1}
    assert a4["buckets"].count("M4-FP") == 1 and a4["buckets"].count("M2-FP") == 1
    assert b4["buckets"].count("M4-FP") == 2 and b4["buckets"].count("M2-FP") == 0
    assert len(a4["event_assignments"]) == len(set(a4["event_assignments"]))
    assert len(b4["event_assignments"]) == len(set(b4["event_assignments"]))
    allowed_buckets = {"M1-FN", "M2-FP", "M3-REV", "M3-UNRES", "M4-FN", "M4-FP", "M4-REV", "M4-UNRES"}
    assert set(a4["event_assignments"].values()) <= allowed_buckets
    assert set(b4["event_assignments"].values()) <= allowed_buckets
    assert a4["event_assignments"][pair("X", "Y")] == "M4-FP"
    assert a4["event_assignments"][pair("W", "X")] == "M2-FP"
    assert b4["event_assignments"][pair("W", "X")] == "M4-FP"
    assert pair("M", "Y") not in a4["event_assignments"]  # correctly estimated adjacency is not an error
    assert pair("R", "S") not in a4["event_assignments"]  # both absent is not an error event

    # The A/B difference for boundary W->X is a tag change, not a change to GT.
    assert fp_is_task(pair("W", "X"), "A", task_nodes4, route_fp) is False
    assert fp_is_task(pair("W", "X"), "B", task_nodes4, route_fp) is True

    # Greedy gains come from the actual before/after event counts, normalized by
    # initial error counts. Fixture-only beta; no research beta is approved here.
    candidates = policy_candidates()
    beta_fixture_only = None  # M4 has only one active component (FN) in this scheduler fixture.
    gains = {}
    for edit in candidates:
        gain, valid = candidate_gain(initial_states, edit, GT, TASK_PAIRS, TASK_NODES, initial, beta_fixture_only, (edit.metric,))
        assert valid and gain > 0
        gains[edit.metric] = gain
    assert gains == {"M1": 1.0, "M2": 1.0, "M3": 1.0, "M4": 1.0}

    # Fixed opportunity-denominator gains are separately derived; they differ.
    fixed_stats = {
        edit.metric: calculate(GT, apply_edit(initial_states, edit), TASK_PAIRS, TASK_NODES)
        for edit in candidates
    }
    opportunity = {
        edit.metric: fixed_opportunity_gains(initial, fixed_stats[edit.metric], beta_fixture_only)[edit.metric]
        for edit in candidates
    }
    assert opportunity == {"M1": 0.5, "M2": 0.5, "M3": 0.5, "M4": 0.25}
    assert opportunity != gains

    subsets = [tuple(s) for k in range(1, 5) for s in combinations(ORDER, k)]
    assert len(subsets) == 15
    edits_by_metric = {edit.metric: edit for edit in candidates}
    all_subsets = [(), *subsets]
    assert len(all_subsets) == 16
    print("PASS metric cases: M1/M2/M3/M4 numerators and denominators from graph states")
    print("PASS M3 reversed->UNRES: accuracy 1/2->1/1; unresolved 0/2->1/2; resolve and delete state transitions checked")
    print("PASS M4 vector from graph: FN=1, internal FP=1, REV=1, UNRES=1; boundary FP A/B tag differs")
    print(f"DERIVED_GAINS initial-error-count normalization: {gains}")
    print(f"DERIVED_GAINS fixed-opportunity normalization: {opportunity}")
    print("M4 scalarization was not needed: this scheduler fixture has only M4-FN active; multi-component beta remains OPEN.")

    for norm_name, gain_map in (("initial_error_count", gains), ("fixed_opportunity", opportunity)):
        print(f"NORMALIZATION={norm_name}")
        for budget in range(5):
            costs = {"M1": 1, "M2": 1, "M3": 1, "M4": 1}
            out_a = [schedule_a(s, budget, costs) for s in all_subsets]
            out_b = [schedule_b(s, budget, costs, gain_map) for s in all_subsets]
            graph_a = [trajectory(seq, initial_states, edits_by_metric)[-1] for seq in out_a]
            graph_b = [trajectory(seq, initial_states, edits_by_metric)[-1] for seq in out_b]
            path_a = [trajectory(seq, initial_states, edits_by_metric) for seq in out_a]
            path_b = [trajectory(seq, initial_states, edits_by_metric) for seq in out_b]
            print(f"B={budget}: unique_final_A={len(set(graph_a))}/16 unique_final_B={len(set(graph_b))}/16 same_subset_final={sum(x == y for x, y in zip(graph_a, graph_b))}/16 same_subset_path={sum(x == y for x, y in zip(path_a, path_b))}/16")

    assert schedule_a(ORDER, 1, {m: 1 for m in ORDER}) == ("M1",)
    assert schedule_b(ORDER, 1, {m: 1 for m in ORDER}, gains) == ("M1",)
    # S15=B1=S1 for quota A; nontrivial quota/greedy differences are evaluated above.
    assert trajectory(schedule_a(ORDER, 1, {m: 1 for m in ORDER}), initial_states, edits_by_metric)[-1] == trajectory(schedule_a(("M1",), 1, {m: 1 for m in ORDER}), initial_states, edits_by_metric)[-1]
    for budget in range(5):
        for orientation_cost in (1, 2, 3):
            scenario_costs = {"M1": 1, "M2": 1, "M3": orientation_cost, "M4": 1}
            for subset in all_subsets:
                selected_a = schedule_a(subset, budget, scenario_costs)
                selected_b = schedule_b(subset, budget, scenario_costs, gains)
                assert sum(scenario_costs[m] for m in selected_a) <= budget
                assert sum(scenario_costs[m] for m in selected_b) <= budget
    assert schedule_b(("M3",), 1, {**{m: 1 for m in ORDER}, "M3": 2}, gains) == ()
    assert schedule_b(("M3",), 2, {**{m: 1 for m in ORDER}, "M3": 2}, gains) == ("M3",)
    assert schedule_b(("M3",), 2, {**{m: 1 for m in ORDER}, "M3": 3}, gains) == ()
    assert schedule_b(("M3",), 3, {**{m: 1 for m in ORDER}, "M3": 3}, gains) == ("M3",)

    # Multiple same-metric candidates: choose from real event reductions per cost.
    multi_gt = {("T", "U"), ("P", "Q"), ("V", "W")}
    multi_initial = {("P", "Q")}  # two independent missing M1 edges
    multi_nodes = {"T", "U", "P", "Q", "V", "W"}
    multi_task = set()
    multi_states = estimate_state(multi_initial)
    multi_stats = calculate(multi_gt, multi_states, multi_task, set())
    multi_ops = [Edit("add:T-U", "M1", pair("T", "U"), ("T", "U"), 1), Edit("add:V-W", "M1", pair("V", "W"), ("V", "W"), 2)]
    def multi_score(op: Edit, candidate_states: dict[frozenset[str], tuple[str, str] | str]) -> float:
        after_stats = calculate(multi_gt, candidate_states, multi_task, set())
        return (multi_stats["M1"][0] - after_stats["M1"][0]) / multi_stats["M1"][0]

    selected, rejected = select_candidate(multi_states, tuple(multi_ops), multi_score, 2)
    assert selected is not None and selected.name == "add:T-U" and rejected == ()

    # Distinguish cycle detection from policy-level candidate rejection.
    cycle_gt = {("Y", "X"), ("T", "U")}
    cycle_est = estimate_state({("X", "B"), ("B", "Y")})
    cycle_candidate = Edit("add:Y->X", "M1", pair("X", "Y"), ("Y", "X"), 1)
    safe_candidate = Edit("add:T->U", "M1", pair("T", "U"), ("T", "U"), 1)
    proposed = apply_edit(cycle_est, cycle_candidate)
    assert not is_dag(directed_edges(proposed))  # graph detector
    cycle_stats = calculate(cycle_gt, cycle_est, set(), set())
    def cycle_score(op: Edit, trial: dict[frozenset[str], tuple[str, str] | str]) -> float:
        after_stats = calculate(cycle_gt, trial, set(), set())
        return (cycle_stats["M1"][0] - after_stats["M1"][0]) / cycle_stats["M1"][0]
    selected_cycle_safe, cycle_rejections = select_candidate(cycle_est, (cycle_candidate, safe_candidate), cycle_score, 1)
    assert cycle_rejections == ("add:Y->X",) and selected_cycle_safe == safe_candidate
    print("PASS multiple same-type candidates: actual Δerror/cost selects cheaper equal-benefit repair")
    print("PASS cycle detector rejects cyclic graph; scheduler rejects it and selects a feasible positive-gain repair")
    print("PASS B=0..4 cost caps with c_ori=1,2,3; unaffordable orientation edits are not selected")

    # Error-count vs fixed-opportunity normalization can reverse the chosen metric.
    outside_truth = {(f"O{i}", f"P{i}") for i in range(10)}
    task_truth = {("X", "M"), ("M", "Y"), ("X", "Y")}
    norm_gt = outside_truth | task_truth
    norm_est_edges = {(f"O{i}", f"P{i}") for i in range(1, 10)} | {("X", "Y")}
    norm_est = estimate_state(norm_est_edges)
    norm_task = {pair(*e) for e in task_truth}
    norm_task_nodes = {"X", "M", "Y"}
    norm_stats = calculate(norm_gt, norm_est, norm_task, norm_task_nodes)
    assert norm_stats["M1"] == (1, 10)
    assert norm_stats["M4"]["FN"] == 2
    # One M1 FN versus two M4 FN, using beta_FN=1 only for this didactic fixture.
    norm_beta_fixture = None  # only M4-FN is active in this fixture
    m1_op = Edit("add:O0->P0", "M1", pair("O0", "P0"), ("O0", "P0"), 1)
    m4_op = Edit("add:X->M", "M4", pair("X", "M"), ("X", "M"), 1)
    initial_error_gain = {
        "M1": candidate_gain(norm_est, m1_op, norm_gt, norm_task, norm_task_nodes, norm_stats, norm_beta_fixture, ("M1",))[0],
        "M4": candidate_gain(norm_est, m4_op, norm_gt, norm_task, norm_task_nodes, norm_stats, norm_beta_fixture, ("M4",))[0],
    }
    norm_after_m1 = calculate(norm_gt, apply_edit(norm_est, Edit("add:O0->P0", "M1", pair("O0", "P0"), ("O0", "P0"), 1)), norm_task, norm_task_nodes)
    norm_after_m4 = calculate(norm_gt, apply_edit(norm_est, Edit("add:X->M", "M4", pair("X", "M"), ("X", "M"), 1)), norm_task, norm_task_nodes)
    norm_fixed = {
        "M1": fixed_opportunity_gains(norm_stats, norm_after_m1, norm_beta_fixture)["M1"],
        "M4": fixed_opportunity_gains(norm_stats, norm_after_m4, norm_beta_fixture)["M4"],
    }
    assert initial_error_gain == {"M1": 1.0, "M4": 0.5}
    assert max(initial_error_gain, key=initial_error_gain.get) == "M1"
    assert norm_fixed == {"M1": 0.1, "M4": 1 / 3}
    assert max(norm_fixed, key=norm_fixed.get) == "M4"
    print(f"NORMALIZATION_COUNTEREXAMPLE initial_error={initial_error_gain} fixed_opportunity={norm_fixed}; selected M1 vs M4 (only M4-FN active; no beta scalarization)")
    print("No SCM, observations, interventions, Decision Regret, or fitted cost weights generated.")


if __name__ == "__main__":
    main()
