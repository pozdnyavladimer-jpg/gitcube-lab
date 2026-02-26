# -*- coding: utf-8 -*-
"""
Kuramoto-13 (Self-controlled coupling K(t) + basic telemetry)

Goal:
- Simulate n=13 phase oscillators with noise.
- Track synchronization R(t) and phase-entropy H(t).
- Simple feedback controller adjusts K(t) to push toward targets.
- Emits a CRYSTAL event when (R >= R_gate and H <= H_gate) holds for N steps.

Notes:
- This is a clean "engine" file: no Drive, no Colab specifics.
- You can later wire CRYSTAL events to your memory.jsonl writer.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def wrap_angle(a: float) -> float:
    # wrap to (-pi, pi]
    while a <= -math.pi:
        a += 2 * math.pi
    while a > math.pi:
        a -= 2 * math.pi
    return a


def order_parameter(theta: List[float]) -> float:
    # R = |(1/n) Σ exp(iθ)|
    n = len(theta)
    c = sum(math.cos(t) for t in theta) / n
    s = sum(math.sin(t) for t in theta) / n
    return math.sqrt(c * c + s * s)


def phase_entropy(theta: List[float], bins: int = 24) -> float:
    """
    Simple histogram entropy of phase angles.
    Returns H in [0,1] (normalized by log(bins)).
    """
    if bins < 4:
        bins = 4
    counts = [0] * bins
    for t in theta:
        # map (-pi,pi] -> [0,1)
        u = (t + math.pi) / (2 * math.pi)
        idx = int(u * bins)
        if idx == bins:
            idx = bins - 1
        counts[idx] += 1

    n = len(theta)
    if n == 0:
        return 0.0

    eps = 1e-12
    h = 0.0
    for c in counts:
        if c <= 0:
            continue
        p = c / n
        h -= p * math.log(p + eps)

    h_max = math.log(bins + eps)
    return clamp(h / h_max, 0.0, 1.0)


@dataclass
class CrystalEvent:
    step: int
    R: float
    H: float
    K: float
    key: str
    theta_quant: List[int]


def quantize_theta(theta: List[float], deg_step: float = 15.0) -> List[int]:
    """
    Quantize each theta to a discrete bucket of size deg_step (in degrees),
    mapped to integer bins in [0, 360/deg_step).
    """
    step_rad = (deg_step * math.pi) / 180.0
    m = int(round((2 * math.pi) / step_rad))
    if m <= 0:
        m = 24
    out = []
    for t in theta:
        # map (-pi,pi] -> [0,2pi)
        u = t + math.pi
        idx = int(round(u / (2 * math.pi) * (m - 1)))
        idx = max(0, min(idx, m - 1))
        out.append(idx)
    return out


def make_crystal_key(theta_q: List[int]) -> str:
    """
    Deterministic "DNA-like" key from quantized theta.
    Keep it short but stable.
    """
    # simple rolling hash -> base36-ish alphabet
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    h = 2166136261  # FNV-ish start
    for v in theta_q:
        h ^= (v + 1)
        h = (h * 16777619) & 0xFFFFFFFF

    # produce 8 chars
    s = []
    x = h
    for _ in range(8):
        s.append(alphabet[x % len(alphabet)])
        x //= len(alphabet)
    return "K13-" + "".join(s)


def simulate(
    *,
    seed: int = 42,
    n: int = 13,
    steps: int = 4000,
    dt: float = 0.02,
    noise_sigma: float = 0.10,
    # natural frequencies:
    omega_center: float = 0.0,
    omega_spread: float = 1.0,
    # feedback controller targets:
    R_target: float = 0.88,
    H_target: float = 0.22,
    # controller gains:
    alpha: float = 0.8,   # push by (R_target - R)
    beta: float = 0.6,    # push by (H - H_target)
    gamma: float = 0.15,  # damping toward K_base
    K_base: float = 1.2,
    K_min: float = 0.05,
    K_max: float = 8.0,
    # CRYSTAL gate:
    R_gate: float = 0.88,
    H_gate: float = 0.22,
    hold_steps: int = 80,
    # quantization for key:
    quant_deg: float = 15.0,
) -> Dict[str, Any]:
    """
    Returns telemetry arrays + list of CrystalEvent.
    """
    rng = random.Random(seed)

    # init phases and natural freqs
    theta = [rng.uniform(-math.pi, math.pi) for _ in range(n)]
    omega = [omega_center + rng.uniform(-omega_spread, omega_spread) for _ in range(n)]

    K = K_base

    Rs: List[float] = []
    Hs: List[float] = []
    Ks: List[float] = []
    events: List[CrystalEvent] = []

    gate_count = 0

    for t in range(steps):
        # compute metrics
        R = order_parameter(theta)
        H = phase_entropy(theta, bins=24)

        Rs.append(R)
        Hs.append(H)
        Ks.append(K)

        # gate detector
        if (R >= R_gate) and (H <= H_gate):
            gate_count += 1
        else:
            gate_count = 0

        if gate_count == hold_steps:
            theta_q = quantize_theta(theta, deg_step=quant_deg)
            key = make_crystal_key(theta_q)
            events.append(CrystalEvent(step=t, R=R, H=H, K=K, key=key, theta_quant=theta_q))

        # --- feedback controller for K(t) ---
        # Intuition:
        # - If R below target -> increase K.
        # - If H above target -> increase K (more coupling to reduce disorder).
        # - Add damping toward base to avoid runaway.
        dK = alpha * (R_target - R) + beta * (H - H_target) - gamma * (K - K_base)
        K = clamp(K + dt * dK, K_min, K_max)

        # --- Kuramoto step (Euler-Maruyama) ---
        # dθ_i = ω_i dt + (K/n) Σ sin(θ_j - θ_i) dt + σ dW
        new_theta = []
        for i in range(n):
            coupling_sum = 0.0
            ti = theta[i]
            for j in range(n):
                coupling_sum += math.sin(theta[j] - ti)
            coupling = (K / n) * coupling_sum

            noise = noise_sigma * math.sqrt(dt) * rng.gauss(0.0, 1.0)
            ti_new = ti + (omega[i] + coupling) * dt + noise
            new_theta.append(wrap_angle(ti_new))
        theta = new_theta

    return {
        "params": {
            "seed": seed, "n": n, "steps": steps, "dt": dt,
            "noise_sigma": noise_sigma, "omega_center": omega_center, "omega_spread": omega_spread,
            "R_target": R_target, "H_target": H_target,
            "alpha": alpha, "beta": beta, "gamma": gamma,
            "K_base": K_base, "K_min": K_min, "K_max": K_max,
            "R_gate": R_gate, "H_gate": H_gate, "hold_steps": hold_steps,
            "quant_deg": quant_deg,
        },
        "telemetry": {"R": Rs, "H": Hs, "K": Ks},
        "events": [e.__dict__ for e in events],
    }


if __name__ == "__main__":
    # Minimal CLI-like run (prints summary only)
    out = simulate(seed=1, steps=3000, noise_sigma=0.12)
    events = out["events"]
    last_R = out["telemetry"]["R"][-1]
    last_H = out["telemetry"]["H"][-1]
    last_K = out["telemetry"]["K"][-1]
    print(f"done: last R={last_R:.3f}, H={last_H:.3f}, K={last_K:.3f}, events={len(events)}")
    if events:
        print("first event:", events[0]["key"], "at step", events[0]["step"])
