# -*- coding: utf-8 -*-
"""Training loop for Graph School / Architecture Gym v0.1.

Runs episodes over all tasks in datasets/grapheval/tasks,
builds simple initial solutions, applies mutation loop via agent.gym,
and stores training traces as JSONL.

Usage:
  export PYTHONPATH=.
  python -m agent.train

Optional:
  python -m agent.train --limit 3
  python -m agent.train --tasks-dir datasets/grapheval/tasks --out traces/train_traces.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Tuple

from apps.grapheval.schema import validate_task
from agent.gym import run_episode


# ---------------------------------------------------------
# IO helpers
# ---------------------------------------------------------

def load_tasks(tasks_dir: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not os.path.isdir(tasks_dir):
        return items

    for fn in sorted(os.listdir(tasks_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(tasks_dir, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                task = json.load(f)
            if validate_task(task):
                items.append(task)
        except Exception:
            continue
    return items


def ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def append_jsonl(path: str, row: Dict[str, Any]) -> None:
    ensure_parent(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------
# Initial solution builder
# ---------------------------------------------------------

def guess_initial_solution(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Very simple baseline proposal:
    - connect adjacent layers with SYNC_CALL / DATA chain
    - intentionally naive, so gym can improve it
    """
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
        cur_layer = layers[i]
        next_layer = layers[i + 1]

        srcs = by_layer.get(cur_layer, [])
        dsts = by_layer.get(next_layer, [])

        if not srcs or not dsts:
            continue

        # take first node of current layer -> first node of next layer
        src = srcs[0]
        dst = dsts[0]

        edge_type = "SYNC_CALL" if next_layer - cur_layer <= 1 else "DATA"
        edges.append([src, dst, edge_type])

    # if task explicitly requires must_have_edges, add none at start:
    # gym should discover improvements itself

    return {
        "id": str(task.get("id") or "unknown_task"),
        "edges": edges,
    }


# ---------------------------------------------------------
# Trace builder
# ---------------------------------------------------------

def episode_to_trace(task: Dict[str, Any], ep) -> Dict[str, Any]:
    attempts = ep.attempts
    best = ep.best_attempt()

    scores = [float(a.report.get("score", 0.0)) for a in attempts]
    risks = [float(a.report.get("risk", 1.0)) for a in attempts]
    verdicts = [str(a.report.get("verdict", "")) for a in attempts]
    actions = [str(a.action) for a in attempts]

    return {
        "kind": "GRAPH_SCHOOL_TRACE",
        "task_id": str(task.get("id")),
        "title": str(task.get("title")),
        "attempt_count": len(attempts),
        "score_initial": scores[0] if scores else None,
        "score_best": float(best.report.get("score", 0.0)),
        "risk_best": float(best.report.get("risk", 1.0)),
        "verdict_best": str(best.report.get("verdict", "")),
        "dna_best": str(best.report.get("dna", "")),
        "actions": actions,
        "score_curve": scores,
        "risk_curve": risks,
        "verdict_curve": verdicts,
        "best_solution": best.solution,
        "best_report": best.report,
    }


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "tasks": 0,
            "allow_best": 0,
            "warn_best": 0,
            "block_best": 0,
            "mean_best_score": 0.0,
        }

    allow_best = sum(1 for r in rows if r.get("verdict_best") == "ALLOW")
    warn_best = sum(1 for r in rows if r.get("verdict_best") == "WARN")
    block_best = sum(1 for r in rows if r.get("verdict_best") == "BLOCK")

    mean_best_score = sum(float(r.get("score_best", 0.0) or 0.0) for r in rows) / max(1, len(rows))

    return {
        "tasks": len(rows),
        "allow_best": allow_best,
        "warn_best": warn_best,
        "block_best": block_best,
        "mean_best_score": round(mean_best_score, 4),
    }


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-dir", default="datasets/grapheval/tasks")
    ap.add_argument("--out", default="traces/train_traces.jsonl")
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0, help="0 = all tasks")
    ap.add_argument("--reset", action="store_true", help="truncate output file before run")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    tasks = load_tasks(args.tasks_dir)
    if args.limit and args.limit > 0:
        tasks = tasks[: int(args.limit)]

    if args.reset and os.path.exists(args.out):
        os.remove(args.out)

    traces: List[Dict[str, Any]] = []

    print("=" * 80)
    print("GRAPH SCHOOL TRAINING LOOP")
    print("=" * 80)

    for i, task in enumerate(tasks, start=1):
        init_sol = guess_initial_solution(task)
        ep = run_episode(task, init_sol, max_steps=int(args.max_steps))
        trace = episode_to_trace(task, ep)
        append_jsonl(args.out, trace)
        traces.append(trace)

        print(f"[{i}/{len(tasks)}] {task['id']} | best={trace['verdict_best']} | score={trace['score_best']:.3f}")
        print(f"  actions: {' -> '.join(trace['actions'])}")
        print(f"  dna_best: {trace['dna_best']}")

    summary = summarize(traces)

    print("-" * 80)
    print("SUMMARY")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"traces saved to: {args.out}")
    print("=" * 80)


if __name__ == "__main__":
    main()
