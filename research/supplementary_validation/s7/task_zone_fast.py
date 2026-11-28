"""Exact reachability implementation of the frozen Research C task-zone rule.

This module is an isolated feasibility candidate. It does not modify or replace
research.original_objective.policy_engine.task_zone.
"""
from __future__ import annotations
from collections import deque
import time

def task_zone_fast(truth, action: str, target: str, *, max_seconds: float|None=None):
    if action == target:
        raise ValueError("Action and target must differ")
    edges={e for e in truth.values() if e!="UNRES"}
    nodes={x for e in edges for x in e}
    undirected={n:set() for n in nodes}
    children={n:set() for n in nodes}
    parents={n:set() for n in nodes}
    for u,v in edges:
        undirected[u].add(v);undirected[v].add(u)
        children[u].add(v);parents[v].add(u)
    if action not in undirected or target not in undirected:
        return set(),{action,target}

    # Directed action-to-target paths: edge lies on such a path iff its tail
    # is reachable from action and its head can reach target.
    def closure(starts, adjacency):
        seen=set(starts);q=deque(starts)
        while q:
            u=q.popleft()
            for v in adjacency.get(u,()):
                if v not in seen:seen.add(v);q.append(v)
        return seen
    from_action=closure([action],children)
    to_target=closure([target],parents)
    selected={tuple(sorted((u,v))) for u,v in edges if u in from_action and v in to_target}

    # Backdoor paths begin with an arrow into action and have no collider.
    # Build the finite state graph first and use reverse reachability to prune
    # prefixes that cannot terminate at target. Then enumerate only simple,
    # collider-free prefixes, matching the frozen DFS's path semantics.
    states={(u,v) for u,v in edges}|{(v,u) for u,v in edges}
    nexts={s:set() for s in states};prevs={s:set() for s in states}
    for u,v in states:
        if v==target:continue
        for w in undirected[v]:
            collider=(u,v) in edges and (w,v) in edges
            if not collider:
                dest=(v,w);nexts[(u,v)].add(dest);prevs[dest].add((u,v))
    terminals={(u,target) for u in undirected if target in undirected[u]}
    can_reach_target=closure(terminals,prevs)
    deadline=None if max_seconds is None else time.monotonic()+max_seconds
    visits=0
    def visit(path,seen):
        nonlocal visits
        visits+=1
        if deadline is not None and visits%1024==0 and time.monotonic()>deadline:
            raise TimeoutError(f"task-zone feasibility time cap exceeded after {visits} prefixes")
        u=path[-2];v=path[-1]
        if v==target:
            selected.update(tuple(sorted(p)) for p in zip(path,path[1:]))
            return
        for w in sorted(undirected[v]-seen):
            if (u,v) in edges and (w,v) in edges:continue
            nxt=(v,w)
            if nxt not in can_reach_target:continue
            visit(path+[w],seen|{w})
    for p in sorted(parents.get(action,())):
        start=(action,p)
        if start in can_reach_target:
            visit([action,p],{action,p})
    zone_nodes={n for e in selected for n in e}|{action,target}
    return selected,zone_nodes
