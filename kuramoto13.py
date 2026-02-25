#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
kuramoto13.py — minimal, reliable simulator that ALWAYS outputs JSON.

Outputs (stdout JSON):
{
  "R_last": float,          # order parameter in [0,1]
  "H_last": float,          # normalized phase entropy in [0,1] (0=ordered, 1=max disorder)
  "metrics": {"R":..., "H":...},
  "params": {...},
  "steps": int,
  "dt": float
}

Optional:
--out report.json   -> also writes JSON to file
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np


def clamp01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def order_parameter(theta: np.ndarray) -> float:
    """
    Kuramoto order parameter R = |mean(exp(i*theta))| in [0,1]
    """
    z = np.exp(1j * theta).mean()
    return float(np.abs(z))


def phase_entropy(theta: np.ndarray, bins: int = 36) -> float:
    """
    Entropy of phase distribution, normalized to [0,1].
    0 -> all phases concentrated, 1 -> uniform distribution.
    """
    # Map phases to [0, 2pi)
    x = np.mod(theta, 2.0 * math.pi)
    hist, _ = np.histogram(x, bins=bins, range=(0.0, 2.0 * math.pi), density=False)
    total = hist.sum()
    if total <= 0:
        return 1.0
    p = hist.astype(np.float64) / float(total)
    p = p[p > 0]
    H = -float(np.sum(p * np.log(p)))
    Hmax = math.log(bins)
    if Hmax <= 0:
        return 1.0
    return clamp01(H / Hmax)


@dataclass
class SimConfig:
    n: int = 13
    steps: int = 2500
    dt: float = 0.02
    beta: float = 0.30
    noise_sigma: float = 0.02
    k0: float = 1.0
    omega_sigma: float = 0.6  # natural frequency spread
    bins: int = 36


def simulate(cfg: SimConfig, seed: int) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)

    n = cfg.n
    dt = cfg.dt
    steps = cfg.steps

    # Natural frequencies (heterogeneity)
    omega = rng.normal(loc=0.0, scale=cfg.omega_sigma, size=n)

    # Initial phases
    theta = rng.uniform(low=0.0, high=2.0 * math.pi, size=n)

    # Coupling strength K is shaped by beta (simple nonlinearity)
    # You can reinterpret beta however you want later; here it's just a scale curve.
    # K grows with beta, but gently.
    K = cfg.k0 * (0.5 + 1.5 * float(cfg.beta))  # beta 0.1..0.6 -> K ~0.65..1.4

    # Euler-Maruyama integration: dθ = [ω + (K/N)*Σ sin(θj-θi)]dt + σ dW
    sqrt_dt = math.sqrt(dt)
    for _ in range(steps):
        # pairwise differences θj - θi
        diffs = theta[None, :] - theta[:, None]
        coupling = (K / n) * np.sum(np.sin(diffs), axis=1)
        dtheta = (omega + coupling) * dt

        # noise term
        if cfg.noise_sigma > 0:
            dtheta += float(cfg.noise_sigma) * rng.normal(size=n) * sqrt_dt

        theta = theta + dtheta

        # keep numbers bounded (optional)
        theta = np.mod(theta, 2.0 * math.pi)

    R_last = order_parameter(theta)
    H_last = phase_entropy(theta, bins=cfg.bins)

    return {
        "R_last": float(R_last),
        "H_last": float(H_last),
        "metrics": {"R": float(R_last), "H": float(H_last)},
        "params": {
            "seed": int(seed),
            "n": int(cfg.n),
            "steps": int(cfg.steps),
            "dt": float(cfg.dt),
            "beta": float(cfg.beta),
            "noise_sigma": float(cfg.noise_sigma),
            "K": float(K),
            "omega_sigma": float(cfg.omega_sigma),
            "bins": int(cfg.bins),
        },
        "steps": int(cfg.steps),
        "dt": float(cfg.dt),
    }


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Kuramoto(13) simulator that outputs JSON report.")
    p.add_argument("--seed", type=int, default=1, help="RNG seed")
    p.add_argument("--beta", type=float, default=0.30, help="Nonlinearity/control parameter (0..1 typical)")
    p.add_argument("--noise_sigma", type=float, default=0.02, help="Noise sigma (0..0.2 typical)")
    p.add_argument("--steps", type=int, default=2500, help="Simulation steps")
    p.add_argument("--dt", type=float, default=0.02, help="Time step")
    p.add_argument("--n", type=int, default=13, help="Number of oscillators (default 13)")
    p.add_argument("--omega_sigma", type=float, default=0.6, help="Natural frequency spread")
    p.add_argument("--bins", type=int, default=36, help="Bins for phase entropy")
    p.add_argument("--out", type=str, default="", help="Optional path to also write report JSON file")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    cfg = SimConfig(
        n=int(args.n),
        steps=int(args.steps),
        dt=float(args.dt),
        beta=float(args.beta),
        noise_sigma=float(args.noise_sigma),
        omega_sigma=float(args.omega_sigma),
        bins=int(args.bins),
    )

    try:
        report = simulate(cfg, seed=int(args.seed))
        out_json = json.dumps(report, ensure_ascii=False)
        print(out_json)

        if args.out:
            out_path = args.out
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(out_json + "\n")

        return 0

    except Exception as e:
        # Always output JSON, even on failure
        err = {
            "error": str(e),
            "params": {
                "seed": int(args.seed),
                "beta": float(args.beta),
                "noise_sigma": float(args.noise_sigma),
                "steps": int(args.steps),
                "dt": float(args.dt),
                "n": int(args.n),
                "omega_sigma": float(args.omega_sigma),
                "bins": int(args.bins),
            },
        }
        print(json.dumps(err, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
