# -*- coding: utf-8 -*-
"""
Meta-controller (Feedback Loop) for GitCube Memory.

Goal:
- Look into recent MemoryAtoms (via MemoryStore.query)
- If similar DNA patterns historically lead to BLOCK, shrink thresholds (be more conservative)
- Keep BLOCK gate logic "shape" intact, only shift thresholds via multiplicative factor.

Usage:
  python -m memory.meta --report report.json --store memory/memory.jsonl
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional

from .store import MemoryStore, Query


def _dna_prefix(dna: str, n_pairs: int = 2) -> str:
    # "C1 L0 D2 ..." -> "C1 L0"
    toks = (dna or "").strip().split()
    return " ".join(toks[: max(1, int(n_pairs))])


def meta_shrink_factor(
    report: Dict[str, Any],
    store_path: str,
    *,
    n_pairs: int = 2,
    lookback: int = 200,
    floor: float = 0.70,
    strength: float = 0.35,
) -> float:
    """
    Returns factor in [floor..1.0]. Multiply thresholds by this factor.
    More past BLOCK concentration for similar DNA => smaller factor.
    """
    dna = report.get("dna", "") or ""
    key = _dna_prefix(dna, n_pairs=n_pairs)
    if not key:
        return 1.0

    store = MemoryStore(store_path)
    atoms = store.query(Query(dna_contains=key, limit=lookback))

    if not atoms:
        return 1.0

    blocks = sum(1 for a in atoms if a.get("verdict") == "BLOCK")
    rate = blocks / max(1, len(atoms))  # 0..1

    # shrink grows with block-rate, but bounded by floor
    shrink = 1.0 - (strength * rate)
    if shrink < float(floor):
        shrink = float(floor)
    if shrink > 1.0:
        shrink = 1.0
    return shrink


def apply_meta(report: Dict[str, Any], store_path: str, **kw: Any) -> Dict[str, Any]:
    baseline = dict(report.get("baseline") or {})
    wt = baseline.get("warn_threshold")
    bt = baseline.get("block_threshold")

    # If thresholds are absent, do nothing (fail-safe)
    if wt is None or bt is None:
        report["meta"] = {"shrink": 1.0, "reason": "no_thresholds"}
        return report

    shrink = meta_shrink_factor(report, store_path, **kw)

    baseline["warn_threshold"] = float(wt) * shrink
    baseline["block_threshold"] = float(bt) * shrink

    report["baseline"] = baseline
    report["meta"] = {
        "shrink": shrink,
        "dna_prefix": _dna_prefix(report.get("dna", "") or "", n_pairs=int(kw.get("n_pairs", 2))),
        "store": store_path,
    }
    return report


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True, help="Path to HFS/GitCube report.json")
    p.add_argument("--store", default="memory/memory.jsonl", help="Path to memory store JSONL")
    p.add_argument("--pairs", type=int, default=2, help="How many DNA pairs to match (prefix length)")
    p.add_argument("--lookback", type=int, default=200, help="How many recent matching atoms to consider")
    p.add_argument("--floor", type=float, default=0.70, help="Minimum shrink factor")
    p.add_argument("--strength", type=float, default=0.35, help="Shrink strength vs BLOCK rate")
    args = p.parse_args(argv)

    with open(args.report, "r", encoding="utf-8") as f:
        report = json.load(f)

    out = apply_meta(
        report,
        args.store,
        n_pairs=args.pairs,
        lookback=args.lookback,
        floor=args.floor,
        strength=args.strength,
    )

    # Print patched report (so you can pipe into validator / CI)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
