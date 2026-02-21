# -*- coding: utf-8 -*-
"""
Meta-controller (Feedback Loop) — v0.2

Goal:
- Look at recent memory atoms for the same dna_key
- Compute a "reflex" (how often it collapses + how hot it was)
- Produce shrink factor for thresholds (warn/block)

No ML. Pure control.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .store import MemoryStore, Query


def band_hotness(band: int) -> float:
    """
    Map band 1..7 to hotness 1..0
    band=1 => 1.0 (hottest)
    band=7 => 0.0 (cold)
    """
    b = int(band)
    if b < 1:
        b = 1
    if b > 7:
        b = 7
    return (7 - b) / 6.0


@dataclass
class MetaDecision:
    shrink: float
    reflex: float
    block_rate: float
    hot_avg: float
    matches: int


def meta_shrink_factor(
    *,
    store_path: str,
    dna_key: str,
    kind: Optional[str] = None,
    lookback: int = 200,
) -> MetaDecision:
    """
    Returns shrink in [0.65..1.0]
    - shrink=1.0 => no memory effect
    - shrink=0.65 => maximum tightening (35% tighter)
    """
    if not dna_key:
        return MetaDecision(shrink=1.0, reflex=0.0, block_rate=0.0, hot_avg=0.0, matches=0)

    store = MemoryStore(store_path)
    atoms = store.query(
        Query(
            kind=kind,
            dna_key=dna_key,
            limit=max(1, int(lookback)),
        )
    )

    if not atoms:
        return MetaDecision(shrink=1.0, reflex=0.0, block_rate=0.0, hot_avg=0.0, matches=0)

    n = len(atoms)
    blocks = 0
    hot_sum = 0.0

    for a in atoms:
        v = str(a.get("verdict") or "").upper()
        if v == "BLOCK":
            blocks += 1
        hot_sum += band_hotness(int(a.get("band", 7) or 7))

    block_rate = blocks / max(1, n)
    hot_avg = hot_sum / max(1, n)

    # Reflex: mix "logic" (collapse frequency) + "pain" (how hot it was)
    reflex = (0.45 * block_rate) + (0.25 * hot_avg)

    # Limit tightening to max 35%
    max_shrink = 0.35
    shrink = 1.0 - min(max_shrink, max(0.0, reflex))

    # Safety clamp
    if shrink < 0.65:
        shrink = 0.65
    if shrink > 1.0:
        shrink = 1.0

    return MetaDecision(
        shrink=shrink,
        reflex=reflex,
        block_rate=block_rate,
        hot_avg=hot_avg,
        matches=n,
    )


def apply_meta_to_report(
    report: Dict[str, Any],
    *,
    store_path: str,
    kind: Optional[str] = None,
    lookback: int = 200,
) -> Dict[str, Any]:
    """
    Mutates thresholds in report.baseline by shrink factor derived from memory.

    Adds:
      report["meta_control"] = {shrink, reflex, ...}
      baseline["warn_threshold_meta"]
      baseline["block_threshold_meta"]
    """
    baseline = report.get("baseline") or {}
    dna_key = (report.get("dna_key") or "").strip()

    # If report doesn't have dna_key, fall back to parsing from dna
    if not dna_key:
        # try to read from atom.normalize_dna_key style tokens
        dna = str(report.get("dna") or "")
        # simple inline parse: take first 3 tokens like Xn
        s = dna.strip()
        if s.lower().startswith("dna:"):
            s = s.split(":", 1)[1].strip()
        toks = [t for t in s.replace(",", " ").split() if t and t[0].isalpha() and t[-1].isdigit()]
        dna_key = "|".join(toks[:3]) if toks else ""

    md = meta_shrink_factor(
        store_path=store_path,
        dna_key=dna_key,
        kind=kind,
        lookback=lookback,
    )

    warn = baseline.get("warn_threshold")
    block = baseline.get("block_threshold")

    if isinstance(warn, (int, float)) and isinstance(block, (int, float)):
        baseline["warn_threshold_meta"] = float(warn) * md.shrink
        baseline["block_threshold_meta"] = float(block) * md.shrink

    report["meta_control"] = {
        "dna_key": dna_key,
        "shrink": md.shrink,
        "reflex": md.reflex,
        "block_rate": md.block_rate,
        "hot_avg": md.hot_avg,
        "matches": md.matches,
        "lookback": int(lookback),
    }
    report["baseline"] = baseline
    report["dna_key"] = dna_key
    return report
