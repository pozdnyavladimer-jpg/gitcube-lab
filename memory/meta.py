# -*- coding: utf-8 -*-
"""
Meta-controller (Feedback Loop) for Hybrid Regulator
License: AGPL-3.0
Author: Володимир Поздняк

Idea:
- Read current report.json (HFS or GitCube)
- Look into memory.jsonl (atoms history)
- If recent atoms show high concentration of BLOCK/WARN in similar bands,
  reduce thresholds (become more cautious)

No ML. Pure control / stats.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _dna_prefix(dna: str) -> str:
    # Works for "DNA: T2 R1 ..." and also "C1 L0 ..."
    if not dna:
        return ""
    s = dna.replace("DNA:", "").strip()
    parts = [p for p in s.split() if p]
    return " ".join(parts[:3])  # tiny signature


def adjust_thresholds(report: Dict[str, Any], store_path: Path, lookback: int = 200) -> Dict[str, Any]:
    baseline = report.get("baseline", {}) or {}
    warn = float(baseline.get("warn_threshold", 0.0) or 0.0)
    block = float(baseline.get("block_threshold", 0.0) or 0.0)

    cur_verdict = str(report.get("verdict", "UNKNOWN"))
    cur_dna = str(report.get("dna", report.get("structural_dna", "")) or "")
    cur_prefix = _dna_prefix(cur_dna)

    cur_band = report.get("band", None)
    if cur_band is None:
        # some reports won't have band; that's OK
        cur_band = None
    else:
        try:
            cur_band = int(cur_band)
        except Exception:
            cur_band = None

    # Load last N atoms
    atoms: List[Dict[str, Any]] = []
    for a in _iter_jsonl(store_path):
        atoms.append(a)
        if len(atoms) >= lookback:
            atoms = atoms[-lookback:]

    # Score "danger" in similar context:
    # - strong match: same band (or band is missing)
    # - soft match: same dna prefix (if available)
    danger = 0.0
    support = 0.0

    for a in atoms:
        v = str(a.get("verdict", ""))
        band = a.get("band", None)
        dna = str(a.get("dna", "") or "")
        prefix = _dna_prefix(dna)

        band_match = (cur_band is None) or (band == cur_band)
        prefix_match = (not cur_prefix) or (prefix == cur_prefix)

        if not band_match and not prefix_match:
            continue

        w = 1.0
        if band_match:
            w += 0.5
        if prefix_match:
            w += 0.5

        support += w
        if v == "BLOCK":
            danger += 1.0 * w
        elif v == "WARN":
            danger += 0.35 * w

    # If no history, no adjustment
    if support <= 1e-9:
        return {
            "warn_threshold": warn,
            "block_threshold": block,
            "delta_warn": 0.0,
            "delta_block": 0.0,
            "danger_ratio": 0.0,
            "note": "no_history",
        }

    danger_ratio = danger / support  # 0..1-ish
    # Map danger_ratio -> shrink factor (max 20% shrink)
    shrink = min(0.20, max(0.0, danger_ratio * 0.20))

    new_warn = warn * (1.0 - shrink)
    new_block = block * (1.0 - shrink)

    return {
        "warn_threshold": new_warn,
        "block_threshold": new_block,
        "delta_warn": new_warn - warn,
        "delta_block": new_block - block,
        "danger_ratio": danger_ratio,
        "note": f"shrink={shrink:.3f}",
    }


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="Path to report.json")
    ap.add_argument("--store", required=True, help="Path to memory.jsonl")
    ap.add_argument("--out", default="", help="Optional: write patched report to file")
    ap.add_argument("--lookback", type=int, default=200)
    args = ap.parse_args()

    report_path = Path(args.report)
    store_path = Path(args.store)

    report = _load_json(report_path)
    adj = adjust_thresholds(report, store_path, lookback=args.lookback)

    # attach meta section (do NOT overwrite original baseline)
    report.setdefault("meta_control", {})
    report["meta_control"]["adjustment"] = adj

    print("=== META CONTROL ===")
    print(json.dumps(adj, ensure_ascii=False, indent=2))

    if args.out:
        out_path = Path(args.out)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[meta] wrote patched report -> {out_path}")


if __name__ == "__main__":
    main()
