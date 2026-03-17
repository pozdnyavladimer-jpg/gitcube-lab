# -*- coding: utf-8 -*-
"""Mutation operators for Graph School / Architecture Gym."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Callable


Mutator = Callable[[Dict[str, Any], Dict[str, Any]], Tuple[str, Dict[str, Any]]]


def edge_key(e: List[Any]) -> Tuple[str, str, str]:
    return (str(e[0]), str(e[1]), str(e[2]))


def clone_solution(sol: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": sol["id"],
        "edges": [list(e) for e in sol.get("edges", [])],
    }


# ---------------------------------------------------------
# Memory-aware helpers
# ---------------------------------------------------------

def get_memory_context(task: Dict[str, Any]) -> Tuple[int, float]:
    """
    Read optional memory-guidance hints from task.

    Supported keys:
      task["memory_context"] = {
          "memory_hits": int,
          "risk": float,
      }

    If absent, defaults to:
      memory_hits = 0
      risk = 0.0
    """
    ctx = task.get("memory_context")
    if not isinstance(ctx, dict):
        return 0, 0.0

    memory_hits = int(ctx.get("memory_hits", 0) or 0)
    risk = float(ctx.get("risk", 0.0) or 0.0)
    return memory_hits, risk


def apply_memory_bias(mutators: List[Mutator], memory_hits: int, risk: float) -> List[Mutator]:
    """
    Reorder mutators based on memory and structural risk.

    Rules:
    - if memory is present and risk is low -> prefer stabilizing / conservative actions
    - if risk is high -> prefer destructive cleanup first
    - otherwise keep default order
    """
    if not mutators:
        return mutators

    names = {m.__name__: m for m in mutators}

    safe_order = [
        "remove_forbidden_edges",
        "remove_reverse_feedback_deadly_pairs",
        "trim_feedback_without_capability",
        "add_required_edges",
        "reroute_feedback_via_adapter",
    ]

    aggressive_order = [
        "remove_reverse_feedback_deadly_pairs",
        "remove_forbidden_edges",
        "trim_feedback_without_capability",
        "reroute_feedback_via_adapter",
        "add_required_edges",
    ]

    if memory_hits > 0 and risk < 0.30:
        ordered_names = safe_order
    elif risk > 0.70:
        ordered_names = aggressive_order
    else:
        return list(mutators)

    ordered: List[Mutator] = []
    used = set()

    for name in ordered_names:
        fn = names.get(name)
        if fn is not None:
            ordered.append(fn)
            used.add(name)

    for fn in mutators:
        if fn.__name__ not in used:
            ordered.append(fn)

    return ordered


def order_mutators(task: Dict[str, Any], mutators: List[Mutator]) -> List[Mutator]:
    """
    Public helper used by gym.py to obtain memory-aware mutator order.
    """
    memory_hits, risk = get_memory_context(task)
    return apply_memory_bias(list(mutators), memory_hits, risk)


# ---------------------------------------------------------
# Mutators
# ---------------------------------------------------------

def remove_forbidden_edges(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)
    forbidden = set()

    goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
    for e in goal.get("must_not_have_edges", []):
        if len(e) >= 3:
            forbidden.add((e[0], e[1], e[2]))

    before = len(sol["edges"])
    sol["edges"] = [e for e in sol["edges"] if edge_key(e) not in forbidden]
    removed = before - len(sol["edges"])

    return f"remove_forbidden_edges removed={removed}", sol


def add_required_edges(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)
    existing = {edge_key(e) for e in sol["edges"]}

    goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
    added = 0
    for e in goal.get("must_have_edges", []):
        if len(e) >= 3:
            k = (e[0], e[1], e[2])
            if k not in existing:
                sol["edges"].append([e[0], e[1], e[2]])
                existing.add(k)
                added += 1

    return f"add_required_edges added={added}", sol


def remove_reverse_feedback_deadly_pairs(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)

    sync_pairs = set()
    feedback_pairs = set()

    for e in sol["edges"]:
        u, v, t = e[0], e[1], e[2]
        if t == "SYNC_CALL":
            sync_pairs.add((u, v))
        if t == "FEEDBACK":
            feedback_pairs.add((u, v))

    deadly_feedback = set()
    for (a, b) in sync_pairs:
        if (b, a) in feedback_pairs:
            deadly_feedback.add((b, a, "FEEDBACK"))

    before = len(sol["edges"])
    sol["edges"] = [e for e in sol["edges"] if edge_key(e) not in deadly_feedback]
    removed = before - len(sol["edges"])

    return f"remove_reverse_feedback_deadly_pairs removed={removed}", sol


def trim_feedback_without_capability(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)

    flags = {}
    for n in task.get("nodes", []):
        if isinstance(n, dict):
            flags[n["id"]] = n

    constraints = task.get("constraints") if isinstance(task.get("constraints"), dict) else {}
    feedback_key = str(constraints.get("feedback_capability_key", "can_feedback"))

    kept = []
    removed = 0

    for e in sol["edges"]:
        u, v, t = e[0], e[1], e[2]
        if t != "FEEDBACK":
            kept.append(e)
            continue

        if flags.get(u, {}).get(feedback_key, False) and flags.get(v, {}).get(feedback_key, False):
            kept.append(e)
        else:
            removed += 1

    sol["edges"] = kept
    return f"trim_feedback_without_capability removed={removed}", sol


def reroute_feedback_via_adapter(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)

    flags = {}
    for n in task.get("nodes", []):
        if isinstance(n, dict):
            flags[n["id"]] = n

    constraints = task.get("constraints") if isinstance(task.get("constraints"), dict) else {}
    feedback_key = str(constraints.get("feedback_capability_key", "can_feedback"))

    adapters = [nid for nid, meta in flags.items() if meta.get(feedback_key, False)]
    if not adapters:
        return "reroute_feedback_via_adapter skipped=1", sol

    adapter = adapters[0]
    changed = 0
    new_edges = []

    for e in sol["edges"]:
        u, v, t = e[0], e[1], e[2]
        if t == "FEEDBACK" and not flags.get(v, {}).get(feedback_key, False):
            new_edges.append([u, adapter, t])
            changed += 1
        else:
            new_edges.append(e)

    sol["edges"] = new_edges
    return f"reroute_feedback_via_adapter changed={changed}", sol


MUTATORS: List[Mutator] = [
    remove_forbidden_edges,
    add_required_edges,
    remove_reverse_feedback_deadly_pairs,
    trim_feedback_without_capability,
    reroute_feedback_via_adapter,
]
