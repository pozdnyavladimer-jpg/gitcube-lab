# -*- coding: utf-8 -*-
"""
HFS Demo (Human Function Stream) — v0.2 (Wave-aware)

Adds:
- Spectral entropy (wave instability)
- CUSUM early drift detection
- Hybrid regulator preserved (μ+2σ / μ+3σ)

License: AGPL-3.0
Author: Володимир Поздняк
"""

from __future__ import annotations
import json
import math
import random
import time
import argparse
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple


# ---------------------------
# Basic math
# ---------------------------

def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def mean_std(xs: List[float]) -> Tuple[float, float]:
    if not xs:
        return 0.0, 0.0
    m = sum(xs) / len(xs)
    v = sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1)
    return m, math.sqrt(v)


# ---------------------------
# Signal Processing
# ---------------------------

def spectral_entropy(xs: List[float]) -> float:
    """
    Spectral entropy (0..1)
    Higher = more chaotic spectrum
    """
    n = len(xs)
    if n < 8:
        return 0.0

    m = sum(xs) / n
    ys = [x - m for x in xs]

    mags = []
    for k in range(1, n // 2 + 1):
        re = 0.0
        im = 0.0
        for t, y in enumerate(ys):
            ang = 2.0 * math.pi * k * t / n
            re += y * math.cos(ang)
            im -= y * math.sin(ang)
        mags.append(re * re + im * im)

    total = sum(mags)
    if total <= 1e-12:
        return 0.0

    ps = [p / total for p in mags]
    h = -sum(p * math.log(p + 1e-12) for p in ps)
    h_max = math.log(len(ps) + 1e-12)

    return clamp(h / h_max, 0.0, 1.0)


def cusum_alarm(xs: List[float], k: float = 0.02, h: float = 0.15) -> bool:
    """
    Simple one-sided CUSUM drift detector.
    """
    if len(xs) < 10:
        return False

    mu = sum(xs[:-1]) / max(1, len(xs) - 1)
    s = 0.0
    for x in xs:
        s = max(0.0, s + (x - mu - k))
        if s > h:
            return True
    return False


# ---------------------------
# Synthetic generator
# ---------------------------

TOPICS = ["ship", "refactor", "docs", "demo", "ci", "agent"]

@dataclass
class HFSEvent:
    t: float
    topic: str
    edits: int
    pause: float
    structure: float


def generate(seed: int, n: int) -> List[HFSEvent]:
    rng = random.Random(seed)
    t0 = time.time()
    topic = rng.choice(TOPICS)
    pressure = 0.2
    events = []

    for i in range(n):
        if rng.random() < 0.2:
            topic = rng.choice(TOPICS)

        if rng.random() < 0.1:
            pressure = clamp(pressure + rng.uniform(0.25, 0.45), 0.0, 1.0)
        else:
            pressure = clamp(pressure - rng.uniform(0.02, 0.04), 0.0, 1.0)

        edits = int(round(pressure * rng.uniform(0, 6)))
        pause = clamp(rng.gauss(0.6 + pressure, 0.25), 0.05, 3.0)
        structure = clamp(1.0 - pressure + rng.uniform(-0.2, 0.2), 0.0, 1.0)

        events.append(HFSEvent(
            t=t0 + i,
            topic=topic,
            edits=edits,
            pause=pause,
            structure=structure
        ))

    return events


# ---------------------------
# Window metrics
# ---------------------------

@dataclass
class WindowMetrics:
    T: float
    R: float
    S: float
    risk: float
    spectral_entropy: float


def compute_windows(events: List[HFSEvent], window: int = 20) -> Tuple[List[WindowMetrics], List[float]]:
    windows = []
    risk_series = []

    for w0 in range(0, len(events), window):
        chunk = events[w0:w0 + window]
        if not chunk:
            break

        topics = [e.topic for e in chunk]
        edits = sum(e.edits for e in chunk)
        pauses = [e.pause for e in chunk]
        structs = [e.structure for e in chunk]

        topic_switches = sum(1 for a, b in zip(topics, topics[1:]) if a != b)
        T = topic_switches / max(1, len(topics) - 1)
        R = clamp(edits / max(1, len(chunk) * 6), 0.0, 1.0)
        S = clamp(sum(structs) / max(1, len(structs)), 0.0, 1.0)

        base_risk = clamp(
            0.4 * T + 0.3 * R + 0.3 * (1.0 - S),
            0.0, 1.0
        )

        risk_series.append(base_risk)

        # Wave modifier
        specH = spectral_entropy(risk_series[-32:])
        risk = clamp(base_risk + 0.15 * specH, 0.0, 1.0)

        windows.append(WindowMetrics(T, R, S, risk, specH))

    return windows, risk_series


# ---------------------------
# Navigator
# ---------------------------

def navigator(windows: List[WindowMetrics], risk_series: List[float]) -> Dict[str, Any]:
    risks = [w.risk for w in windows]
    if not risks:
        return {"verdict": "ALLOW"}

    warm = max(2, int(0.6 * len(risks)))
    mu, sigma = mean_std(risks[:warm])

    warn = mu + 2 * sigma
    block = mu + 3 * sigma

    last = risks[-1]

    verdict = "ALLOW"
    if last > block:
        verdict = "BLOCK"
    elif last > warn:
        verdict = "WARN"

    # Early drift detection (can only escalate to WARN)
    drift = cusum_alarm(risk_series)
    if drift and verdict == "ALLOW":
        verdict = "WARN"

    return {
        "verdict": verdict,
        "mu": mu,
        "sigma": sigma,
        "warn_threshold": warn,
        "block_threshold": block,
        "last_risk": last,
        "cusum_drift": drift
    }


# ---------------------------
# Main
# ---------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n", type=int, default=220)
    ap.add_argument("--window", type=int, default=20)
    args = ap.parse_args()

    events = generate(args.seed, args.n)
    windows, risk_series = compute_windows(events, args.window)
    nav = navigator(windows, risk_series)

    last = windows[-1] if windows else None

    report = {
        "kind": "HFS_NAVIGATOR_REPORT",
        "version": "0.2-wave",
        "verdict": nav["verdict"],
        "metrics_last_window": asdict(last) if last else {},
        "baseline": nav,
        "meta": {
            "events": len(events),
            "windows": len(windows),
            "wave_enabled": True
        }
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
