# agent/memory_policy.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


def action_family(action: str) -> str:
    s = str(action or "").lower()

    if s.startswith("remove_forbidden_edges"):
        return "remove_forbidden_edges"
    if s.startswith("add_required_edges"):
        return "add_required_edges"
    if s.startswith("remove_reverse_feedback_deadly_pairs"):
        return "remove_reverse_feedback_deadly_pairs"
    if s.startswith("trim_feedback_without_capability"):
        return "trim_feedback_without_capability"
    if s.startswith("reroute_feedback_via_adapter"):
        return "reroute_feedback_via_adapter"

    return "unknown"


def build_action_scores(transitions: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Aggregate transition history by action family.
    Score = success count + avg risk improvement.
    """
    table: Dict[str, Dict[str, float]] = {}

    for t in transitions:
        action = action_family(str(t.get("action", "")))
        if action == "unknown":
            continue

        from_risk = _num(t.get("from_risk", 1.0), 1.0)
        to_risk = _num(t.get("to_risk", 1.0), 1.0)
        delta = from_risk - to_risk

        row = table.setdefault(
            action,
            {
                "count": 0.0,
                "success": 0.0,
                "risk_gain_sum": 0.0,
            },
        )

        row["count"] += 1.0
        if delta > 0:
            row["success"] += 1.0
        row["risk_gain_sum"] += delta

    for action, row in table.items():
        count = max(1.0, row["count"])
        row["success_rate"] = row["success"] / count
        row["avg_risk_gain"] = row["risk_gain_sum"] / count
        row["score"] = row["success_rate"] + row["avg_risk_gain"]

    return table


def rank_mutators_from_history(
    mutators: List[Any],
    transitions: List[Dict[str, Any]],
) -> List[Any]:
    """
    Reorder mutators using learned action scores from transition history.
    """
    scores = build_action_scores(transitions)

    decorated: List[Tuple[float, Any]] = []
    for m in mutators:
        fam = action_family(getattr(m, "__name__", ""))
        score = scores.get(fam, {}).get("score", 0.0)
        decorated.append((float(score), m))

    decorated.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in decorated]
