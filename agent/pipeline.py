# agent/pipeline.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, Optional

from apps.grapheval.scorer import GraphScorer
from agent.gym import run_episode
from agent.orchestrator import orchestrate_task_dict
from memory.record_crystal import record_crystal


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def build_initial_solution(task_def: Dict[str, Any]) -> Dict[str, Any]:
    """
    Very simple baseline solution builder.

    Rule:
    - connect first node of each layer to first node of next layer
    - if no layered chain found, return empty graph
    """
    nodes = task_def.get("nodes", [])
    by_layer: Dict[int, list] = {}

    for n in nodes:
        if not isinstance(n, dict):
            continue
        nid = n.get("id")
        layer = n.get("layer")
        if isinstance(nid, str) and isinstance(layer, int):
            by_layer.setdefault(layer, []).append(nid)

    layers = sorted(by_layer.keys())
    edges = []

    for i in range(len(layers) - 1):
        srcs = by_layer.get(layers[i], [])
        dsts = by_layer.get(layers[i + 1], [])

        if not srcs or not dsts:
            continue

        src = srcs[0]
        dst = dsts[0]

        # simple default edge type
        edge_type = "SYNC_CALL" if (layers[i + 1] - layers[i]) <= 1 else "DATA"
        edges.append([src, dst, edge_type])

    return {
        "id": str(task_def.get("id") or "unknown_task"),
        "edges": edges,
    }


def report_to_memory(
    *,
    report: Dict[str, Any],
    store_path: str,
    note: Optional[str] = None,
) -> None:
    """
    Save GraphEval report into structural memory.
    """
    try:
        record_crystal(
            store_path=store_path,
            kind=str(report.get("kind") or "GRAPH_EVAL"),
            verdict=str(report.get("verdict") or "ALLOW"),
            dna=str(report.get("dna") or ""),
            metrics={
                "risk": float(report.get("risk") or 0.0),
                "spectral_entropy": float(
                    (report.get("metrics") or {}).get("entropy", 0.0)
                ),
            },
            baseline={
                "mu": 0.30,
                "sigma": 0.10,
                "warn_threshold": 0.45,
                "block_threshold": 0.70,
            },
            context={
                "repo": "gitcube-lab",
                "ref": str(report.get("task_id") or ""),
                "note": note or "",
            },
        )
    except Exception:
        # Memory failure should not kill the pipeline
        pass


def build_agent_task(task_def: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrap task definition into orchestrator runtime task format.
    """
    return {
        "kind": "AGENT_TASK",
        "intent": "analyze_graph_feedback",
        "context": "graph",
        "payload": {
            "task_id": str(task_def.get("id") or "unknown_task"),
            "title": str(task_def.get("title") or ""),
        },
        "constraints": {},
        "meta": {
            "task_id": str(task_def.get("id") or "unknown_task"),
        },
    }


# ---------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------

def run_pipeline(
    *,
    task_def: Dict[str, Any],
    initial_solution: Optional[Dict[str, Any]] = None,
    store_path: str = "memory/memory.jsonl",
    max_steps: int = 6,
    lookback: int = 200,
) -> Dict[str, Any]:
    """
    Full GitCube Lab pipeline:

    task
    -> initial solution
    -> GraphEval scoring
    -> repair episode
    -> best solution
    -> memory atom
    -> policy/orchestrator result
    """

    # -----------------------------------------------------
    # 1. Build initial solution
    # -----------------------------------------------------
    if initial_solution is None:
        initial_solution = build_initial_solution(task_def)

    # -----------------------------------------------------
    # 2. Initial GraphEval report
    # -----------------------------------------------------
    scorer = GraphScorer(task_def)

    initial_report = scorer.score_solution(initial_solution)
    initial_report["kind"] = "GRAPH_EVAL"

    # -----------------------------------------------------
    # 3. Run repair loop
    # -----------------------------------------------------
    episode = run_episode(
        task=task_def,
        initial_solution=initial_solution,
        max_steps=max_steps,
    )

    best_attempt = episode.best_attempt()
    best_solution = best_attempt.solution
    best_report = dict(best_attempt.report)
    best_report["kind"] = "GRAPH_EVAL"

    # -----------------------------------------------------
    # 4. Record memory
    # -----------------------------------------------------
    report_to_memory(
        report=best_report,
        store_path=store_path,
        note="best_report_from_pipeline",
    )

    # -----------------------------------------------------
    # 5. Orchestrate final runtime decision
    # -----------------------------------------------------
    agent_task = build_agent_task(task_def)

    orchestrated = orchestrate_task_dict(
        task_dict=agent_task,
        report=best_report,
        store_path=store_path,
        lookback=lookback,
    )

    # -----------------------------------------------------
    # 6. Final package
    # -----------------------------------------------------
    return {
        "task_id": str(task_def.get("id") or "unknown_task"),
        "title": str(task_def.get("title") or ""),
        "initial_solution": initial_solution,
        "initial_report": initial_report,
        "attempt_count": len(episode.attempts),
        "attempts": [a.to_dict() for a in episode.attempts],
        "best_solution": best_solution,
        "best_report": best_report,
        "orchestrated_result": orchestrated,
    }


# ---------------------------------------------------------
# Demo
# ---------------------------------------------------------

def demo_task() -> Dict[str, Any]:
    return {
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


def main() -> None:
    import json

    task = demo_task()

    out = run_pipeline(
        task_def=task,
        store_path="memory/memory.jsonl",
        max_steps=6,
        lookback=200,
    )

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
