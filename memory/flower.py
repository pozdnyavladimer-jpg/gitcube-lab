# -*- coding: utf-8 -*-
"""
Flower invariant utilities (Topological Memory)
- Computes "petal area" (hysteresis) for a 6-step cycle
- Pure math, no dependencies

We use the polygon area (shoelace formula) in (risk, specH) plane.
If the system goes 3 steps forward and 3 steps back, state may return,
but the path can enclose non-zero area => invariant of trajectory.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple, Dict, Any


Point = Tuple[float, float]


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def shoelace_area(points: Sequence[Point]) -> float:
    """
    Area of a polygon defined by points (x,y).
    If points are not closed, we close automatically.
    Returns non-negative area.
    """
    n = len(points)
    if n < 3:
        return 0.0

    area2 = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area2 += x1 * y2 - x2 * y1
    return abs(area2) * 0.5


def flower_from_cycle(
    cycle: Iterable[Dict[str, Any]],
    *,
    x_key: str = "risk",
    y_key: str = "specH",
    take: int = 6,
) -> Dict[str, Any]:
    """
    cycle: iterable of dicts with at least (risk, specH), length>=6 recommended.
    Returns:
      {
        "petal_area": float,
        "points": [(risk, specH), ...]  # up to 6
      }
    """
    pts: List[Point] = []
    for item in cycle:
        if not isinstance(item, dict):
            continue
        x = _to_float(item.get(x_key), 0.0)
        y = _to_float(item.get(y_key), 0.0)
        pts.append((x, y))
        if len(pts) >= take:
            break

    area = shoelace_area(pts)
    return {"petal_area": float(area), "points": pts}
