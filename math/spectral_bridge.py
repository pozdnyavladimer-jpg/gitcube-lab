# -*- coding: utf-8 -*-
"""
Spectral bridge for GitCube:
maps structural report -> spectral phase (1..6) -> color -> wave cycle.

3 phases forward (expansion):
    1 RED      (impulse / pressure)
    2 ORANGE   (flow / exploration)
    3 YELLOW   (structure / analysis)

3 phases backward (compression):
    4 GREEN    (balance / stabilization)
    5 BLUE     (law / memory)
    6 VIOLET   (transformation / next state)
"""

from __future__ import annotations

from typing import Dict, Any


# ---------------------------------------------------------
# Phase → color
# ---------------------------------------------------------

PHASE_TO_COLOR = {
    1: "RED",
    2: "ORANGE",
    3: "YELLOW",
    4: "GREEN",
    5: "BLUE",
    6: "VIOLET",
}


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _get_metric(report: Dict[str, Any], key: str, default: float = 0.0) -> float:
    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    return float(metrics.get(key, default) or default)


# ---------------------------------------------------------
# Core mapping
# ---------------------------------------------------------

def spectral_phase(report: Dict[str, Any]) -> int:
    """
    Map report -> phase (1..6)

    Uses:
    - risk
    - entropy
    - density
    - cycles
    """

    risk = float(report.get("risk", 0.0) or 0.0)
    entropy = _get_metric(report, "entropy", 0.0)
    density = _get_metric(report, "density", 0.0)
    cycles = _get_metric(report, "cycles", 0.0)

    # --- Phase logic ---

    # 🔴 Phase 1: high pressure / chaos
    if risk > 0.75:
        return 1

    # 🟠 Phase 2: active instability / exploration
    if risk > 0.55 or cycles > 0:
        return 2

    # 🟡 Phase 3: structured but still unstable
    if entropy > 0.5 or density > 0.4:
        return 3

    # 🟢 Phase 4: stabilizing
    if risk > 0.25:
        return 4

    # 🔵 Phase 5: stable + structured
    if risk > 0.10:
        return 5

    # 🟣 Phase 6: near-optimal / transformed
    return 6


def spectral_color(report: Dict[str, Any]) -> str:
    phase = spectral_phase(report)
    return PHASE_TO_COLOR.get(phase, "UNKNOWN")


def wave_direction(phase: int) -> str:
    """
    Determine wave direction:
    """
    if phase <= 3:
        return "EXPAND"   # 3 туди
    return "COMPRESS"     # 3 назад


def spectral_state(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full spectral state for logs / memory
    """
    phase = spectral_phase(report)
    color = PHASE_TO_COLOR.get(phase, "UNKNOWN")

    return {
        "phase": phase,
        "color": color,
        "direction": wave_direction(phase),
        "cycle_position": f"{phase}/6",
    }


# ---------------------------------------------------------
# Pretty
# ---------------------------------------------------------

def pretty_spectral(report: Dict[str, Any]) -> str:
    s = spectral_state(report)
    return (
        f"{s['color']} | phase={s['phase']} "
        f"| dir={s['direction']} "
        f"| cycle={s['cycle_position']}"
    )
