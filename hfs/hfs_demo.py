# -*- coding: utf-8 -*-
"""
HFS Demo (Human Function Stream) — v0.1
License: AGPL-3.0
Author: Володимир Поздняк

This script generates a synthetic HFS session (chat/ide style events),
computes adaptive baseline, produces:
- Structural DNA (T R P S C F W M)
- Verdict: ALLOW / WARN / BLOCK
- JSON report for AI/CI

Usage:
  python hfs/hfs_demo.py --seed 42 --n 220
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
# Helpers
# ---------------------------

def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def mean_std(xs: List[float]) -> Tuple[float, float]:
    if not xs:
        return 0.0, 0.0
    m = sum(xs) / len(xs)
    v = sum((x - m) ** 2 for x in xs) / max(1, (len(xs) - 1))
    return m, math.sqrt(v)

def zscore(x: float, mu: float, sigma: float) -> float:
    if sigma <= 1e-9:
        return 0.0
    return (x - mu) / sigma

def has_structure(text: str) -> float:
    """
    Cheap proxy for 'structured thinking':
    - presence of numbered steps, bullets, short lines
    Returns 0..1
    """
    if not text:
        return 0.0
    score = 0.0
    # bullets / steps
    if "\n-" in text or "\n*" in text:
        score += 0.35
    if any(f"{i}." in text for i in range(1, 6)):
        score += 0.35
    # short lines (more structure)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines:
        avg_len = sum(len(ln) for ln in lines) / len(lines)
        if avg_len <= 60:
            score += 0.30
    return clamp(score, 0.0, 1.0)

def contradiction_proxy(prev: str, cur: str) -> float:
    """
    Very simple contradiction proxy:
    if user says "I want X" then "No, not X" or switches polarity.
    Returns 0 or 1.
    """
    p = (prev or "").lower()
    c = (cur or "").lower()
    if not p or not c:
        return 0.0
    # polarity flip markers
    neg = ["no", "not", "don't", "do not", "нік", "не "]
    if "i want" in p and any(n in c for n in neg) and ("i want" in c or "i need" in c):
        return 1.0
    if "хочу" in p and "не" in c and ("хочу" in c or "треба" in c):
        return 1.0
    return 0.0


# ---------------------------
# Event model
# ---------------------------

@dataclass
class HFSEvent:
    t: float
    channel: str
    event: str
    payload: Dict[str, Any]
    features: Dict[str, Any]


# ---------------------------
# Synthetic generator
# ---------------------------

TOPICS = [
    "ship", "prototype", "refactor", "investor", "docs",
    "demo", "ci", "ai_agent", "vr", "hfs"
]

def gen_message(rng: random.Random, topic: str, structured: bool) -> str:
    base = {
        "ship": "We should ship the MVP and get feedback.",
        "prototype": "Let's build a minimal prototype and measure risk.",
        "refactor": "We need to refactor to reduce dependency pressure.",
        "investor": "We need a clean explanation for decision-makers.",
        "docs": "Write a one-screen README with steps.",
        "demo": "Run a demo and export JSON for AI.",
        "ci": "Add a GitHub Action gate.",
        "ai_agent": "An agent should read the report and decide.",
        "vr": "Connect the idea to VR later, but keep it software now.",
        "hfs": "We need a stream format to capture human interaction."
    }.get(topic, "Let's continue.")

    if structured:
        return (
            f"{base}\n"
            "1. Define input\n"
            "2. Compute metrics\n"
            "3. Output verdict\n"
        )
    # unstructured / noisy
    noise = ["umm", "maybe", "idk", "random", "all at once", "???"]
    return f"{base} {rng.choice(noise)} {rng.choice(noise)}"


def generate_hfs(seed: int, n: int) -> List[HFSEvent]:
    rng = random.Random(seed)
    events: List[HFSEvent] = []

    t0 = time.time()
    topic = rng.choice(TOPICS)
    last_text = ""

    # session state knobs
    pressure = 0.2
    rewrite_rate = 0.1

    for i in range(n):
        # stochastic changes
        if rng.random() < 0.18:  # drift to new topic
            topic = rng.choice(TOPICS)

        # sometimes pressure spikes
        if rng.random() < 0.10:
            pressure = clamp(pressure + rng.uniform(0.25, 0.50), 0.0, 1.0)
        else:
            pressure = clamp(pressure - rng.uniform(0.01, 0.03), 0.0, 1.0)

        # rewrite correlates with pressure
        rewrite_rate = clamp(0.05 + 0.70 * pressure + rng.uniform(-0.05, 0.05), 0.0, 1.0)

        structured = (pressure < 0.35) and (rng.random() < 0.55)

        text = gen_message(rng, topic, structured)
        contr = contradiction_proxy(last_text, text)
        last_text = text

        pause_s = clamp(rng.gauss(0.6 + 1.2 * pressure, 0.25), 0.05, 4.0)
        edits = int(round(rewrite_rate * rng.uniform(0, 6)))

        ev = HFSEvent(
            t=t0 + i * 0.9,
            channel="chat",
            event="message",
            payload={"topic": topic, "text": text},
            features={
                "len": len(text),
                "pause_s": round(pause_s, 3),
                "edits": edits,
                "structure": round(has_structure(text), 3),
                "contradiction": contr,
                "pressure_latent": round(pressure, 3),  # for demo only
            },
        )
        events.append(ev)

        # occasional edit events
        if edits >= 3 and rng.random() < 0.35:
            events.append(HFSEvent(
                t=ev.t + 0.2,
                channel="ide",
                event="edit",
                payload={"topic": topic, "note": "edit burst"},
                features={"edits": edits, "pause_s": 0.0}
            ))

    return events


# ---------------------------
# Metrics + DNA
# ---------------------------

@dataclass
class HFSWindowMetrics:
    T_topic_drift: float
    R_rewrite: float
    P_pressure_spike: float
    S_stability: float
    C_contradiction: float
    F_focus: float
    risk: float


def compute_windows(events: List[HFSEvent], window_size: int = 20) -> List[HFSWindowMetrics]:
    """
    Compute metrics over sliding windows (non-overlapping for simplicity).
    """
    windows: List[HFSWindowMetrics] = []
    prev_vol = None

    for w0 in range(0, len(events), window_size):
        chunk = events[w0:w0 + window_size]
        if not chunk:
            break

        # topic drift
        topics = []
        rewrites = 0
        structures = []
        contradictions = 0
        pauses = []
        lengths = []

        for ev in chunk:
            if ev.event == "message":
                topics.append(ev.payload.get("topic", ""))
                rewrites += int(ev.features.get("edits", 0))
                structures.append(float(ev.features.get("structure", 0.0)))
                contradictions += int(ev.features.get("contradiction", 0))
                pauses.append(float(ev.features.get("pause_s", 0.0)))
                lengths.append(float(ev.features.get("len", 0.0)))
            elif ev.event == "edit":
                rewrites += int(ev.features.get("edits", 0))

        topic_switches = 0
        for a, b in zip(topics, topics[1:]):
            if a and b and a != b:
                topic_switches += 1

        T = topic_switches / max(1, len(topics) - 1)  # 0..1 approx

        # rewrite rate per message (0..1 scaled)
        R = clamp(rewrites / max(1, len(topics) * 6), 0.0, 1.0)

        # volatility proxy: combines rewrite, topic drift, pause jitter
        pause_m = sum(pauses) / max(1, len(pauses))
        pause_j = math.sqrt(sum((p - pause_m) ** 2 for p in pauses) / max(1, len(pauses))) if pauses else 0.0
        vol = 0.45 * T + 0.35 * R + 0.20 * clamp(pause_j / 1.2, 0.0, 1.0)

        # pressure spike: acceleration of volatility
        if prev_vol is None:
            P = 0.0
        else:
            P = clamp(vol - prev_vol, -1.0, 1.0)
        prev_vol = vol

        # stability: structured writing + low drift + reasonable pauses
        struct_mean = sum(structures) / max(1, len(structures)) if structures else 0.0
        S = clamp(0.60 * struct_mean + 0.25 * (1.0 - T) + 0.15 * clamp(1.2 - pause_m, 0.0, 1.0), 0.0, 1.0)

        # contradiction rate
        C = clamp(contradictions / max(1, len(topics)), 0.0, 1.0)

        # focus: sustained low drift + high structure
        F = clamp((1.0 - T) * struct_mean, 0.0, 1.0)

        # combined risk (Shadow/Pressure-like): higher T, R, P(+), C increases risk; S & F reduce it
        P_pos = max(0.0, P)
        risk = clamp(
            0.30 * T + 0.25 * R + 0.20 * P_pos + 0.15 * C + 0.10 * (1.0 - S),
            0.0, 1.0
        )

        windows.append(HFSWindowMetrics(T, R, P_pos, S, C, F, risk))

    return windows


def level(x: float, cuts: Tuple[float, float, float] = (0.15, 0.35, 0.60)) -> int:
    """
    Discretize a 0..1 metric to 0..3.
    """
    if x <= cuts[0]:
        return 0
    if x <= cuts[1]:
        return 1
    if x <= cuts[2]:
        return 2
    return 3


def make_dna(last: HFSWindowMetrics, verdict: str) -> str:
    T = level(last.T_topic_drift)
    R = level(last.R_rewrite)
    P = level(last.P_pressure_spike)
    S = level(last.S_stability)
    C = level(last.C_contradiction)
    F = level(last.F_focus)
    W = 1 if verdict == "WARN" else 0
    M = 1 if verdict == "BLOCK" else 0
    return f"DNA: T{T} R{R} P{P} S{S} C{C} F{F} W{W} M{M}"


def navigator_verdict(risks: List[float]) -> Dict[str, Any]:
    """
    Adaptive baseline from earlier windows:
    - baseline computed from first 60% of windows (warmup)
    - verdict from last risk against thresholds
    """
    if not risks:
        return {"verdict": "ALLOW", "mu": 0.0, "sigma": 0.0, "warn": 0.0, "block": 0.0}

    n = len(risks)
    warm = max(2, int(0.60 * n))
    base = risks[:warm]
    mu, sigma = mean_std(base)

    warn = mu + 2.0 * sigma
    block = mu + 3.0 * sigma

    last = risks[-1]
    if last > block:
        v = "BLOCK"
    elif last > warn:
        v = "WARN"
    else:
        v = "ALLOW"

    return {"verdict": v, "mu": mu, "sigma": sigma, "warn": warn, "block": block, "last_risk": last}


def recommendation_for(verdict: str) -> str:
    if verdict == "BLOCK":
        return "Stop. Reduce drift: pick 1 goal, write 3 steps, then continue."
    if verdict == "WARN":
        return "Slow down. Keep 1 topic for the next 10 minutes. Convert to steps."
    return "Proceed. Next: turn the plan into 3 concrete tasks."


# ---------------------------
# Main
# ---------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n", type=int, default=220)
    ap.add_argument("--window", type=int, default=20)
    ap.add_argument("--dump-events", action="store_true")
    args = ap.parse_args()

    events = generate_hfs(args.seed, args.n)
    windows = compute_windows(events, window_size=args.window)
    risks = [w.risk for w in windows]

    base = navigator_verdict(risks)
    verdict = base["verdict"]
    last = windows[-1] if windows else HFSWindowMetrics(0, 0, 0, 0, 0, 0, 0)
    dna = make_dna(last, verdict)

    report = {
        "kind": "HFS_NAVIGATOR_REPORT",
        "version": "0.1",
        "verdict": verdict,
        "dna": dna,
        "metrics_last_window": asdict(last),
        "baseline": {
            "mu": base["mu"],
            "sigma": base["sigma"],
            "warn_threshold": base["warn"],
            "block_threshold": base["block"],
            "last_risk": base["last_risk"],
        },
        "recommendation": recommendation_for(verdict),
        "meta": {
            "seed": args.seed,
            "events": len(events),
            "windows": len(windows),
            "window_size": args.window,
        },
    }

    # Optionally dump event stream (JSONL)
    if args.dump_events:
        for ev in events:
            print(json.dumps(asdict(ev), ensure_ascii=False))

    # Always print the final JSON report (what AI/CI consumes)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
