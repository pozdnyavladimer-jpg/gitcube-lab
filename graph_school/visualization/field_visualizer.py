# -*- coding: utf-8 -*-
"""
field_visualizer.py

Simple console visualizer for Graph School pressure field.

Shows:
- resonance mode
- total pressure
- component bars
- mutation priorities

Usage example:
  export PYTHONPATH=$(pwd)
  python -m graph_school.visualization.field_visualizer
"""

from __future__ import annotations

from typing import Dict, List

from agent.resonance_controller import (
    ResonanceState,
    update,
    report_to_vector,
    mode_to_mutations,
)


BAR_WIDTH = 28


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def bar(value: float, scale: float = 3.0, width: int = BAR_WIDTH) -> str:
    """
    Draw a simple ASCII bar.
    """
    v = clamp(value / scale, 0.0, 1.0)
    filled = int(round(v * width))
    return "█" * filled + "·" * (width - filled)


def vector_to_named_components(vec: List[float]) -> Dict[str, float]:
    names = [
        "cycles",
        "layers",
        "toxins",
        "feedback",
        "density",
        "entropy",
    ]
    return {name: float(vec[i]) for i, name in enumerate(names)}


def render_field(report: Dict) -> str:
    state = ResonanceState()
    state = update(state, report)

    vec = report_to_vector(report)
    named = vector_to_named_components(vec)
    priorities = mode_to_mutations(state.mode)

    lines: List[str] = []
    lines.append("=" * 72)
    lines.append("GRAPH SCHOOL — PRESSURE FIELD")
    lines.append("=" * 72)
    lines.append(f"mode     : {state.mode}")
    lines.append(f"pressure : {state.pressure:.3f}")
    lines.append("")

    lines.append("components:")
    for key, value in named.items():
        lines.append(f"  {key:10s} {value:6.3f} | {bar(value)}")

    lines.append("")
    lines.append("mutation priorities:")
    if priorities:
        for i, m in enumerate(priorities, start=1):
            lines.append(f"  {i}. {m}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("verdict:")
    lines.append(f"  {report.get('verdict', 'UNKNOWN')}")

    lines.append("=" * 72)
    return "\n".join(lines)


def example_report_block() -> Dict:
    """
    Demo report compatible with the current resonance controller.
    This is a synthetic example for visual testing.
    """
    return {
        "verdict": "BLOCK",
        "cycles": 1.0,
        "layer_violations": 0.0,
        "toxins": 0.0,
        "feedback_edges": 1.0,
        "edge_density": 0.42,
        "entropy": 0.35,
    }


def example_report_soft() -> Dict:
    return {
        "verdict": "WARN",
        "cycles": 0.0,
        "layer_violations": 0.4,
        "toxins": 0.0,
        "feedback_edges": 0.0,
        "edge_density": 0.30,
        "entropy": 0.20,
    }


def example_report_ok() -> Dict:
    return {
        "verdict": "ALLOW",
        "cycles": 0.0,
        "layer_violations": 0.0,
        "toxins": 0.0,
        "feedback_edges": 0.0,
        "edge_density": 0.10,
        "entropy": 0.08,
    }


def main() -> None:
    examples = [
        ("UNSTABLE / BLOCK example", example_report_block()),
        ("SOFT / WARN example", example_report_soft()),
        ("OK / ALLOW example", example_report_ok()),
    ]

    for title, report in examples:
        print()
        print(title)
        print(render_field(report))


if __name__ == "__main__":
    main()
