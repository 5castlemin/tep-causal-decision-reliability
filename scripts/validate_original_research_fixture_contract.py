"""Small deterministic DAG and metric arithmetic checks for the proposed contract.

This is not a research runner and creates no SCM, observational data, intervention,
or regret outcomes. Run with Python 3.11: python scripts/validate_original_research_fixture_contract.py
"""

from __future__ import annotations

from itertools import combinations


NODES = ("X", "A", "B", "Y", "T", "U", "P", "Q", "R", "S")
GT = {("X", "A"), ("A", "Y"), ("X", "B"), ("B", "Y"), ("T", "U"), ("P", "Q")}
INITIAL = {("A", "Y"), ("X", "B"), ("B", "Y"), ("Q", "P"), ("R", "S")}
TASK_PAIRS = {frozenset(p) for p in (("X", "A"), ("A", "Y"), ("X", "B"), ("B", "Y"))}
ORDER = ("M1", "M2", "M3", "M4")
GAINS = {"M1": 0.5, "M2": 0.5, "M3": 1.0, "M4": 0.25}


def is_dag(edges: set[tuple[str, str]]) -> bool:
    indegree = {n: 0 for n in NODES}
    children = {n: [] for n in NODES}
    for u, v in edges:
        if u == v or u not in indegree or v not in indegree:
            return False
        children[u].append(v)
        indegree[v] += 1
    queue = [n for n, d in indegree.items() if d == 0]
    seen = 0
    while queue:
        u = queue.pop()
        seen += 1
        for v in children[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    return seen == len(NODES)


def apply(metric: str, edges: set[tuple[str, str]]) -> set[tuple[str, str]]:
    result = set(edges)
    if metric == "M1":
        result.add(("T", "U"))
    elif metric == "M2":
        result.remove(("R", "S"))
    elif metric == "M3":
        result.remove(("Q", "P"))
        result.add(("P", "Q"))
    elif metric == "M4":
        result.add(("X", "A"))
    else:
        raise ValueError(metric)
    return result


def original_metrics(edges: set[tuple[str, str]]) -> dict[str, tuple[int, int] | tuple[int, int, int]]:
    # Adjacency is scored on unordered pairs; the estimate direction is retained.
    gt_pairs = {frozenset(e) for e in GT}
    est_pairs = {frozenset(e) for e in edges}
    off_gt = gt_pairs - TASK_PAIRS
    off_est = est_pairs - TASK_PAIRS
    off_missing = off_gt - off_est
    off_fp = off_est - off_gt
    off_correct = sum(1 for pair in off_gt & off_est if next(e for e in edges if frozenset(e) == pair) in GT)
    off_reversed = sum(1 for pair in off_gt & off_est if next(e for e in edges if frozenset(e) == pair) not in GT)
    off_unresolved = 0  # this fixture encodes directed edges only
    return {
        "M1": (len(off_missing), len(off_gt)),
        "M2": (len(off_fp), len(off_est)),
        "M3_acc": (off_correct, off_correct + off_reversed),
        "M3_unresolved": (off_unresolved, len(off_gt & off_est)),
        "M4": (len(TASK_PAIRS - est_pairs), 0, 0, 0),
    }


def schedule_a(subset: tuple[str, ...], budget: int, orientation_cost: int) -> tuple[str, ...]:
    if not subset or budget == 0:
        return ()
    slots = budget  # reference cost is 1; actual operation costs remain a separate cap
    base, remainder = divmod(slots, len(subset))
    quota = {m: base for m in subset}
    for metric in ORDER:
        if metric in quota and remainder:
            quota[metric] += 1
            remainder -= 1
    applied: list[str] = []
    spent = 0
    for metric in ORDER:
        for _ in range(quota.get(metric, 0)):
            cost = orientation_cost if metric == "M3" else 1
            if metric not in applied and spent + cost <= budget:
                applied.append(metric)
                spent += cost
    return tuple(applied)


def schedule_b(subset: tuple[str, ...], budget: int, orientation_cost: int) -> tuple[str, ...]:
    remaining = set(subset)
    selected: list[str] = []
    spent = 0
    while remaining:
        affordable = [m for m in ORDER if m in remaining and spent + (orientation_cost if m == "M3" else 1) <= budget]
        if not affordable:
            break
        # U_S is the mean of initial-error-count-normalized residual burdens; the common 1/|S| factor
        # cancels for ranking candidates within a fixed subset.
        metric = max(affordable, key=lambda m: (GAINS[m] / (orientation_cost if m == "M3" else 1), -ORDER.index(m)))
        selected.append(metric)
        spent += orientation_cost if metric == "M3" else 1
        remaining.remove(metric)
    return tuple(selected)


def main() -> None:
    assert is_dag(GT) and is_dag(INITIAL)
    for metric in ORDER:
        fixed = apply(metric, INITIAL)
        assert is_dag(fixed), metric

    m0 = original_metrics(INITIAL)
    assert m0["M1"] == (1, 2)
    assert m0["M2"] == (1, 2)
    assert m0["M3_acc"] == (0, 1)
    assert m0["M3_unresolved"] == (0, 1)
    assert m0["M4"] == (1, 0, 0, 0)

    after_m1 = original_metrics(apply("M1", INITIAL))
    assert after_m1["M1"] == (0, 2)
    assert after_m1["M2"] == (1, 3)  # same FP numerator, larger denominator
    after_m2 = original_metrics(apply("M2", INITIAL))
    assert after_m2["M2"] == (0, 1)  # an FP is actually removed
    after_m3 = original_metrics(apply("M3", INITIAL))
    assert after_m3["M3_acc"] == (1, 1)

    # Conditional direction accuracy can rise when a reversal becomes unresolved.
    acc_before = 1 / (1 + 1)
    acc_after = 1 / (1 + 0)
    unresolved_after = 1 / (1 + 0 + 1)
    assert (acc_before, acc_after, unresolved_after) == (0.5, 1.0, 0.5)

    # Mutually exclusive per-event assignment; a false pair gets one tag under
    # either A or B, never both. Correct pairs are not error events.
    error_buckets = ["M1", "M2", "M3-REV", "M4-FN"]
    assert len(error_buckets) == len(set(error_buckets)) == 4
    fp_bucket_a = "M2"  # outside endpoint pair under A
    fp_bucket_b = "M4-FP"  # same candidate if B's route criterion is satisfied
    assert fp_bucket_a != fp_bucket_b

    subsets = [tuple(s) for k in range(1, 5) for s in combinations(ORDER, k)]
    assert len(subsets) == 15 and len(set(subsets)) == 15
    assert schedule_a(ORDER, 1, 1) == schedule_a(("M1",), 1, 1) == ("M1",)
    assert _apply_sequence(schedule_a(ORDER, 1, 1)) != _apply_sequence(schedule_b(ORDER, 1, 1))
    assert schedule_a(ORDER, 0, 1) == ()
    assert schedule_b(ORDER, 0, 1) == ()
    for schedule in (schedule_a, schedule_b):
        for subset in [(), *subsets]:
            for budget in range(5):
                for orientation_cost in (1, 2, 3):
                    seq = schedule(subset, budget, orientation_cost)
                    assert is_dag(_apply_sequence(seq)), (schedule.__name__, subset, budget, orientation_cost, seq)
    # A deliberately cyclic proposal must be rejected before it becomes a state.
    assert not is_dag(set(INITIAL) | {("Y", "X")})
    assert "M3" not in schedule_b(("M3",), 1, 2)
    assert "M3" in schedule_b(("M3",), 2, 2)
    assert "M3" not in schedule_b(("M3",), 2, 3)
    assert "M3" in schedule_b(("M3",), 3, 3)

    print("PASS: four-metric fixture fractions, M2 denominator guard, M3 unresolved counterexample")
    print("PASS: 15 subsets + no-edit; DAG-valid repairs for all A quotas and B greedies at B=0..4, c_ori=1..3")
    print("PASS: S15 and S1 quota-A final graph coincide at B=1; orientation affordability respects cost cap")
    for budget in range(5):
        for schedule in (schedule_a, schedule_b):
            trajectories = [frozenset(_apply_sequence(schedule(s, budget, 1))) for s in [(), *subsets]]
            print(f"TRAJECTORY_UNIQUENESS {schedule.__name__} B={budget}: {len(set(trajectories))}/16 distinct final graphs")
            ordered = [_trajectory(schedule(s, budget, 1)) for s in [(), *subsets]]
            print(f"ORDERED_PATH_UNIQUENESS {schedule.__name__} B={budget}: {len(set(ordered))}/16 distinct trajectories")
        a_trajectories = [frozenset(_apply_sequence(schedule_a(s, budget, 1))) for s in [(), *subsets]]
        b_trajectories = [frozenset(_apply_sequence(schedule_b(s, budget, 1))) for s in [(), *subsets]]
        same_policy_pair = sum(a == b for a, b in zip(a_trajectories, b_trajectories))
        print(f"A_B_SAME_SUBSET_FINAL_GRAPH B={budget}: {same_policy_pair}/16")
        a_paths = [_trajectory(schedule_a(s, budget, 1)) for s in [(), *subsets]]
        b_paths = [_trajectory(schedule_b(s, budget, 1)) for s in [(), *subsets]]
        same_path_pair = sum(a == b for a, b in zip(a_paths, b_paths))
        print(f"A_B_SAME_SUBSET_TRAJECTORY B={budget}: {same_path_pair}/16")
    print("No SCM, observations, intervention effects, Decision Regret, or fitted costs generated.")


def _apply_sequence(sequence: tuple[str, ...]) -> set[tuple[str, str]]:
    edges = set(INITIAL)
    for metric in sequence:
        edges = apply(metric, edges)
    return edges


def _trajectory(sequence: tuple[str, ...]) -> tuple[frozenset[tuple[str, str]], ...]:
    edges = set(INITIAL)
    states = [frozenset(edges)]
    for metric in sequence:
        edges = apply(metric, edges)
        states.append(frozenset(edges))
    return tuple(states)


if __name__ == "__main__":
    main()
