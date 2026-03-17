# agent/core.py
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Any, Dict

from agent.pipeline import run_pipeline


class CoreEngine:
    """
    V-CORE Engine

    Orchestrates:
    - pipeline execution
    - memory influence
    - attractor dynamics
    """

    def __init__(
        self,
        *,
        store_path: str = "memory/memory.jsonl",
        lookback: int = 200,
    ) -> None:
        self.store_path = store_path
        self.lookback = lookback

    # -----------------------------------------------------
    # Main entry
    # -----------------------------------------------------

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full system execution.
        """

        result = run_pipeline(
            task_def=task,
            store_path=self.store_path,
            lookback=self.lookback,
        )

        enriched = self._apply_gravity(result)

        return enriched

    # -----------------------------------------------------
    # Gravity / Attractor logic
    # -----------------------------------------------------

    def _apply_gravity(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject attractor-based bias into result.
        """

        report = result.get("best_report", {})
        orchestrated = result.get("orchestrated_result", {})

        memory_hits = (
            orchestrated.get("state", {})
            .get("memory_hits", 0)
        )

        risk = float(report.get("risk", 0.0))

        gravity = self._compute_gravity(memory_hits, risk)

        result["gravity"] = gravity

        return result

    def _compute_gravity(self, memory_hits: int, risk: float) -> Dict[str, Any]:
        """
        Simple attractor model.
        """

        if memory_hits > 0 and risk < 0.3:
            return {
                "mode": "FOLLOW",
                "effect": "positive_attractor",
                "strength": round(1.0 - risk, 3),
            }

        if risk > 0.7:
            return {
                "mode": "ESCAPE",
                "effect": "repulsion",
                "strength": round(risk, 3),
            }

        return {
            "mode": "CAUTIOUS",
            "effect": "neutral",
            "strength": round(1.0 - risk, 3),
        }
