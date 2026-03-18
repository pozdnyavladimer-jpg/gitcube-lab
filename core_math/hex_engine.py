# core_math/hex_engine.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict


def _clip01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _get_metric(report: Dict[str, Any], key: str, default: float = 0.0) -> float:
    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    try:
        return float(metrics.get(key, default) or default)
    except Exception:
        return float(default)


def hexagram_vectors(report: Dict[str, Any]) -> Dict[str, float]:
    """
    Convert a GraphEval report into 6 normalized rays [0..1].

    Rays:
      red_mass       - graph weight / pressure
      orange_flow    - entropy / motion
      yellow_struct  - density / structural packing
      green_balance  - anti-cycle / anti-chaos balance
      blue_law       - rule compliance / layer discipline
      violet_future  - extensibility / low-risk future potential
    """

    risk = _clip01(float(report.get("risk", 0.0) or 0.0))

    n = _get_metric(report, "N", 0.0)
    e = _get_metric(report, "E", 0.0)
    density = _clip01(_get_metric(report, "density", 0.0))
    entropy = _clip01(_get_metric(report, "entropy", 0.0))

    strict_cycle_nodes = _get_metric(report, "strict_cycle_nodes", 0.0)
    layer_viol = _get_metric(report, "layer_viol", 0.0)
    deadly_pairs = _get_metric(report, "deadly_pairs", 0.0)
    strict_count = _get_metric(report, "strict_count", 0.0)

    # --- RED: mass / pressure
    # crude normalized graph weight
    red_mass = _clip01((n + e) / 20.0)

    # --- ORANGE: flow / motion
    orange_flow = entropy

    # --- YELLOW: structure / packing
    yellow_struct = density

    # --- GREEN: balance
    # high if fewer cycle-like structural tensions
    green_balance = _clip01(1.0 - min(1.0, strict_cycle_nodes / 3.0))

    # --- BLUE: law
    # high if fewer explicit rule violations
    law_penalty = min(1.0, (layer_viol + deadly_pairs + strict_count) / 6.0)
    blue_law = _clip01(1.0 - law_penalty)

    # --- VIOLET: future
    # high if risk is low
    violet_future = _clip01(1.0 - risk)

    return {
        "red_mass": red_mass,
        "orange_flow": orange_flow,
        "yellow_struct": yellow_struct,
        "green_balance": green_balance,
        "blue_law": blue_law,
        "violet_future": violet_future,
    }


def hexagram_tilt(v: Dict[str, float]) -> Dict[str, float]:
    """
    Three paired tensions:
      mass vs future
      flow vs law
      structure vs balance
    Positive value means left term dominates.
    """
    return {
        "mass_vs_future": float(v["red_mass"] - v["violet_future"]),
        "flow_vs_law": float(v["orange_flow"] - v["blue_law"]),
        "structure_vs_balance": float(v["yellow_struct"] - v["green_balance"]),
    }


def hexagram_score(v: Dict[str, float]) -> float:
    """
    Average health score of the 6-ray state.
    Higher is better.
    """
    vals = [
        1.0 - v["red_mass"],   # less mass pressure is better
        v["orange_flow"],      # some flow is good
        1.0 - v["yellow_struct"],  # too much packing is bad
        v["green_balance"],
        v["blue_law"],
        v["violet_future"],
    ]
    return sum(vals) / float(len(vals))


def hexagram_state(report: Dict[str, Any]) -> Dict[str, Any]:
    v = hexagram_vectors(report)
    tilt = hexagram_tilt(v)
    score = hexagram_score(v)

    dominant_shadow = max(
        [
            ("RED", v["red_mass"]),
            ("ORANGE", v["orange_flow"]),
            ("YELLOW", v["yellow_struct"]),
        ],
        key=lambda x: x[1],
    )[0]

    dominant_stability = max(
        [
            ("GREEN", v["green_balance"]),
            ("BLUE", v["blue_law"]),
            ("VIOLET", v["violet_future"]),
        ],
        key=lambda x: x[1],
    )[0]

    return {
        "vectors": v,
        "tilt": tilt,
        "score": score,
        "dominant_shadow": dominant_shadow,
        "dominant_stability": dominant_stability,
    }


def pretty_hexagram(report: Dict[str, Any]) -> str:
    h = report.get("hexagram")
    if not isinstance(h, dict):
        h = hexagram_state(report)

    v = h["vectors"]
    return (
        "HEX | "
        f"R={v['red_mass']:.2f} "
        f"O={v['orange_flow']:.2f} "
        f"Y={v['yellow_struct']:.2f} "
        f"G={v['green_balance']:.2f} "
        f"B={v['blue_law']:.2f} "
        f"V={v['violet_future']:.2f} "
        f"| tilt={h['tilt']}"
    )
