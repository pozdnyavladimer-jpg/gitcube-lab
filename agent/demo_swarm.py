# -*- coding: utf-8 -*-
"""Demo runner for Swarm v0.1.

Runs:
- GraphEval task
- GraphScorer
- Agent orchestrator
- prints final JSON

Usage:
  PYTHONPATH=. python -m agent.demo_swarm
"""

from __future__ import annotations

import json

from apps.grapheval.scorer import GraphScorer
from agent.orchestrator import orchestrate_task_dict


def make_demo_task(task_id: str) -> dict:
    return {
        "kind": "AGENT_TASK",
        "intent": "analyze_graph_feedback",
        "context": "graph",
        "payload": {
            "task_id": task_id,
        },
        "constraints": {
            "mode_hint": "CAUTIOUS",
        },
        "meta": {
            "task_id": task_id,
        },
    }


def main():
    # demo task definition
    task_def = {
        "id": "task_010_feedback_ok",
        "title": "Antidote: allow FEEDBACK only via capability adapter",
        "nodes": [
            {"id": "UI", "layer": 1},
            {"id": "Service", "layer": 2},
            {"id": "DB", "layer": 3, "is_core": True},
            {"id": "Observer", "layer": 2, "can_feedback": True, "can_event": True},
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
                ["Observer", "UI", "FEEDBACK"]
            ],
            "must_not_have_edges": [
                ["DB", "UI", "FEEDBACK"],
                ["UI", "DB", "SYNC_CALL"]
            ],
        },
    }

    # demo candidate solution
    solution = {
        "id": "task_010_feedback_ok",
        "edges": [
            ["UI", "Service", "SYNC_CALL"],
            ["Service", "DB", "DATA"],
            ["DB", "Observer", "EVENT"],
            ["Observer", "UI", "FEEDBACK"],
        ],
    }

    scorer = GraphScorer(task_def)
    report = scorer.score_solution(solution)
    report["kind"] = "GRAPH_EVAL"

    task = make_demo_task(task_def["id"])

    out = orchestrate_task_dict(
        task_dict=task,
        report=report,
        store_path="memory/memory.jsonl",
        lookback=200,
    )

    print("=== GRAPH REPORT ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print()
    print("=== SWARM RESULT ===")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
