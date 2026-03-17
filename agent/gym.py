# agent/gym.py
# -*- coding: utf-8 -*-
"""Architecture Gym v0.5 for GraphEval (predictive memory control)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from apps.grapheval.scorer import GraphScorer
from agent.mutations import MUTATORS, clone_solution, order_mutators
from agent.memory_policy import rank_mutators_from_history, predict_best_action
from memory.transitions import TransitionStore, build_transition
from memory.atom import MemoryAtom


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
        if not self.attempts:
            raise ValueError("Episode has no attempts")
        return max(
            self.attempts,
            key=lambda a: (
                float(a.report.get("score", 0.0) or 0.0),
                -float(a.report.get("risk", 1.0) or 1.0),
            ),
        )

    def last_attempt(self) -> Attempt:
        if not self.attempts:
            raise ValueError("Episode has no attempts")
        return self.attempts[-1]

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

def score(task: Dict[str, Any], solution: Dict[str, Any]) -> Dict[str, Any]:
    scorer = GraphScorer(task)
    report = scorer.score_solution(solution)
    report["kind"] = "GRAPH_EVAL"

    atom = MemoryAtom.from_report(report)
    report["dna_key"] = atom.dna_key
    report["band"] = atom.band
    report["phase_state"] = atom.phase_state
    report["flower"] = atom.flower

    return report


def pretty(report: Dict[str, Any]) -> str:
    return (
        f"{report.get('verdict')} | "
        f"score={float(report.get('score', 0.0)):.3f} "
        f"risk={float(report.get('risk', 0.0)):.3f} | "
        f"{report.get('dna')}"
    )


def _is_better(candidate: Dict[str, Any], current: Dict[str, Any]) -> bool:
    cand_score = float(candidate.get("score", 0.0) or 0.0)
    curr_score = float(current.get("score", 0.0) or 0.0)

    if cand_score > curr_score:
        return True
    if cand_score < curr_score:
        return False

    cand_risk = float(candidate.get("risk", 1.0) or 1.0)
    curr_risk = float(current.get("risk", 1.0) or 1.0)
    return cand_risk < curr_risk


def enrich_task_with_memory_context(task: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
    task2 = dict(task)

    verdict = str(report.get("verdict", "")).upper()
    dna_key = str(report.get("dna_key", "")).strip()
    risk = float(report.get("risk", 0.0) or 0.0)

    memory_hits = 0
    if dna_key:
        if verdict == "ALLOW":
            memory_hits = 2
        elif verdict == "WARN":
            memory_hits = 1

    task2["memory_context"] = {
        "memory_hits": int(memory_hits),
        "risk": float(risk),
    }
    return task2


# ---------------------------------------------------------
# Episode loop
# ---------------------------------------------------------

def run_episode(task: Dict[str, Any], initial_solution: Dict[str, Any], max_steps: int = 6) -> Episode:
    ep = Episode(
        task_id=str(task.get("id") or "unknown_task"),
        title=str(task.get("title") or ""),
    )

    transition_store = TransitionStore("memory/transitions.jsonl")

    current_solution = clone_solution(initial_solution)
    current_report = score(task, current_solution)

    ep.attempts.append(
        Attempt(
            step=0,
            action="initial",
            solution=clone_solution(current_solution),
            report=current_report,
        )
    )

    if str(current_report.get("verdict", "")).upper() == "ALLOW":
        return ep

    step = 1
    while step <= max_steps:
        best_local_solution = None
        best_local_report = None
        best_local_action = None

        task_with_memory = enrich_task_with_memory_context(task, current_report)
        ordered_mutators = order_mutators(task_with_memory, MUTATORS)

        history = transition_store.load_all()
        predicted_action = None

        if history:
            predicted_action = predict_best_action(
                str(current_report.get("dna_key", "")),
                history,
            )
            ordered_mutators = rank_mutators_from_history(
                ordered_mutators,
                history,
                dna_key=str(current_report.get("dna_key", "")),
            )

        for mutator in ordered_mutators:
            action, candidate_solution = mutator(task_with_memory, current_solution)
            candidate_report = score(task, candidate_solution)

            if best_local_report is None or _is_better(candidate_report, best_local_report):
                best_local_solution = candidate_solution
                best_local_report = candidate_report
                best_local_action = action

        if best_local_solution is None or best_local_report is None or best_local_action is None:
            break

        if not _is_better(best_local_report, current_report):
            break

        transition = build_transition(
            task_id=str(task.get("id") or "unknown_task"),
            action=str(best_local_action),
            from_report=current_report,
            to_report=best_local_report,
        )
        transition["predicted_action"] = predicted_action or ""
        transition_store.append(transition)

        current_solution = clone_solution(best_local_solution)
        current_report = best_local_report

        ep.attempts.append(
            Attempt(
                step=step,
                action=str(best_local_action),
                solution=clone_solution(current_solution),
                report=current_report,
            )
        )

        if str(current_report.get("verdict", "")).upper() == "ALLOW":
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

def main() -> None:
    demos = [
        demo_task_009(),
        demo_task_010(),
    ]

    for task, init_sol in demos:
        ep = run_episode(task, init_sol, max_steps=6)

        print("=" * 80)
        print(f"TASK: {task['id']} | {task['title']}")
        print("-" * 80)

        for attempt in ep.attempts:
            print(f"[step {attempt.step}] {attempt.action}")
            print(" ", pretty(attempt.report))
            print(" ", "edges:", attempt.solution["edges"])

        best = ep.best_attempt()
        print("-" * 80)
        print("BEST:")
        print(" ", pretty(best.report))
        print(" ", "action:", best.action)
        print("=" * 80)
        print()


if __name__ == "__main__":
    main()
