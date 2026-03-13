# -*- coding: utf-8 -*-
"""Benchmark runner for Graph School.

Runs all tasks through agent.gym and produces aggregate benchmark metrics.

Usage:
  export PYTHONPATH=.
  python -m agent.benchmark
  python -m agent.benchmark --limit 5
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

from apps.grapheval.schema import validate_task
from agent.gym import run_episode
from agent.train import guess_initial_solution


def load_tasks(tasks_dir: str) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    if not os.path.isdir(tasks_dir):
        return tasks

    for fn in sorted(os.listdir(tasks_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(tasks_dir, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                task = json.load(f)
            if validate_task(task):
                tasks.append(task)
        except Exception:
            continue
    return tasks


def ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def compute_report(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "benchmark": "Graph School v0.1",
            "tasks": 0,
            "pass_at_1": 0.0,
            "pass_at_3": 0.0,
            "pass_at_6": 0.0,
            "mean_initial_score": 0.0,
            "mean_best_score": 0.0,
            "repair_gain_mean": 0.0,
            "block_escape_rate": 0.0,
            "goal_satisfaction_rate": 0.0,
            "hard_failures": [],
        }

    n = len(rows)

    def solved_within_k(r: Dict[str, Any], k: int) -> bool:
        attempts = r.get("attempts", [])
        for a in attempts:
            if int(a.get("step", 999)) <= k and str(a.get("verdict", "")) == "ALLOW":
                return True
        return False

    pass_at_1 = sum(1 for r in rows if solved_within_k(r, 1)) / n
    pass_at_3 = sum(1 for r in rows if solved_within_k(r, 3)) / n
    pass_at_6 = sum(1 for r in rows if solved_within_k(r, 6)) / n

    mean_initial_score = sum(float(r["score_initial"]) for r in rows) / n
    mean_best_score = sum(float(r["score_best"]) for r in rows) / n
    repair_gain_mean = sum(float(r["score_best"]) - float(r["score_initial"]) for r in rows) / n

    block_start = [r for r in rows if str(r["verdict_initial"]) == "BLOCK"]
    if block_start:
        escaped = sum(1 for r in block_start if str(r["verdict_best"]) != "BLOCK")
        block_escape_rate = escaped / len(block_start)
    else:
        block_escape_rate = 0.0

    goal_satisfaction_rate = sum(1 for r in rows if not bool(r["goal_failed_best"])) / n

    hard_failures = [
        r["task_id"]
        for r in rows
        if str(r["verdict_best"]) == "BLOCK"
    ]

    return {
        "benchmark": "Graph School v0.1",
        "tasks": n,
        "pass_at_1": round(pass_at_1, 4),
        "pass_at_3": round(pass_at_3, 4),
        "pass_at_6": round(pass_at_6, 4),
        "mean_initial_score": round(mean_initial_score, 4),
        "mean_best_score": round(mean_best_score, 4),
        "repair_gain_mean": round(repair_gain_mean, 4),
        "block_escape_rate": round(block_escape_rate, 4),
        "goal_satisfaction_rate": round(goal_satisfaction_rate, 4),
        "hard_failures": hard_failures,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-dir", default="datasets/grapheval/tasks")
    ap.add_argument("--out", default="reports/benchmark_report.json")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-steps", type=int, default=6)
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    tasks = load_tasks(args.tasks_dir)
    if args.limit and args.limit > 0:
        tasks = tasks[: int(args.limit)]

    rows: List[Dict[str, Any]] = []

    print("=" * 80)
    print("GRAPH SCHOOL BENCHMARK")
    print("=" * 80)

    for i, task in enumerate(tasks, start=1):
        init_sol = guess_initial_solution(task)
        ep = run_episode(task, init_sol, max_steps=int(args.max_steps))

        attempts = []
        for a in ep.attempts:
            attempts.append({
                "step": int(a.step),
                "action": str(a.action),
                "verdict": str(a.report.get("verdict", "")),
                "score": float(a.report.get("score", 0.0)),
                "risk": float(a.report.get("risk", 1.0)),
            })

        best = ep.best_attempt()
        initial = ep.attempts[0]

        row = {
            "task_id": str(task["id"]),
            "title": str(task["title"]),
            "attempt_count": len(ep.attempts),
            "score_initial": float(initial.report.get("score", 0.0)),
            "verdict_initial": str(initial.report.get("verdict", "")),
            "score_best": float(best.report.get("score", 0.0)),
            "verdict_best": str(best.report.get("verdict", "")),
            "risk_best": float(best.report.get("risk", 1.0)),
            "dna_best": str(best.report.get("dna", "")),
            "goal_failed_best": bool(best.report.get("violations", {}).get("goal_failed", False)),
            "attempts": attempts,
        }
        rows.append(row)

        print(
            f"[{i}/{len(tasks)}] {row['task_id']} | "
            f"initial={row['verdict_initial']}:{row['score_initial']:.3f} -> "
            f"best={row['verdict_best']}:{row['score_best']:.3f}"
        )

    report = compute_report(rows)
    report["items"] = rows

    ensure_parent(args.out)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("-" * 80)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"saved to: {args.out}")
    print("=" * 80)


if __name__ == "__main__":
    main()
