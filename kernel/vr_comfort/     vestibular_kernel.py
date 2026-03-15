# -*- coding: utf-8 -*-
"""
kernel/vr_comfort/vestibular_kernel.py

Simple VR comfort controller.

Idea:
- compare visual motion with real head/body motion
- compute a discomfort proxy H_vr
- accumulate fatigue when mismatch stays high
- return mitigation actions for the renderer / locomotion system

This file is engine-only and can be ported to Unity, Unreal, Godot, etc.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KernelOutput:
    """Single-step output of the VR comfort controller."""
    H_vr: float
    fatigue: float
    mode: str
    vignette: float
    accel_scale: float
    smoothing: float
    add_reference_frame: bool


@dataclass
class KernelState:
    """Internal adaptive state."""
    fatigue: float = 0.0   # 0..1
    last_H: float = 0.0    # last discomfort / entropy proxy


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


class VestibularKernel:
    """
    Minimal adaptive VR comfort controller.

    Inputs:
    - w_head: real head angular velocity
    - w_cam : visual / camera angular velocity
    - a_cam : visual linear acceleration
    - body_a: real body linear acceleration (default 0.0)

    Output:
    - H_vr: discomfort proxy
    - mode: OK / SOFT / HARD
    - vignette: 0..1
    - accel_scale: 0..1
    - smoothing: 0..1
    - add_reference_frame: bool
    """

    def __init__(
        self,
        *,
        H_WARN: float = 0.28,
        H_DROP: float = 0.33,
        fatigue_up: float = 0.02,
        fatigue_down: float = 0.01,
    ) -> None:
        self.state = KernelState()
        self.H_WARN = float(H_WARN)
        self.H_DROP = float(H_DROP)
        self.fatigue_up = float(fatigue_up)
        self.fatigue_down = float(fatigue_down)

    @staticmethod
    def compute_entropy(
        *,
        vis_w: float,
        head_w: float,
        vis_a: float,
        body_a: float,
    ) -> float:
        """
        Discomfort / conflict proxy.
        Higher when visual motion disagrees with real motion.
        """
        dw = abs(vis_w - head_w)
        da = abs(vis_a - body_a)
        H = 0.6 * dw + 0.4 * da
        return float(H)

    def step(
        self,
        *,
        w_head: float,
        w_cam: float,
        a_cam: float,
        dt: float,
        body_a: float = 0.0,
    ) -> KernelOutput:
        """
        Advance the controller by one frame.

        dt is currently accepted for API stability / future tuning,
        even though the present version uses fixed fatigue increments.
        """
        _ = dt  # reserved for future use

        H = self.compute_entropy(
            vis_w=w_cam,
            head_w=w_head,
            vis_a=a_cam,
            body_a=body_a,
        )
        self.state.last_H = H

        # fatigue accumulates under sustained mismatch
        if H > self.H_WARN:
            self.state.fatigue = clamp(self.state.fatigue + self.fatigue_up, 0.0, 1.0)
        else:
            self.state.fatigue = clamp(self.state.fatigue - self.fatigue_down, 0.0, 1.0)

        fatigue = self.state.fatigue

        # action policy
        if H >= self.H_DROP:
            mode = "HARD"
            vignette = 1.0
            accel_scale = 0.50
            smoothing = 0.85
            add_reference_frame = True

        elif H >= self.H_WARN:
            mode = "SOFT"
            t = (H - self.H_WARN) / max(1e-6, (self.H_DROP - self.H_WARN))

            vignette = 0.40 + 0.50 * t + 0.30 * fatigue
            accel_scale = 1.00 - 0.35 * t - 0.25 * fatigue
            smoothing = 0.35 + 0.35 * t + 0.20 * fatigue
            add_reference_frame = (t > 0.35) or (fatigue > 0.45)

        else:
            mode = "OK"
            vignette = 0.15 * fatigue
            accel_scale = 1.00
            smoothing = 0.08 + 0.12 * fatigue
            add_reference_frame = False

        return KernelOutput(
            H_vr=float(H),
            fatigue=float(fatigue),
            mode=mode,
            vignette=clamp(float(vignette), 0.0, 1.0),
            accel_scale=clamp(float(accel_scale), 0.4, 1.0),
            smoothing=clamp(float(smoothing), 0.0, 1.0),
            add_reference_frame=bool(add_reference_frame),
        )
