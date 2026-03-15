# -*- coding: utf-8 -*-
"""Gravity-guided baseline agent for Graph School.

This agent uses:
- GraphEval report
- CrystalMemory
- MemoryGravity
- prioritized mutation families

Flow:
1. score current graph
2. query crystal memory for top attractors
3. derive mutation priorities from memory gravity
4. evaluate candidate mutations
5. keep the best improving move

Usage:
  export PYTHONPATH=$PWD
  python -m graph_school.baselines.gravity_agent --task datasets/grapheval/tasks/task_001.json
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Tuple

from apps.grapheval.scorer import GraphScorer
from apps.grapheval.schema import validate_task, validate_solution
from memory.memory_gravity import MemoryGravity


# ---------------------------------------------------------------------
# IO / scoring
# ---------------------------------------------------------------------

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
            "flower": {"petal_area": 0.0},
            "band": 1,
            "phase_state": 1,
        }

    scorer = GraphScorer(task)
    rep = scorer.score_solution(solution)

    metrics = rep.get("metrics", {})
    antidote = rep.get("antidote", {})

    # normalize fields so memory / gravity can use them
    rep["cycles"] = float(metrics.get("strict_cycle_nodes", 0))
    rep["layer_violations"] = float(metrics.get("layer_viol", 0))
    rep["toxins"] = float(metrics.get("deadly_pairs", 0))
    rep["feedback_edges"] = float(metrics.get("feedback_count", 0))
    rep["edge_density"] = float(metrics.get("density", 0.0))
    rep["entropy"] = float(metrics.get("entropy", 0.0))

    rep["toxins"] += float(antidote.get("feedback_cap_viol", 0))
    rep["toxins"] += float(antidote.get("feedback_quota_viol", 0))
    rep["toxins"] += float(antidote.get("event_cap_viol", 0))
    rep["toxins"] += float(antidote.get("event_core_hits", 0))

    # crystal_memory expects flower field
    if "flower" not in rep:
        rep["flower"] = {"petal_area": 0.0}

    if "band" not in rep:
        v = str(rep.get("verdict", "ALLOW")).upper()
        rep["band"] = 1 if v == "BLOCK" else 3 if v == "WARN" else 6

    if "phase_state" not in rep:
        rep["phase_state"] = 1

    return rep


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


# ---------------------------------------------------------------------
# Mutation families
# ---------------------------------------------------------------------

def break_cycle(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    sol = clone_solution(solution)
    removed = 0
    for i in range(len(sol["edges"]) - 1, -1, -1):
        t = sol["edges"][i][2]
        if t in {"SYNC_CALL", "DEP", "OWN", "DATA"}:
            sol["edges"].pop(i)
            removed = 1
            break
    return "break_cycle", sol, removed


def remove_feedback(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    sol = clone_solution(solution)
    before = len(sol["edges"])
    sol["edges"] = [e for e in sol["edges"] if e[2] != "FEEDBACK"]
    return "remove_feedback", sol, before - len(sol["edges"])


def reduce_density(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    sol = clone_solution(solution)
    if not sol["edges"]:
        return "reduce_density", sol, 0
    sol["edges"].pop()
    return "reduce_density", sol, 1


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


def remove_forbidden_edges(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    sol = clone_solution(solution)
    forbidden = set()

    goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
    for e in goal.get("must_not_have_edges", []):
        if len(e) >= 3:
            forbidden.add((e[0], e[1], e[2]))

    before = len(sol["edges"])
    sol["edges"] = [e for e in sol["edges"] if edge_key(e) not in forbidden]
    return "remove_forbidden_edges", sol, before - len(sol["edges"])


def trim_feedback_without_capability(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    sol = clone_solution(solution)

    flags = {}
    for n in task.get("nodes", []):
        if isinstance(n, dict):
            flags[n["id"]] = n

    feedback_key = "can_feedback"
    constraints = task.get("constraints") if isinstance(task.get("constraints"), dict) else {}
    if "feedback_capability_key" in constraints:
        feedback_key = str(constraints["feedback_capability_key"])

    kept = []
    removed = 0
    for e in sol["edges"]:
        u, v, t = e
        if t != "FEEDBACK":
            kept.append(e)
            continue

        if flags.get(u, {}).get(feedback_key, False) and flags.get(v, {}).get(feedback_key, False):
            kept.append(e)
        else:
            removed += 1

    sol["edges"] = kept
    return "trim_feedback_without_capability", sol, removed


def reroute_edge(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    name, sol, changed = remove_forbidden_edges(task, solution)
    if changed > 0:
        return "reroute_edge(remove_forbidden)", sol, changed
    name, sol, changed = add_required_edges(task, solution)
    if changed > 0:
        return "reroute_edge(add_required)", sol, changed
    return "reroute_edge", clone_solution(solution), 0


def insert_adapter(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    return trim_feedback_without_capability(task, solution)


def split_node(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    return reduce_density(task, solution)


def hard_prune(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    sol = clone_solution(solution)
    removed = min(2, len(sol["edges"]))
    for _ in range(removed):
        sol["edges"].pop()
    return "hard_prune", sol, removed


def cut_edge(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    return reduce_density(task, solution)


def reset_branch(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    return "reset_branch", guess_initial_solution(task), 1


def refactor(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    return "refactor", clone_solution(solution), 0


def optimize(task: Dict[str, Any], solution: Dict[str, Any]) -> Tuple[str, Dict[str, Any], int]:
    return "optimize", clone_solution(solution), 0


MUTATION_MAP = {
    "break_cycle": break_cycle,
    "remove_feedback": remove_feedback,
    "split_node": split_node,
    "reroute_edge": reroute_edge,
    "insert_adapter": insert_adapter,
    "reduce_density": reduce_density,
    "hard_prune": hard_prune,
    "cut_edge": cut_edge,
    "reset_branch": reset_branch,
    "refactor": refactor,
    "optimize": optimize,
    "add_required_edges": add_required_edges,
    "remove_forbidden_edges": remove_forbidden_edges,
    "trim_feedback_without_capability": trim_feedback_without_capability,
}


# ---------------------------------------------------------------------
# Gravity logic
# ---------------------------------------------------------------------

def gravity_to_mutation_priority(report: Dict[str, Any], top_hits: List[Any]) -> List[str]:
    """
    Convert memory gravity into mutation priorities.

    Heuristic:
    - if no memory hits, fallback to report-driven rules
    - if strongest attractor is strong and current state is risky,
      prioritize moves that reduce mismatch with stable crystals
    """
    priorities: List[str] = []

    if top_hits:
        best = top_hits[0]

        # if the strongest hit is a real stable attractor
        if best.gravity > 0.0 and best.verdict.upper() == "ALLOW":
            if best.dna_similarity < 0.8:
                priorities.extend([
                    "remove_forbidden_edges",
                    "add_required_edges",
                    "reroute_edge",
                ])

            if report.get("cycles", 0.0) > 0:
                priorities.append("break_cycle")

            if report.get("toxins", 0.0) > 0 or report.get("feedback_edges", 0.0) > 0:
                priorities.extend([
                    "trim_feedback_without_capability",
                    "remove_feedback",
                    "insert_adapter",
                ])

            if report.get("edge_density", 0.0) > 0.35:
                priorities.extend([
                    "reduce_density",
                    "split_node",
                ])

        # if memory mostly shows repulsion, go aggressive
        elif best.gravity < 0.0:
            priorities.extend([
                "hard_prune",
                "cut_edge",
                "reset_branch",
            ])

    # report-driven fallback / completion
    if report.get("violations", {}).get("goal_failed", False):
        priorities.extend(["add_required_edges", "remove_forbidden_edges"])

    if report.get("cycles", 0.0) > 0:
        priorities.append("break_cycle")

    if report.get("toxins", 0.0) > 0 or report.get("feedback_edges", 0.0) > 0:
        priorities.extend(["trim_feedback_without_capability", "remove_feedback"])

    if report.get("edge_density", 0.0) > 0.35:
        priorities.append("reduce_density")

    if not priorities:
        priorities.extend(["refactor", "optimize"])

    # unique preserve order
    out: List[str] = []
    seen = set()
    for p in priorities:
        if p not in seen:
            seen.add(p)
            out.append(p)

    return out


# ---------------------------------------------------------------------
# Main agent
# ---------------------------------------------------------------------

def run_gravity_agent(
    task: Dict[str, Any],
    *,
    max_steps: int = 8,
    memory_path: str = "memory/crystal_memory.jsonl",
    record_success: bool = False,
) -> Dict[str, Any]:
    current = guess_initial_solution(task)
    current_report = score_solution(task, current)

    gravity = MemoryGravity(store_path=memory_path)

    history: List[Dict[str, Any]] = []

    initial_hits = gravity.top_hits(current_report, top_k=3)
    history.append({
        "step": 0,
        "action": "initial",
        "score": current_report["score"],
        "verdict": current_report["verdict"],
        "gravity_top": [h.to_dict() for h in initial_hits],
    })

    best_sol = clone_solution(current)
    best_rep = dict(current_report)

    for step in range(1, max_steps + 1):
        top_hits = gravity.top_hits(current_report, top_k=5)
        priorities = gravity_to_mutation_priority(current_report, top_hits)

        best_local_sol = None
        best_local_rep = None
        best_action = None
        best_memory = [h.to_dict() for h in top_hits]

        for name in priorities:
            fn = MUTATION_MAP.get(name)
            if fn is None:
                continue

            action, candidate, changed = fn(task, current)
            if changed <= 0 and name not in {"refactor", "optimize"}:
                continue

            rep = score_solution(task, candidate)

            # local objective = better score, then lower risk
            if (
                best_local_rep is None
                or float(rep["score"]) > float(best_local_rep["score"])
                or (
                    float(rep["score"]) == float(best_local_rep["score"])
                    and float(rep.get("risk", 1.0)) < float(best_local_rep.get("risk", 1.0))
                )
            ):
                best_local_sol = candidate
                best_local_rep = rep
                best_action = action

        if best_local_rep is None:
            break

        history.append({
            "step": step,
            "action": str(best_action),
            "score": best_local_rep["score"],
            "verdict": best_local_rep["verdict"],
            "gravity_top": best_memory,
        })

        if float(best_local_rep["score"]) <= float(current_report["score"]):
            break

        current = clone_solution(best_local_sol)
        current_report = dict(best_local_rep)

        if (
            float(current_report["score"]) > float(best_rep["score"])
            or (
                float(current_report["score"]) == float(best_rep["score"])
                and float(current_report.get("risk", 1.0)) < float(best_rep.get("risk", 1.0))
            )
        ):
            best_sol = clone_solution(current)
            best_rep = dict(current_report)

        if str(current_report.get("verdict")) == "ALLOW":
            break

    if record_success and str(best_rep.get("verdict")) == "ALLOW":
        # optional crystal recording
        from memory.crystal_memory import CrystalMemory
        cm = CrystalMemory(store_path=memory_path)
        cm.record_report(
            best_rep,
            repo="gitcube-lab",
            ref=str(task.get("id", "")),
            note="recorded by gravity_agent",
            assembly_code=[row["action"] for row in history if row["action"] != "initial"],
            allow_unassembled=False,
        )

    return {
        "agent": "gravity_agent",
        "task_id": str(task["id"]),
        "best_solution": best_sol,
        "best_report": best_rep,
        "history": history,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="Path to task JSON")
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--memory", default="memory/crystal_memory.jsonl")
    ap.add_argument("--record-success", action="store_true")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    task = load_task(args.task)
    out = run_gravity_agent(
        task,
        max_steps=int(args.steps),
        memory_path=str(args.memory),
        record_success=bool(args.record_success),
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
