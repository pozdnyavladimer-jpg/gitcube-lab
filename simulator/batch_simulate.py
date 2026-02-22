# -*- coding: utf-8 -*-
"""
Batch simulator for Memory evolution (Colab-friendly)

- Generates many HFS reports by running hfs/hfs_demo.py
- Injects flower_cycle (last 6 windows of (risk, specH)) into report.json
- Records atoms to memory.jsonl using memory.cli record
- Prints zone distribution + top crystals

Assumes:
- hfs/hfs_demo.py prints JSON report to stdout
- memory/cli.py exists and supports "record" and "stats" and "query"
"""

from __future__ import annotations

import json
import os
import subprocess
from collections import Counter, defaultdict
from typing import Dict, Any, List, Tuple

STORE = "memory/memory.jsonl"


def zone(phase_state: int) -> str:
    if 1 <= phase_state <= 14:
        return "Z1(1-14)"
    if 15 <= phase_state <= 24:
        return "Z2(15-24)"
    if 25 <= phase_state <= 34:
        return "Z3(25-34)"
    if 35 <= phase_state <= 42:
        return "Z4(35-42)"
    return "OUT"


def run_hfs(seed: int, n: int = 220, window: int = 20) -> Dict[str, Any]:
    """
    Runs hfs_demo and returns parsed JSON report.
    """
    cmd = ["python", "hfs/hfs_demo.py", "--seed", str(seed), "--n", str(n), "--window", str(window)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"hfs_demo failed seed={seed}:\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return json.loads(p.stdout)


def inject_flower_cycle(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    We need 6 points (risk, specH) to compute petal area.
    HFS demo currently gives only metrics_last_window by default.
    So we create a synthetic 6-step cycle around last metrics using deltas if present.
    If you later upgrade HFS demo to export real window history, replace this with real points.
    """
    metrics = report.get("metrics_last_window") if isinstance(report.get("metrics_last_window"), dict) else {}
    deltas = metrics.get("deltas") if isinstance(metrics.get("deltas"), dict) else {}
    baseline = report.get("baseline") if isinstance(report.get("baseline"), dict) else {}

    risk = float(metrics.get("risk", baseline.get("last_risk", 0.0)) or 0.0)
    specH = float(metrics.get("spectral_entropy", metrics.get("specH", 0.0)) or 0.0)

    d_risk = float(deltas.get("d_risk", 0.02) or 0.02)
    d_spec = float(deltas.get("d_specH", 0.02) or 0.02)

    # Build a simple 3 forward + 3 back cycle (not zero area if d_risk and d_spec differ)
    pts: List[Dict[str, float]] = []
    x, y = risk, specH
    # forward 3
    for _ in range(3):
        x = max(0.0, min(1.0, x + abs(d_risk)))
        y = max(0.0, min(1.0, y + abs(d_spec)))
        pts.append({"risk": x, "specH": y})
    # back 3 (different slope)
    for _ in range(3):
        x = max(0.0, min(1.0, x - abs(d_risk) * 0.7))
        y = max(0.0, min(1.0, y - abs(d_spec) * 1.2))
        pts.append({"risk": x, "specH": y})

    report["flower_cycle"] = pts[:6]
    return report


def record_report(report: Dict[str, Any], tmp_path: str = "report.json") -> None:
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    cmd = ["python", "-m", "memory.cli", "record", "--report", tmp_path, "--store", STORE]
    p = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH="."))
    if p.returncode != 0:
        raise RuntimeError(f"record failed:\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")


def main():
    # reset store
    os.makedirs(os.path.dirname(STORE) or ".", exist_ok=True)
    if os.path.exists(STORE):
        os.remove(STORE)

    N = 120  # кількість репортів (постав 200 якщо хочеш)
    for seed in range(N):
        rep = run_hfs(seed=seed, n=220, window=20)
        rep = inject_flower_cycle(rep)
        record_report(rep)

    # analyze store
    rows: List[Dict[str, Any]] = []
    with open(STORE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    zone_counts = Counter(zone(int(r.get("phase_state", 0) or 0)) for r in rows)

    print("\n=== ZONE DISTRIBUTION ===")
    for k in ["Z1(1-14)", "Z2(15-24)", "Z3(25-34)", "Z4(35-42)", "OUT"]:
        if k in zone_counts:
            print(f"{k}: {zone_counts[k]}")

    # top crystals by strength
    rows.sort(key=lambda r: (int(r.get("strength", 1) or 1), float(r.get("last_seen", 0.0) or 0.0)), reverse=True)

    print("\n=== TOP 10 ATOMS (by strength) ===")
    for r in rows[:10]:
        fl = r.get("flower", {}) if isinstance(r.get("flower"), dict) else {}
        print({
            "strength": r.get("strength"),
            "phase_state": r.get("phase_state"),
            "band": r.get("band"),
            "phase_dir": r.get("phase_dir"),
            "petal_area": fl.get("petal_area", 0.0),
            "dna_key": r.get("dna_key", ""),
            "verdict": r.get("verdict", ""),
        })


if __name__ == "__main__":
    main()
