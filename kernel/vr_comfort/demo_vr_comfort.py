# -*- coding: utf-8 -*-
"""
kernel/vr_comfort/demo_vr_comfort.py

Simulate a VR session with 3 phases:
1. normal motion
2. mismatch spikes ("VR rollercoaster")
3. recovery

Run:
  PYTHONPATH=. python -m kernel.vr_comfort.demo_vr_comfort
"""

from __future__ import annotations

import math
import random

from kernel.vr_comfort.vestibular_kernel import VestibularKernel


def main() -> None:
    rng = random.Random(1)
    k = VestibularKernel()

    dt = 1.0 / 60.0
    t = 0.0

    print("=" * 72)
    print("VR COMFORT DEMO")
    print("=" * 72)

    # 30 seconds total, 60 FPS
    for step in range(60 * 30):
        t += dt

        if t < 8.0:
            # normal motion: visual follows head fairly well
            w_head = 0.6 * math.sin(0.6 * t)
            w_cam = w_head + 0.05 * rng.gauss(0.0, 1.0)
            a_cam = 0.4 + 0.1 * rng.random()

        elif t < 20.0:
            # mismatch: camera swings hard while body stays calm
            w_head = 0.2 * math.sin(0.4 * t)
            w_cam = 2.0 * math.sin(1.6 * t) + 0.2 * rng.gauss(0.0, 1.0)
            a_cam = 3.0 + 0.8 * rng.random()

        else:
            # recover: visual motion tracks head again
            w_head = 0.5 * math.sin(0.6 * t)
            w_cam = w_head + 0.07 * rng.gauss(0.0, 1.0)
            a_cam = 0.6 + 0.15 * rng.random()

        out = k.step(
            w_head=w_head,
            w_cam=w_cam,
            a_cam=a_cam,
            dt=dt,
            body_a=0.0,
        )

        # print twice per second
        if step % 30 == 0:
            print(
                f"t={t:5.1f}s | "
                f"H={out.H_vr:5.3f} | "
                f"fatigue={out.fatigue:4.2f} | "
                f"mode={out.mode:4s} | "
                f"vignette={out.vignette:4.2f} | "
                f"accel={out.accel_scale:4.2f} | "
                f"smooth={out.smoothing:4.2f} | "
                f"ref_frame={out.add_reference_frame}"
            )

    print("-" * 72)
    print("done")
    print("=" * 72)


if __name__ == "__main__":
    main()
