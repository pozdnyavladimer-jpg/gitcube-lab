# -*- coding: utf-8 -*-
"""
Meta-controller: Memory -> Threshold Shrink (Feedback Loop)

Uses MemoryStore.query() to estimate how dangerous a DNA pattern is historically.
If similar patterns often ended in BLOCK (and/or had hot energy bands),
we "shrink" thresholds (make gating stricter) for the current run.

No ML. Pure control.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .store import MemoryStore, Query


def _dna_prefix(dna: str, n: int = 2) -> str:
    toks = (dna or "").strip().split()
    return " ".join(toks[: max(1, int(n))])


def _band_hotness(band: int) -> float:
    """
    band: 1..7 (1 = hottest / highest risk)
    returns hotness in [0..1]
    """
    b = int(band or 0)
    if b <= 0:
        return 0.0
    b = max(1, min(7, b))
    return (7 - b) / 6.0


def meta_shrink_factor(
    *,
    store_path: str,
    dna: str,
    kind: Optional[str] = None,
    prefix_n: int = 2,
    limit: int = 200,
) -> float:
    """
    Returns shrink factor in [0.65..1.0]
    1.0 => no change, 0.8 => thresholds become 20% tighter
    """
    prefix = _dna_prefix(dna, prefix_n)
    if not prefix:
        return 1.0

    store = MemoryStore(store_path)
    matches = store.query(Query(kind=kind, dna_contains=prefix, limit=limit))
    if not matches:
        return 1.0

    total = len(matches)
    blocks = sum(1 for a in matches if a.get("verdict") == "BLOCK")
    block_rate = blocks / max(1, total)

    # band-weighted reflex: hot bands increase the reflex strength
    hot_avg = 0.0
    hot_cnt = 0
    for a in matches:
        if a.get("verdict") == "BLOCK":
            hot_avg += _band_hotness(int(a.get("band", 0) or 0))
            hot_cnt += 1
    hot_avg = hot_avg / max(1, hot_cnt) if hot_cnt else 0.0

    # Compose reflex strength (tunable, but stable & simple)
    reflex = (0.45 * block_rate) + (0.25 * hot_avg)  # in [0..0.70] realistically

    # Map reflex -> shrink, clamp to keep BLOCK gate rare but more cautious
    shrink = 1.0 - min(0.35, max(0.0, reflex))  # shrink in [0.65..1.0]
    return float(shrink)


def apply_shrink_to_baseline(baseline: Dict[str, Any], shrink: float) -> Dict[str, Any]:
    """
    Multiply thresholds by shrink. Keep mu/sigma unchanged.
    """
    out = dict(baseline or {})
    for k in ("warn_threshold", "block_threshold"):
        if k in out and out[k] is not None:
            try:
                out[k] = float(out[k]) * float(shrink)
            except Exception:
                pass
    out["meta_shrink"] = float(shrink)
    return out


def meta_adjust_report(
    report: Dict[str, Any],
    *,
    store_path: str,
    kind: Optional[str] = None,
    prefix_n: int = 2,
    limit: int = 200,
) -> Dict[str, Any]:
    """
    Returns a patched report dict with baseline thresholds shrunk (meta_shrink added).
    """
    dna = report.get("dna", "") or ""
    baseline = report.get("baseline", {}) or {}
    shrink = meta_shrink_factor(
        store_path=store_path, dna=dna, kind=kind, prefix_n=prefix_n, limit=limit
    )
    report = dict(report)
    report["baseline"] = apply_shrink_to_baseline(baseline, shrink)
    return report
