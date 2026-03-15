# -*- coding: utf-8 -*-
"""
run_lab.py

Minimal GitCube Lab runner.

Usage:
  export PYTHONPATH=$PWD
  python run_lab.py --task datasets/grapheval/tasks/task_001.json --agent resonance
"""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any, Dict

from graph_school.visualization.field_visualizer import render_field


def run_agent(task_path: str, agent_name: str) -> Dict[str, Any]:
    module_map = {
        "random": "graph_school.baselines.random_agent",
        "greedy": "graph_school.baselines.greedy_agent",
        "rule": "graph_school.baselines.rule_based_agent",
        "resonance": "graph_school.baselines.resonance_agent",
    }
    if agent_name not in module_map:
        raise ValueError(f"Unknown agent: {agent_name}")

    cmd = [
        "python",
        "-m",
        module_map[agent_name],
        "--task",
        task_path,
    ]

    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print("AGENT FAILED")
        print("-" * 80)
        print(e.output)
        raise

    return json.loads(out)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="Path to task JSON")
    ap.add_argument(
        "--agent",
        default="resonance",
        choices=["random", "greedy", "rule", "resonance"],
        help="Which baseline agent to run",
    )
    ap.add_argument(
        "--vr-demo",
        action="store_true",
        help="Also run kernel.vr_comfort.demo_vr_comfort after Graph School",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 80)
    print("GITCUBE LAB — UNIFIED RUNNER")
    print("=" * 80)
    print(f"task : {args.task}")
    print(f"agent: {args.agent}")
    print()

    result = run_agent(args.task, args.agent)
    best_report = result["best_report"]

    print("BEST REPORT")
    print("-" * 80)
    print(json.dumps(best_report, ensure_ascii=False, indent=2))
    print()

    print("PRESSURE FIELD")
    print(render_field(best_report))
    print()

    print("HISTORY")
    print("-" * 80)
    for row in result.get("history", []):
        print(row)
    print()

    if args.vr_demo:
        print("=" * 80)
        print("RUNNING VR COMFORT DEMO")
        print("=" * 80)
        subprocess.run(["python", "-m", "kernel.vr_comfort.demo_vr_comfort"], check=False)

    print("=" * 80)
    print("done")
    print("=" * 80)


if __name__ == "__main__":
    main()
