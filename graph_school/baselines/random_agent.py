# -*- coding: utf-8 -*-
"""Random baseline agent for Graph School.

This baseline samples random mutation actions over a graph solution
and keeps the best result it finds within a small step budget.

Usage:
  export PYTHONPATH=.
  python -m graph_school.baselines.random_agent --task datasets/grapheval/tasks/task_001.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
from typing import Any, Dict, List, Tuple

from apps.grapheval.scorer import GraphScorer
from apps.grapheval.schema import validate_task, validate_solution


ALLOWED_EDGE_TYPES = ["SYNC_CALL", "DATA", "EVENT", "DEP", "OWN", "FEEDBACK"]


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


def node_ids(task: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for n in task.get("nodes", []):
        if isinstance(n, dict) and isinstance(n.get("id"), str):
            out.append(n["id"])
    return out


def random_initial_solution(task: Dict[str, Any]) -> Dict[str, Any]:
    nodes = node_ids(task)
    edges: List[List[str]] = []

    # very small seed graph: connect first node of each adjacent layer if possible
    by_layer: Dict[int, List[str]] = {}
    for n in task.get("nodes", []):
        if isinstance(n, dict) and isinstance(n.get("layer"), int):
            by_layer.setdefault(int(n["layer"]), []).append(str(n["id"]))

    layers = sorted(by_layer.keys())
    for i in range(len(layers) - 1):
        srcs = by_layer[layers[i]]
        dsts = by_layer[layers[i + 1]]
        if srcs and dsts:
            edges.append([srcs[0], dsts[0], "SYNC_CALL"])

    return {"id": str(task["id"]), "edges": edges}


def mutate_add_edge(task: Dict[str, Any], solution: Dict[str, Any], rng: random.Random) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)
    ids = node_ids(task)
    if len(ids) < 2:
        return "add_edge(noop)", sol

    u = rng.choice(ids)
    v = rng.choice(ids)
    t = rng.choice(ALLOWED_EDGE_TYPES)

    if u != v:
        edge = [u, v, t]
        if edge not in sol["edges"]:
            sol["edges"].append(edge)

    return "add_edge", sol


def mutate_remove_edge(task: Dict[str, Any], solution: Dict[str, Any], rng: random.Random) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)
    if not sol["edges"]:
        return "remove_edge(noop)", sol
    idx = rng.randrange(len(sol["edges"]))
    sol["edges"].pop(idx)
    return "remove_edge", sol


def mutate_change_type(task: Dict[str, Any], solution: Dict[str, Any], rng: random.Random) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)
    if not sol["edges"]:
        return "change_type(noop)", sol
    idx = rng.randrange(len(sol["edges"]))
    sol["edges"][idx][2] = rng.choice(ALLOWED_EDGE_TYPES)
    return "change_type", sol


def mutate_swap_endpoint(task: Dict[str, Any], solution: Dict[str, Any], rng: random.Random) -> Tuple[str, Dict[str, Any]]:
    sol = clone_solution(solution)
    ids = node_ids(task)
    if not sol["edges"] or len(ids) < 2:
        return "swap_endpoint(noop)", sol

    idx = rng.randrange(len(sol["edges"]))
    if rng.random() < 0.5:
        sol["edges"][idx][0] = rng.choice(ids)
    else:
        sol["edges"][idx][1] = rng.choice(ids)
    return "swap_endpoint", sol


MUTATIONS = [
    mutate_add_edge,
    mutate_remove_edge,
    mutate_change_type,
    mutate_swap_endpoint,
]


def run_random_agent(task: Dict[str, Any], *, steps: int = 20, seed: int = 42) -> Dict[str, Any]:
    rng = random.Random(seed)

    current = random_initial_solution(task)
    current_report = score_solution(task, current)

    best_sol = clone_solution(current)
    best_rep = dict(current_report)
    history: List[Dict[str, Any]] = [
        {"step": 0, "action": "initial", "score": best_rep["score"], "verdict": best_rep["verdict"]}
    ]

    for step in range(1, steps + 1):
        mut = rng.choice(MUTATIONS)
        action, cand = mut(task, current, rng)
        rep = score_solution(task, cand)

        history.append({
            "step": step,
            "action": action,
            "score": rep["score"],
            "verdict": rep["verdict"],
        })

        # random baseline keeps best-so-far globally
        if float(rep.get("score", 0.0)) > float(best_rep.get("score", 0.0)):
            best_sol = clone_solution(cand)
            best_rep = dict(rep)

        # also sometimes move current state, even if worse
        if rng.random() < 0.35 or float(rep.get("score", 0.0)) >= float(current_report.get("score", 0.0)):
            current = clone_solution(cand)
            current_report = dict(rep)

    return {
        "agent": "random_agent",
        "task_id": str(task["id"]),
        "best_solution": best_sol,
        "best_report": best_rep,
        "history": history,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="Path to task JSON")
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    task = load_task(args.task)
    out = run_random_agent(task, steps=int(args.steps), seed=int(args.seed))
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
