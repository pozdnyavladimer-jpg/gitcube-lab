# -*- coding: utf-8 -*-
"""
resonance_controller.py

Translate GraphEval report → system pressure vector → control mode.

This acts like a physical regulator for graph architecture search.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ResonanceState:
    pressure: float = 0.0
    mode: str = "OK"


# ----------------------------------------
# Convert GraphEval report → pressure vector
# ----------------------------------------

def report_to_vector(report: Dict) -> List[float]:

    cycles = float(report.get("cycles", 0))
    layers = float(report.get("layer_violations", 0))
    toxins = float(report.get("toxins", 0))
    feedback = float(report.get("feedback_edges", 0))
    density = float(report.get("edge_density", 0))
    entropy = float(report.get("entropy", 0))

    return [
        cycles,
        layers,
        toxins,
        feedback,
        density,
        entropy,
    ]


# ----------------------------------------
# Compute structural pressure
# ----------------------------------------

def compute_pressure(vec: List[float]) -> float:

    w = [
        1.4,  # cycles
        1.2,  # layers
        1.0,  # toxins
        0.8,  # feedback
        0.4,  # density
        0.6,  # entropy
    ]

    p = 0.0
    for i in range(len(vec)):
        p += vec[i] * w[i]

    return p


# ----------------------------------------
# Convert pressure → system mode
# ----------------------------------------

def pressure_to_mode(p: float) -> str:

    if p < 0.5:
        return "OK"

    if p < 1.5:
        return "SOFT"

    if p < 3.0:
        return "HARD"

    return "UNSTABLE"


# ----------------------------------------
# Main control step
# ----------------------------------------

def update(state: ResonanceState, report: Dict) -> ResonanceState:

    vec = report_to_vector(report)

    p = compute_pressure(vec)

    mode = pressure_to_mode(p)

    state.pressure = p
    state.mode = mode

    return state


# ----------------------------------------
# Mutation priority
# ----------------------------------------

def mode_to_mutations(mode: str):

    if mode == "OK":
        return [
            "refactor",
            "optimize",
        ]

    if mode == "SOFT":
        return [
            "reroute_edge",
            "insert_adapter",
            "reduce_density",
        ]

    if mode == "HARD":
        return [
            "break_cycle",
            "remove_feedback",
            "split_node",
        ]

    if mode == "UNSTABLE":
        return [
            "hard_prune",
            "cut_edge",
            "reset_branch",
        ]

    return []
