# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


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


def _transition_dna_key(t: Dict[str, Any]) -> str:
    return str(
        t.get("dna_key")
        or t.get("from_dna_key")
        or t.get("from_dna")
        or ""
    ).strip()


def build_action_scores(
    transitions: List[Dict[str, Any]],
    *,
    dna_key: Optional[str] = None,
) -> Dict[str, Dict[str, float]]:
    table: Dict[str, Dict[str, float]] = {}

    for t in transitions:
        if dna_key:
            td = _transition_dna_key(t)
            if td and td != dna_key:
                continue

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


def predict_best_action(
    dna_key: str,
    transitions: List[Dict[str, Any]],
) -> Optional[str]:
    """
    Return the historically best action family for a given dna_key.
    Falls back to global history if no exact dna_key match exists.
    """
    dna_key = str(dna_key or "").strip()

    local_scores = build_action_scores(transitions, dna_key=dna_key)
    if local_scores:
        best = max(local_scores.items(), key=lambda kv: kv[1].get("score", 0.0))
        return str(best[0])

    global_scores = build_action_scores(transitions)
    if global_scores:
        best = max(global_scores.items(), key=lambda kv: kv[1].get("score", 0.0))
        return str(best[0])

    return None


def rank_mutators_from_history(
    mutators,
    transitions,
    *,
    dna_key: str = "",
):
    """
    Reorder mutators:
    1. put predicted best action first
    2. then sort the rest by learned score
    """
    best_action = predict_best_action(dna_key, transitions)

    global_scores = build_action_scores(transitions)

    decorated: List[Tuple[int, float, Any]] = []
    for m in mutators:
        fam = action_family(getattr(m, "__name__", ""))
        priority = 1 if fam == best_action else 0
        score = global_scores.get(fam, {}).get("score", 0.0)
        decorated.append((priority, float(score), m))

    decorated.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [m for _, _, m in decorated]
