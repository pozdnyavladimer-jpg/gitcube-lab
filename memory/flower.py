# -*- coding: utf-8 -*-
"""
Flower invariant (6-step cycle):
- compute petal area in (risk, specH) plane using shoelace formula
- extract points from report["flower_cycle"] if present

We store:
  flower = {
    "petal_area": float,
    "points": [[risk, specH], ...]
  }
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple


def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


def shoelace_area(points: List[Tuple[float, float]]) -> float:
    """
    Discrete polygon area (absolute), points expected in order.
    """
    n = len(points)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def extract_flower(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read report["flower_cycle"] as list of dicts: [{"risk":..., "specH":...}, ...]
    Returns {} if not present.
    """
    cyc = report.get("flower_cycle")
    if not isinstance(cyc, list) or not cyc:
        return {}

    pts: List[Tuple[float, float]] = []
    for item in cyc:
        if not isinstance(item, dict):
            continue
        x = _num(item.get("risk"), 0.0)
        y = _num(item.get("specH"), _num(item.get("spectral_entropy"), 0.0))
        pts.append((x, y))

    if len(pts) < 3:
        return {}

    area = shoelace_area(pts)
    return {
        "petal_area": float(area),
        "points": [[float(x), float(y)] for x, y in pts],
    }
