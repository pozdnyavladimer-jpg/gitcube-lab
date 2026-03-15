# -*- coding: utf-8 -*-
"""Run all Graph School baseline agents on all tasks.

This benchmark runner evaluates:
- random_agent
- greedy_agent
- rule_based_agent

It loads tasks from datasets/grapheval/tasks, runs each baseline,
collects summary metrics, and writes a JSON report.

Usage:
  export PYTHONPATH=.
  python -m graph_school.benchmark.run_all_baselines

Optional:
  python -m graph_school.benchmark.run_all_baselines --limit 3
  python -m graph_school.benchmark.run_all_baselines --tasks-dir datasets/grapheval/tasks
  python -m graph_school.benchmark.run_all_baselines --out reports/graph_school_report.json
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

from apps.grapheval.schema import validate_task
from graph_school.baselines.random_agent import run_random_agent
from graph_school.baselines.greedy_agent import run_greedy_agent
from graph_school.baselines.rule_based_agent import run_rule_based_agent


# ---------------------------------------------------------
# IO
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Metrics
# ---------------------------------------------------------

def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def solved_within_k(history: List[Dict[str, Any]], k: int) -> bool:
    for row in history:
        step = int(row.get("step", 999999))
        verdict = str(row.get("verdict", ""))
        if step <= k and verdict == "ALLOW":
            return True
    return False


def summarize_agent_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
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

    pass_at_1 = sum(1 for r in rows if solved_within_k(r["history"], 1)) / n
    pass_at_3 = sum(1 for r in rows if solved_within_k(r["history"], 3)) / n
    pass_at_6 = sum(1 for r in rows if solved_within_k(r["history"], 6)) / n

    mean_initial_score = sum(safe_float(r["score_initial"]) for r in rows) / n
    mean_best_score = sum(safe_float(r["score_best"]) for r in rows) / n
    repair_gain_mean = sum(safe_float(r["score_best"]) - safe_float(r["score_initial"]) for r in rows) / n

    blocked_initial = [r for r in rows if str(r["verdict_initial"]) == "BLOCK"]
    if blocked_initial:
        escaped = sum(1 for r in blocked_initial if str(r["verdict_best"]) != "BLOCK")
        block_escape_rate = escaped / len(blocked_initial)
    else:
        block_escape_rate = 0.0

    goal_satisfaction_rate = sum(1 for r in rows if not bool(r["goal_failed_best"])) / n

    hard_failures = [r["task_id"] for r in rows if str(r["verdict_best"]) == "BLOCK"]

    return {
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


# ---------------------------------------------------------
# Agent adapters
# ---------------------------------------------------------

def normalize_agent_output(agent_name: str, task: Dict[str, Any], out: Dict[str, Any]) -> Dict[str, Any]:
    history = list(out.get("history", []))
    best_report = dict(out.get("best_report", {}))

    if history:
        first = history[0]
        score_initial = safe_float(first.get("score"))
        verdict_initial = str(first.get("verdict", ""))
    else:
        score_initial = safe_float(best_report.get("score"))
        verdict_initial = str(best_report.get("verdict", ""))

    return {
        "agent": agent_name,
        "task_id": str(task.get("id")),
        "title": str(task.get("title")),
        "score_initial": score_initial,
        "verdict_initial": verdict_initial,
        "score_best": safe_float(best_report.get("score")),
        "verdict_best": str(best_report.get("verdict", "")),
        "risk_best": safe_float(best_report.get("risk"), 1.0),
        "dna_best": str(best_report.get("dna", "")),
        "goal_failed_best": bool(best_report.get("violations", {}).get("goal_failed", False)),
        "history": history,
        "best_solution": out.get("best_solution", {}),
        "best_report": best_report,
    }


# ---------------------------------------------------------
# Main runner
# ---------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-dir", default="datasets/grapheval/tasks")
    ap.add_argument("--out", default="reports/graph_school_report.json")
    ap.add_argument("--limit", type=int, default=0, help="0 = all tasks")
    ap.add_argument("--random-steps", type=int, default=20)
    ap.add_argument("--greedy-steps", type=int, default=6)
    ap.add_argument("--rule-passes", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    tasks = load_tasks(args.tasks_dir)
    if args.limit and args.limit > 0:
        tasks = tasks[: int(args.limit)]

    print("=" * 80)
    print("GRAPH SCHOOL — RUN ALL BASELINES")
    print("=" * 80)
    print(f"tasks: {len(tasks)}")
    print()

    random_rows: List[Dict[str, Any]] = []
    greedy_rows: List[Dict[str, Any]] = []
    rule_rows: List[Dict[str, Any]] = []

    for i, task in enumerate(tasks, start=1):
        print(f"[{i}/{len(tasks)}] {task['id']} | {task['title']}")

        random_out = run_random_agent(task, steps=int(args.random_steps), seed=int(args.seed))
        greedy_out = run_greedy_agent(task, max_steps=int(args.greedy_steps))
        rule_out = run_rule_based_agent(task, max_passes=int(args.rule_passes))

        random_row = normalize_agent_output("random_agent", task, random_out)
        greedy_row = normalize_agent_output("greedy_agent", task, greedy_out)
        rule_row = normalize_agent_output("rule_based_agent", task, rule_out)

        random_rows.append(random_row)
        greedy_rows.append(greedy_row)
        rule_rows.append(rule_row)

        print(
            f"  random : {random_row['verdict_best']:5s} | "
            f"{random_row['score_best']:.3f} | {random_row['dna_best']}"
        )
        print(
            f"  greedy : {greedy_row['verdict_best']:5s} | "
            f"{greedy_row['score_best']:.3f} | {greedy_row['dna_best']}"
        )
        print(
            f"  rule   : {rule_row['verdict_best']:5s} | "
            f"{rule_row['score_best']:.3f} | {rule_row['dna_best']}"
        )
        print()

    summary_random = summarize_agent_rows(random_rows)
    summary_greedy = summarize_agent_rows(greedy_rows)
    summary_rule = summarize_agent_rows(rule_rows)

    report = {
        "benchmark": "Graph School Baselines v0.1",
        "tasks_dir": args.tasks_dir,
        "task_count": len(tasks),
        "agents": {
            "random_agent": {
                "summary": summary_random,
                "items": random_rows,
            },
            "greedy_agent": {
                "summary": summary_greedy,
                "items": greedy_rows,
            },
            "rule_based_agent": {
                "summary": summary_rule,
                "items": rule_rows,
            },
        },
    }

    ensure_parent(args.out)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("-" * 80)
    print("SUMMARY")
    print(json.dumps(
        {
            "random_agent": summary_random,
            "greedy_agent": summary_greedy,
            "rule_based_agent": summary_rule,
        },
        ensure_ascii=False,
        indent=2,
    ))
    print(f"saved to: {args.out}")
    print("=" * 80)


if __name__ == "__main__":
    main()
