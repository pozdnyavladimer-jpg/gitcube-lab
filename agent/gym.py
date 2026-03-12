# -*- coding: utf-8 -*-
"""Architecture Gym v0.1 for GraphEval.

Goal:
- take a graph task
- try simple graph mutations
- score each attempt with GraphScorer
- keep improvements
- print episode summary

No ML. Pure mutation + scoring loop.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from apps.grapheval.scorer import GraphScorer


# ---------------------------------------------------------
# Data models
# ---------------------------------------------------------

@dataclass
class Attempt:
    step: int
    action: str
    solution: Dict[str, Any]
    report: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "action": self.action,
            "solution": self.solution,
            "report": self.report,
        }


@dataclass
class Episode:
    task_id: str
    title: str
    attempts: List[Attempt] = field(default_factory=list)

    def best_attempt(self) -> Attempt:
        return max(self.attempts, key=lambda a: float(a.report.get("score", 0.0)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "attempts": [a.to_dict() for a in self.attempts],
            "best": self.best_attempt().to_dict() if self.attempts else None,
        }


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def edge_key(e: List[Any]) -> Tuple[str, str, str]:
    return (str(e[0]), str(e[1]), str(e[2]))


def clone_solution(sol: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": sol["id"],
        "edges": [list(e) for e in sol.get("edges", [])],
    }


def score(task: Dict[str, Any], solution: Dict[str, Any]) -> Dict[str, Any]:
    scorer = GraphScorer(task)
    rep = scorer.score_solution(solution)
    rep["kind"] = "GRAPH_EVAL"
    return rep


def pretty(rep: Dict[str, Any]) -> str:
    return (
        f"{rep.get('verdict')} | "
        f"score={rep.get('score'):.3f} "
        f"risk={rep.get('risk'):.3f} | "
        f"{rep.get('dna')}"
    )


# ---------------------------------------------------------
# Simple mutation operators
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


def remove_illegal_sync_to_core(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
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

    return f"remove_illegal_sync_to_core removed={removed}", sol


def trim_feedback_without_capability(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)

    flags = {}
    for n in task.get("nodes", []):
        if isinstance(n, dict):
            flags[n["id"]] = n

    before = len(sol["edges"])
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
    return f"trim_feedback_without_capability removed={removed}", sol


# ---------------------------------------------------------
# Episode loop
# ---------------------------------------------------------

MUTATORS = [
    remove_forbidden_edges,
    add_required_edges,
    remove_reverse_feedback_deadly_pairs,
    trim_feedback_without_capability,
    remove_illegal_sync_to_core,
]


def run_episode(task: Dict[str, Any], initial_solution: Dict[str, Any], max_steps: int = 6) -> Episode:
    ep = Episode(task_id=str(task["id"]), title=str(task["title"]))

    current = clone_solution(initial_solution)
    current_report = score(task, current)
    ep.attempts.append(
        Attempt(step=0, action="initial", solution=clone_solution(current), report=current_report)
    )

    step = 1
    while step <= max_steps:
        best_local_sol = None
        best_local_rep = None
        best_action = None

        for mut in MUTATORS:
            action, candidate = mut(task, current)
            rep = score(task, candidate)

            if best_local_rep is None or float(rep["score"]) > float(best_local_rep["score"]):
                best_local_sol = candidate
                best_local_rep = rep
                best_action = action

        if best_local_rep is None:
            break

        # stop if no improvement
        if float(best_local_rep["score"]) <= float(current_report["score"]):
            break

        current = best_local_sol
        current_report = best_local_rep

        ep.attempts.append(
            Attempt(step=step, action=str(best_action), solution=clone_solution(current), report=current_report)
        )

        if str(current_report.get("verdict")) == "ALLOW":
            break

        step += 1

    return ep


# ---------------------------------------------------------
# Demo tasks
# ---------------------------------------------------------

def demo_task_009() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    task = {
        "id": "task_009_antidote",
        "title": "Antidote: prevent fake FEEDBACK and deadly pairs",
        "nodes": [
            {"id": "UI", "layer": 1},
            {"id": "Service", "layer": 2},
            {"id": "DB", "layer": 3, "is_core": True},
        ],
        "constraints": {
            "allowed_layer_diff": [0, 1],
            "max_density": 0.40,
            "feedback_requires_capability": True,
            "feedback_capability_key": "can_feedback",
            "feedback_ratio_max": 0.05,
            "deadly_pairs_block": True,
            "event_to_core_block": True,
            "protected_nodes_key": "is_core",
        },
        "goal": {
            "must_not_have_edges": [
                ["DB", "UI", "FEEDBACK"]
            ]
        },
    }

    bad_solution = {
        "id": "task_009_antidote",
        "edges": [
            ["UI", "Service", "SYNC_CALL"],
            ["Service", "DB", "DATA"],
            ["DB", "UI", "FEEDBACK"],
        ],
    }
    return task, bad_solution


def demo_task_010() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    task = {
        "id": "task_010_feedback_ok",
        "title": "Antidote: allow FEEDBACK only via capability adapter",
        "nodes": [
            {"id": "UI", "layer": 1},
            {"id": "Service", "layer": 2},
            {"id": "DB", "layer": 3, "is_core": True},
            {"id": "Observer", "layer": 2, "can_feedback": True, "can_event": True},
            {"id": "UI_FB", "layer": 1, "can_feedback": True},
        ],
        "constraints": {
            "allowed_layer_diff": [0, 1],
            "max_density": 0.40,
            "feedback_requires_capability": True,
            "feedback_capability_key": "can_feedback",
            "event_capability_key": "can_event",
            "feedback_ratio_max": 0.10,
            "deadly_pairs_block": True,
            "event_to_core_block": True,
            "protected_nodes_key": "is_core",
        },
        "goal": {
            "must_have_edges": [
                ["Observer", "UI_FB", "FEEDBACK"]
            ],
            "must_not_have_edges": [
                ["DB", "UI", "FEEDBACK"],
                ["UI", "DB", "SYNC_CALL"]
            ],
        },
    }

    weak_solution = {
        "id": "task_010_feedback_ok",
        "edges": [
            ["UI", "Service", "SYNC_CALL"],
            ["Service", "DB", "DATA"],
            ["DB", "UI", "FEEDBACK"],
        ],
    }
    return task, weak_solution


# ---------------------------------------------------------
# CLI demo
# ---------------------------------------------------------

def main():
    demos = [
        demo_task_009(),
        demo_task_010(),
    ]

    for task, init_sol in demos:
        ep = run_episode(task, init_sol, max_steps=6)

        print("=" * 80)
        print(f"TASK: {task['id']} | {task['title']}")
        print("-" * 80)

        for a in ep.attempts:
            print(f"[step {a.step}] {a.action}")
            print(" ", pretty(a.report))
            print(" ", "edges:", a.solution["edges"])

        best = ep.best_attempt()
        print("-" * 80)
        print("BEST:")
        print(" ", pretty(best.report))
        print(" ", "action:", best.action)
        print("=" * 80)
        print()

    # Optional JSON dump:
    # print(json.dumps(ep.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
