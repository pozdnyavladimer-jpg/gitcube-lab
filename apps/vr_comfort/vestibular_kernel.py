# -*- coding: utf-8 -*-
"""
vestibular_kernel.py

Simple VR comfort controller.
Input: visual angular velocity vs head angular velocity, linear accel mismatch
Output: comfort actions (fov_scale, max_turn_rate, vignette_strength)

This is not tied to Unity/Unreal; it's pure math you can port anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class KernelState:
    fatigue: float = 0.0   # 0..1
    last_H: float = 0.0    # last "entropy"


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def compute_entropy(
    *,
    vis_w: float,   # visual angular velocity (deg/s or rad/s, consistent)
    head_w: float,  # real head angular velocity
    vis_a: float,   # visual linear accel
    body_a: float,  # real body accel
) -> float:
    # mismatch as normalized “conflict energy”
    dw = abs(vis_w - head_w)
    da = abs(vis_a - body_a)
    H = 0.6 * dw + 0.4 * da
    return float(H)


def update(
    st: KernelState,
    *,
    vis_w: float,
    head_w: float,
    vis_a: float,
    body_a: float,
    H_WARN: float = 0.28,
    H_DROP: float = 0.33,
) -> Dict[str, float]:
    H = compute_entropy(vis_w=vis_w, head_w=head_w, vis_a=vis_a, body_a=body_a)
    st.last_H = H

    # fatigue accumulates when H is high
    if H > H_WARN:
        st.fatigue = clamp(st.fatigue + 0.02, 0.0, 1.0)
    else:
        st.fatigue = clamp(st.fatigue - 0.01, 0.0, 1.0)

    # convert to actions
    if H >= H_DROP:
        # emergency
        fov_scale = 0.65
        vignette = 1.0
        max_turn = 0.5
    elif H >= H_WARN:
        # soften
        t = (H - H_WARN) / max(1e-6, (H_DROP - H_WARN))
        fov_scale = 1.0 - 0.25 * t - 0.10 * st.fatigue
        vignette = 0.4 + 0.5 * t + 0.3 * st.fatigue
        max_turn = 1.0 - 0.35 * t - 0.25 * st.fatigue
    else:
        fov_scale = 1.0
        vignette = 0.0 + 0.15 * st.fatigue
        max_turn = 1.0

    return {
        "H": float(H),
        "fatigue": float(st.fatigue),
        "fov_scale": clamp(float(fov_scale), 0.6, 1.0),
        "vignette_strength": clamp(float(vignette), 0.0, 1.0),
        "max_turn_rate_scale": clamp(float(max_turn), 0.4, 1.0),
    }
