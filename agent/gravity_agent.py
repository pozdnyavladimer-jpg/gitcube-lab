# agent/gravity_agent.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from memory.memory_gravity import MemoryGravity


@dataclass
class GravityDecision:
    mode_hint: str
    memory_effect: str
    confidence: float
    gravity_mean: float
    gravity_max: float
    attractor_verdict: str
    attractor_band: int
    attractor_phase_state: int
    attractor_octave: int
    attractor_octave_label: str
    recommended_bias: str
    notes: list[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_hint": self.mode_hint,
            "memory_effect": self.memory_effect,
            "confidence": round(float(self.confidence), 6),
            "gravity_mean": round(float(self.gravity_mean), 6),
            "gravity_max": round(float(self.gravity_max), 6),
            "attractor_verdict": self.attractor_verdict,
            "attractor_band": int(self.attractor_band),
            "attractor_phase_state": int(self.attractor_phase_state),
            "attractor_octave": int(self.attractor_octave),
            "attractor_octave_label": self.attractor_octave_label,
            "recommended_bias": self.recommended_bias,
            "notes": list(self.notes),
        }


def decide_from_gravity(
    report: Dict[str, Any],
    *,
    store_path: str = "memory/memory.jsonl",
) -> GravityDecision:
    """
    Read memory gravity and convert it into a lightweight agent decision.

    This does not mutate the graph itself.
    It only returns a bias / hint for the next repair or policy step.
    """
    mg = MemoryGravity(store_path=store_path)

    guidance = mg.guidance_vector(report)
    best = mg.best_attractor(report)

    gravity_mean = float(guidance.get("gravity_mean", 0.0))
    gravity_max = float(guidance.get("gravity_max", 0.0))
    confidence = float(guidance.get("confidence", 0.0))

    if best is None:
        return GravityDecision(
            mode_hint="NEUTRAL",
            memory_effect="no_memory",
            confidence=0.0,
            gravity_mean=0.0,
            gravity_max=0.0,
            attractor_verdict="UNKNOWN",
            attractor_band=0,
            attractor_phase_state=0,
            attractor_octave=0,
            attractor_octave_label="UNKNOWN",
            recommended_bias="explore_freely",
            notes=["No memory attractor found."],
        )

    notes: list[str] = []

    # ---------------------------------------------------------
    # Interpret gravity
    # ---------------------------------------------------------
    if gravity_mean >= 0.35:
        memory_effect = "positive_attractor"
        mode_hint = "FOLLOW"
        recommended_bias = "move_toward_stable_pattern"
        notes.append("Memory suggests a stable nearby attractor.")
    elif gravity_mean >= 0.10:
        memory_effect = "weak_positive"
        mode_hint = "CAUTIOUS_FOLLOW"
        recommended_bias = "prefer_safe_mutations"
        notes.append("Memory weakly favors nearby stable structure.")
    elif gravity_mean <= -0.35:
        memory_effect = "negative_attractor"
        mode_hint = "AVOID"
        recommended_bias = "move_away_from_hazard"
        notes.append("Memory warns about hazardous nearby pattern.")
    elif gravity_mean <= -0.10:
        memory_effect = "weak_negative"
        mode_hint = "CAUTIOUS_AVOID"
        recommended_bias = "avoid_similar_failures"
        notes.append("Memory weakly warns against similar structure.")
    else:
        memory_effect = "neutral_field"
        mode_hint = "NEUTRAL"
        recommended_bias = "explore_freely"
        notes.append("Memory field is too weak to guide strongly.")

    # ---------------------------------------------------------
    # Refine by attractor verdict
    # ---------------------------------------------------------
    if best.verdict.upper() == "BLOCK":
        notes.append("Nearest attractor is a BLOCK-pattern.")
        if recommended_bias == "move_toward_stable_pattern":
            recommended_bias = "prefer_safe_mutations"
        elif recommended_bias == "explore_freely":
            recommended_bias = "avoid_similar_failures"

    elif best.verdict.upper() == "ALLOW":
        notes.append("Nearest attractor is an ALLOW-pattern.")

    elif best.verdict.upper() == "WARN":
        notes.append("Nearest attractor is a WARN-pattern.")

    # ---------------------------------------------------------
    # Refine by confidence
    # ---------------------------------------------------------
    if confidence < 0.20:
        notes.append("Confidence is low; memory signal may be noisy.")
    elif confidence > 0.60:
        notes.append("Confidence is strong; memory signal is consistent.")

    return GravityDecision(
        mode_hint=mode_hint,
        memory_effect=memory_effect,
        confidence=confidence,
        gravity_mean=gravity_mean,
        gravity_max=gravity_max,
        attractor_verdict=best.verdict,
        attractor_band=best.band,
        attractor_phase_state=best.phase_state,
        attractor_octave=best.octave,
        attractor_octave_label=best.octave_label,
        recommended_bias=recommended_bias,
        notes=notes,
    )


def enrich_report_with_gravity(
    report: Dict[str, Any],
    *,
    store_path: str = "memory/memory.jsonl",
) -> Dict[str, Any]:
    """
    Attach gravity guidance into a normal report dict.
    """
    gd = decide_from_gravity(report, store_path=store_path)

    out = dict(report)
    out["gravity_guidance"] = gd.to_dict()
    return out


def main() -> None:
    import json

    demo_report = {
        "kind": "GRAPH_EVAL",
        "verdict": "ALLOW",
        "risk": 0.12,
        "dna": "C0 L0 D1 H1",
        "band": 6,
        "phase_state": 35,
        "flower": {
            "petal_area": 0.08,
        },
    }

    gd = decide_from_gravity(
        demo_report,
        store_path="memory/memory.jsonl",
    )

    print(json.dumps(gd.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
