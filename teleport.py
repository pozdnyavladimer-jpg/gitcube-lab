# -*- coding: utf-8 -*-
"""
teleport.py — Discrete "octave + letter" mapping

Purpose:
- Take a continuous state vector x (features in [0..1], intention in [-1..1])
- Produce:
  - octave O1..O7 (coarse level)
  - letter (stable geometry label) derived from topology (bitmask)
- Provides test cases and a small Monte-Carlo distribution.
"""

from __future__ import annotations
import math
import random
from typing import List, Tuple, Dict


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


# Indices: 0 Resonance, 1 Entropy, 2 Intention, 3 Structure, 4 Pressure, 5 Stability, 6 Novelty
WEIGHTS = [1.5, -1.2, 1.0, 1.0, 0.8, 1.2, 0.9]
THRESHOLDS = [0.80, 0.30, 0.50, 0.70, 0.60, 0.80, 0.50]

ALPHABET = "0123456789ABCDEFGHIJKLMN"  # 24 symbols


def bitmask_from_x(x: List[float]) -> int:
    m = 0
    for i, v in enumerate(x):
        if i == 1:  # entropy: lower is better
            if v <= THRESHOLDS[i]:
                m |= (1 << i)
        else:
            if v >= THRESHOLDS[i]:
                m |= (1 << i)
    return m


def normalized_energy(x: List[float]) -> float:
    e = 0.0
    for i, v in enumerate(x):
        vv = abs(v) if i == 2 else v  # intention magnitude matters
        e += WEIGHTS[i] * vv
    max_e = sum(w for w in WEIGHTS if w > 0)  # positive sum
    return clamp(e / max_e, 0.0, 1.0)


def stable_letter_from_mask(mask: int) -> str:
    # deterministic, topology-based
    idx = (mask ^ (mask >> 3) ^ (mask >> 1)) % 24
    return ALPHABET[idx]


def octave_from_mask_and_energy(mask: int, e: float) -> int:
    """
    Returns octave index 1..7.
    Hard "locks" first; otherwise energy-based.
    """
    # Lock for "high" (пример: Res+Int+Struct+Stab+Nov active, entropy suppressed)
    lock_O7 = 0b0111101  # bits: 0,2,3,4,5,6? (entropy is bit 1, we exclude it)
    lock_O5 = 0b0001101  # bits: 0,2,3
    if (mask & lock_O7) == lock_O7:
        return 7
    if (mask & lock_O5) == lock_O5:
        return 5
    # fallback: map energy to 1..7
    return max(1, min(7, int(math.floor(e * 7)) + 1))


def get_key(x: List[float]) -> Tuple[str, int, float]:
    mask = bitmask_from_x(x)
    e = normalized_energy(x)
    octave = octave_from_mask_and_energy(mask, e)
    letter = stable_letter_from_mask(mask)
    return f"O{octave}-{letter}", mask, e


def monte_carlo(iterations: int = 10000) -> Dict[str, float]:
    counts = {f"O{i}": 0 for i in range(1, 8)}
    for _ in range(iterations):
        x = [random.random() for _ in range(7)]
        x[2] = random.uniform(-1, 1)  # intention
        key, _, _ = get_key(x)
        o = key.split("-")[0]
        counts[o] += 1
    return {k: v / iterations for k, v in counts.items()}


if __name__ == "__main__":
    tests = {
        "facebook_chaos": [0.20, 0.90, 0.10, 0.20, 0.40, 0.10, 0.80],
        "creator_coherence": [0.92, 0.12, 0.85, 0.82, 0.70, 0.90, 0.62],
        "drop_stability": [0.92, 0.12, 0.85, 0.82, 0.70, 0.75, 0.62],
        "drop_intention": [0.92, 0.12, 0.40, 0.82, 0.70, 0.90, 0.62],
        "spike_entropy": [0.92, 0.40, 0.85, 0.82, 0.70, 0.90, 0.62],
    }

    for name, x in tests.items():
        key, mask, e = get_key(x)
        print(f"{name:14s} -> {key} | mask={bin(mask)} | E={e:.3f}")

    dist = monte_carlo(20000)
    print("\nMonte-Carlo distribution:")
    for k in sorted(dist.keys()):
        print(f"{k}: {dist[k]*100:.2f}%")
