# -*- coding: utf-8 -*-
"""
kuramoto_heatmap.py

Run grid(beta, noise_sigma, seeds), compute stable_rate and optionally
record "crystals" into memory.jsonl via memory.record_crystal.

Designed to be safe on weak machines: resumable via CSV "key" column.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, Optional, Tuple, List

import numpy as np
import pandas as pd

from memory.record_crystal import record_crystal


def extract_RH(rep: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    if not isinstance(rep, dict) or not rep:
        return None, None
    if "R_last" in rep and "H_last" in rep:
        return float(rep["R_last"]), float(rep["H_last"])
    m = rep.get("metrics") if isinstance(rep.get("metrics"), dict) else {}
    if "R" in m and ("H" in m or "spectral_entropy" in m):
        H = m.get("H", m.get("spectral_entropy"))
        return float(m["R"]), float(H)
    mw = rep.get("metrics_last_window") if isinstance(rep.get("metrics_last_window"), dict) else {}
    if "R" in mw and ("H" in mw or "spectral_entropy" in mw):
        H = mw.get("H", mw.get("spectral_entropy"))
        return float(mw["R"]), float(H)
    return None, None


def is_crystal(R: Optional[float], H: Optional[float], R_TH: float, H_TH: float) -> bool:
    return (R is not None) and (H is not None) and (R >= R_TH) and (H <= H_TH)


def run_one(workdir: str, seed: int, noise_sigma: float, beta: float) -> Dict[str, Any]:
    cmd = [
        sys.executable,
        "kuramoto13.py",
        "--seed", str(int(seed)),
        "--beta", str(float(beta)),
        "--noise_sigma", str(float(noise_sigma)),
    ]
    p = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"kuramoto13.py crashed\nSTDERR:\n{p.stderr[-4000:]}\nSTDOUT:\n{p.stdout[-4000:]}")
    s = (p.stdout or "").strip()
    if not s:
        return {}
    # try parse as clean JSON first
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # fallback: last json object in stdout
    start = s.rfind("{")
    if start != -1:
        try:
            return json.loads(s[start:])
        except json.JSONDecodeError:
            return {}
    return {}


def load_done_keys(results_csv: str) -> set:
    if not os.path.exists(results_csv):
        return set()
    try:
        df = pd.read_csv(results_csv)
        if "key" not in df.columns:
            return set()
        return set(df["key"].astype(str).tolist())
    except Exception:
        return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=".", help="folder where kuramoto13.py lives")
    ap.add_argument("--results_csv", default="heatmap_results.csv")
    ap.add_argument("--memory_jsonl", default="memory/memory.jsonl")

    ap.add_argument("--R_TH", type=float, default=0.88)
    ap.add_argument("--H_TH", type=float, default=0.22)

    ap.add_argument("--noise_min", type=float, default=0.0)
    ap.add_argument("--noise_max", type=float, default=0.08)
    ap.add_argument("--noise_steps", type=int, default=9)

    ap.add_argument("--beta_min", type=float, default=0.10)
    ap.add_argument("--beta_max", type=float, default=0.60)
    ap.add_argument("--beta_steps", type=int, default=9)

    ap.add_argument("--seeds", default="1,2,3,4,5")
    ap.add_argument("--repo", default="gitcube-lab")
    args = ap.parse_args()

    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    noise_grid = np.linspace(args.noise_min, args.noise_max, args.noise_steps)
    beta_grid = np.linspace(args.beta_min, args.beta_max, args.beta_steps)

    done = load_done_keys(args.results_csv)
    total_points = len(noise_grid) * len(beta_grid)
    start_time = time.time()

    point_idx = 0
    for noise_sigma in noise_grid:
        for beta in beta_grid:
            point_idx += 1
            key = f"noise={float(noise_sigma):.5f}|beta={float(beta):.5f}"
            if key in done:
                continue

            R_list: List[float] = []
            H_list: List[float] = []
            crystal_hits = 0

            for seed in seeds:
                rep = run_one(args.workdir, seed, float(noise_sigma), float(beta))
                R, H = extract_RH(rep)
                if R is not None:
                    R_list.append(R)
                if H is not None:
                    H_list.append(H)

                if is_crystal(R, H, args.R_TH, args.H_TH):
                    crystal_hits += 1

                    raw = f"{key}|seed={seed}|R={R:.6f}|H={H:.6f}"
                    crystal_key = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

                    # write to memory.jsonl
                    record_crystal(
                        store_path=args.memory_jsonl,
                        kind="KURAMOTO_GRID",
                        verdict="ALLOW",
                        dna=f"DNA: {crystal_key}",
                        metrics={
                            "R": float(R),
                            "spectral_entropy": float(H),
                            "risk": float(beta),          # reuse beta as "pressure/risk axis"
                            "cusum": 0.0,
                        },
                        baseline={},
                        context={"repo": args.repo, "ref": raw, "note": "auto crystal"},
                        flower_cycle=[
                            {"risk": float(beta), "specH": float(H)},
                            {"risk": float(beta), "specH": float(H)},  # minimal cycle (ok)
                            {"risk": float(beta), "specH": float(H)},
                        ],
                    )

            stable_rate = crystal_hits / max(1, len(seeds))
            mean_R = float(np.mean(R_list)) if R_list else float("nan")
            mean_H = float(np.mean(H_list)) if H_list else float("nan")

            out = pd.DataFrame([{
                "key": key,
                "noise_sigma": float(noise_sigma),
                "beta": float(beta),
                "stable_rate": float(stable_rate),
                "mean_R": mean_R,
                "mean_H": mean_H,
                "seeds": int(len(seeds)),
            }])

            header = not os.path.exists(args.results_csv)
            out.to_csv(args.results_csv, mode="a", header=header, index=False)

            done.add(key)
            elapsed_min = (time.time() - start_time) / 60.0
            print(f"[{point_idx}/{total_points}] {key} stable={stable_rate:.2f} meanR={mean_R:.3f} meanH={mean_H:.3f} ({elapsed_min:.1f}m)")


if __name__ == "__main__":
    main()
