# -*- coding: utf-8 -*-
"""
vestibular_kernel.py — Adaptive Comfort Controller (ACC) for VR-like motion

Idea (engineering):
- Measure mismatch between visual motion and physical head motion.
- Compute a discomfort proxy H_vr in [0..1].
- Use hysteresis thresholds to avoid rapid toggling.
- Output recommended mitigation parameters:
  - vignette_strength (0..1)
  - accel_scale (0..1)
  - smoothing (0..1)
  - add_reference_frame (bool)

This is a standalone controller. Unity/Unreal can call it every frame.
"""

from __future__ import annotations
import math
from dataclasses import dataclass


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


@dataclass
class ComfortOutput:
    H_vr: float
    mode: str
    vignette: float
    accel_scale: float
    smoothing: float
    add_reference_frame: bool


class VestibularKernel:
    """
    Inputs each tick:
      - w_head: head angular velocity (rad/s) from IMU
      - w_cam:  camera angular velocity (rad/s) from the virtual camera
      - a_cam:  camera linear acceleration magnitude (m/s^2) or normalized
      - dt: seconds

    Internal:
      - tracks exponential moving average of mismatch -> H_vr
      - hysteresis on mode transitions
    """

    def __init__(
        self,
        *,
        tau: float = 0.8,            # smoothing time constant for H
        w_gain: float = 0.35,        # weight for angular mismatch
        a_gain: float = 0.20,        # weight for acceleration
        # hysteresis thresholds:
        warn_on: float = 0.28,
        warn_off: float = 0.22,
        danger_on: float = 0.38,
        danger_off: float = 0.30,
    ):
        self.tau = max(1e-3, tau)
        self.w_gain = w_gain
        self.a_gain = a_gain
        self.warn_on = warn_on
        self.warn_off = warn_off
        self.danger_on = danger_on
        self.danger_off = danger_off

        self.H = 0.0
        self.mode = "NORMAL"  # NORMAL -> WARN -> DANGER

    def step(self, *, w_head: float, w_cam: float, a_cam: float, dt: float) -> ComfortOutput:
        dt = max(1e-4, dt)

        # mismatch terms
        w_mis = abs(w_cam - w_head)              # rad/s mismatch
        a_mis = abs(a_cam)                       # if already magnitude

        # map to [0..1] softly (tanh-like)
        w_term = 1.0 - math.exp(-self.w_gain * w_mis)
        a_term = 1.0 - math.exp(-self.a_gain * a_mis)

        instant = clamp(0.65 * w_term + 0.35 * a_term, 0.0, 1.0)

        # EMA filter for H
        alpha = 1.0 - math.exp(-dt / self.tau)
        self.H = clamp((1 - alpha) * self.H + alpha * instant, 0.0, 1.0)

        # hysteresis mode switch
        if self.mode == "NORMAL":
            if self.H >= self.warn_on:
                self.mode = "WARN"
        elif self.mode == "WARN":
            if self.H >= self.danger_on:
                self.mode = "DANGER"
            elif self.H <= self.warn_off:
                self.mode = "NORMAL"
        elif self.mode == "DANGER":
            if self.H <= self.danger_off:
                self.mode = "WARN"

        # output policy (simple, explainable)
        if self.mode == "NORMAL":
            vignette = 0.0
            accel_scale = 1.0
            smoothing = 0.0
            add_rf = False
        elif self.mode == "WARN":
            vignette = clamp((self.H - self.warn_off) / max(1e-6, (self.danger_on - self.warn_off)), 0.15, 0.55)
            accel_scale = clamp(1.0 - 0.45 * vignette, 0.55, 1.0)
            smoothing = clamp(0.20 + 0.60 * vignette, 0.20, 0.75)
            add_rf = True
        else:  # DANGER
            vignette = clamp(0.65 + 0.35 * self.H, 0.65, 1.0)
            accel_scale = clamp(0.35, 0.20, 0.50)
            smoothing = clamp(0.75, 0.60, 0.90)
            add_rf = True

        return ComfortOutput(
            H_vr=self.H,
            mode=self.mode,
            vignette=vignette,
            accel_scale=accel_scale,
            smoothing=smoothing,
            add_reference_frame=add_rf,
        )
