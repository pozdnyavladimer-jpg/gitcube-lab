# -*- coding: utf-8 -*-
"""
demo_vr_comfort.py — Simulate a session with periods of mismatch and show kernel outputs.
Run:
  python apps/vr_comfort/demo_vr_comfort.py
"""

from __future__ import annotations
import math
import random
from time import sleep
from apps.vr_comfort.vestibular_kernel import VestibularKernel


def main():
    rng = random.Random(1)
    k = VestibularKernel()

    dt = 1 / 60.0
    t = 0.0

    # 3 phases: normal -> mismatch spikes -> recover
    for step in range(60 * 30):  # 30s
        t += dt

        if t < 8.0:
            w_head = 0.6 * math.sin(0.6 * t)
            w_cam = w_head + 0.05 * rng.gauss(0, 1)
            a_cam = 0.4 + 0.1 * rng.random()
        elif t < 20.0:
            # big visual motion while head is quiet -> "VR rollercoaster"
            w_head = 0.2 * math.sin(0.4 * t)
            w_cam = 2.0 * math.sin(1.6 * t) + 0.2 * rng.gauss(0, 1)
            a_cam = 3.0 + 0.8 * rng.random()
        else:
            # recover
            w_head = 0.5 * math.sin(0.6 * t)
            w_cam = w_head + 0.07 * rng.gauss(0, 1)
            a_cam = 0.6 + 0.15 * rng.random()

        out = k.step(w_head=w_head, w_cam=w_cam, a_cam=a_cam, dt=dt)

        if step % 30 == 0:  # print twice a second
            print(
                f"t={t:5.1f}s  H={out.H_vr:.3f}  mode={out.mode:6s}  "
                f"vignette={out.vignette:.2f} accel={out.accel_scale:.2f} smooth={out.smoothing:.2f} rf={out.add_reference_frame}"
            )

    print("done")


if __name__ == "__main__":
    main()
