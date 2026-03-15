# -*- coding: utf-8 -*-
"""Rule-based baseline agent for Graph School.

This baseline follows a fixed repair priority:
1. remove forbidden edges
2. remove deadly feedback
3. trim illegal feedback
4. remove illegal sync-to-core
5. add required edges

Usage:
  export PYTHONPATH=.
  python -m graph_school.baselines.rule_based_agent --task datasets/grapheval/tasks/task_001.json
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Tuple

from apps.grapheval.scorer import GraphScorer
from apps.grapheval.schema import validate_task, validate_solution


def load_task(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        task = json.load(f)
    if not validate_task(task):
        raise ValueError(f"Invalid task format: {path}")
    return task


def clone_solution(sol: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(sol.get("id", "unknown")),
        "edges": [list(e) for e in sol.get("edges", [])],
    }


def score_solution(task: Dict[str, Any], solution: Dict[str, Any]) -> Dict[str, Any]:
    if not validate_solution(solution):
        return {
            "task_id": str(task.get("id")),
            "verdict": "BLOCK",
            "risk": 1.0,
            "score": 0.0,
            "dna": "C9 L9 D9 H9",
            "metrics": {},
            "violations": {"goal_failed": True, "invalid_solution": True},
        }
    scorer = GraphScorer(task)
    return scorer.score_solution(solution)


def guess_initial_solution(task: Dict[str, Any]) -> Dict[str, Any]:
    nodes = task.get("nodes", [])
    by_layer: Dict[int, List[str]] = {}

    for n in nodes:
        if not isinstance(n, dict):
            continue
        nid = n.get("id")
        layer = n.get("layer")
        if isinstance(nid, str) and isinstance(layer, int):
            by_layer.setdefault(layer, []).append(nid)

    edges: List[List[str]] = []
    layers = sorted(by_layer.keys())
    for i in range(len(layers) - 1):
        srcs = by_layer.get(layers[i], [])
        dsts = by_layer.get(layers[i + 1], [])
        if srcs and dsts:
            edges.append([srcs[0], dsts[0], "SYNC_CALL"])

    return {
        "id": str(task.get("id") or "unknown_task"),
        "edges": edges,
    }


def edge_key(e: List[Any]) -> Tuple[str, str, str]:
    return (str(e[0]), str(e[1]), str(e[2]))


def remove_forbidden_edges(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    sol = clone_solution(solution)
    forbidden = set()

    goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
    for e in goal.get("must_not_have_edges", []):
        if len(e) >= 3:
            forbidden.add((e[0], e[1], e[2]))

    before = len(sol["edges"])
    sol["edges"] = [e for e in sol["edges"] if edge_key(e) not in forbidden]
    removed = before - len(sol["edges"])
    return "remove_forbidden_edges", sol, removed


def remove_reverse_feedback_deadly_pairs(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
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

    return "remove_reverse_feedback_deadly_pairs", sol, removed


def trim_feedback_without_capability(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    sol = clone_solution(solution)

    flags = {}
    for n in task.get("nodes", []):
        if isinstance(n, dict):
            flags[n["id"]] = n

    kept = []
    removed = 0

    feedback_key = "can_feedback"
    constraints = task.get("constraints") if isinstance(task.get("constraints"), dict) else {}
    if "feedback_capability_key" in constraints:
        feedback_key = str(constraints["feedback_capability_key"])

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
    return "trim_feedback_without_capability", sol, removed


def remove_illegal_sync_to_core(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    sol = clone_solution(solution)

    core_nodes = {
        n["id"]
        for n in task.get("nodes", [])
        if isinstance(n, dict) and bool(n.get("is_core", False))
    }

    before = len(sol["edges"])
    sol["edges"] = [
        e for e in sol["edges"]
        if not (e[2] == "SYNC_CALL" and e[1] in core_nodes and e[0] != e[1] and e[0] != "Service")
    ]
    removed = before - len(sol["edges"])
    return "remove_illegal_sync_to_core", sol, removed


def add_required_edges(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
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

    return "add_required_edges", sol, added


RULES = [
    remove_forbidden_edges,
    remove_reverse_feedback_deadly_pairs,
    trim_feedback_without_capability,
    remove_illegal_sync_to_core,
    add_required_edges,
]


def run_rule_based_agent(task: Dict[str, Any], *, max_passes: int = 4) -> Dict[str, Any]:
    current = guess_initial_solution(task)
    current_report = score_solution(task, current)

    history: List[Dict[str, Any]] = [
        {"step": 0, "action": "initial", "score": current_report["score"], "verdict": current_report["verdict"]}
    ]

    step = 1
    for _ in range(max_passes):
        changed_any = False

        for rule in RULES:
            action, candidate, changed = rule(task, current)
            if changed <= 0:
                continue

            rep = score_solution(task, candidate)
            history.append({
                "step": step,
                "action": f"{action} changed={changed}",
                "score": rep["score"],
                "verdict": rep["verdict"],
            })

            current = clone_solution(candidate)
            current_report = dict(rep)
            changed_any = True
            step += 1

            if str(current_report.get("verdict")) == "ALLOW":
                break

        if str(current_report.get("verdict")) == "ALLOW":
            break

        if not changed_any:
            break

    return {
        "agent": "rule_based_agent",
        "task_id": str(task["id"]),
        "best_solution": current,
        "best_report": current_report,
        "history": history,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="Path to task JSON")
    ap.add_argument("--passes", type=int, default=4)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    task = load_task(args.task)
    out = run_rule_based_agent(task, max_passes=int(args.passes))
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
