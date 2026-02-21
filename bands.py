# -*- coding: utf-8 -*-
"""Energy bands (1..7) for Topological Memory.

We want a simple, explainable mapping:
- risk is continuous in [0,1]
- band is discrete 1..7

Convention used here:
- band 1 = highest risk / "red" (unstable)
- band 7 = lowest risk / "violet" (stable)

This is intentionally lightweight so it can run in CI.
"""

from __future__ import annotations

import math


def clamp_int(x: int, lo: int, hi: int) -> int:
    return lo if x < lo else hi if x > hi else x


def risk_to_band(risk: float) -> int:
    """Map risk in [0,1] to band 1..7 (high risk -> 1)."""
    r = 0.0 if risk is None else float(risk)
    if r < 0.0:
        r = 0.0
    if r > 1.0:
        r = 1.0
    # 0 -> 7, 1 -> 1
    b = 7 - int(math.floor(r * 6.0 + 1e-9))
    return clamp_int(b, 1, 7)
