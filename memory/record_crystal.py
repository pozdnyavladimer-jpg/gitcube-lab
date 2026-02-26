# -*- coding: utf-8 -*-
"""
record_crystal.py

Bridge: simulation output -> MemoryAtom -> MemoryStore (JSONL).

Usage (python):
  from memory.record_crystal import record_crystal

  record_crystal(
      store_path="memory/memory.jsonl",
      kind="KURAMOTO_GRID",
      verdict="ALLOW",
      dna="DNA: O6-9 K13 ...",
      metrics={"R":0.91,"spectral_entropy":0.18,"risk":0.42,"cusum":0.0},
      baseline={"mu":0.32,"sigma":0.05,"warn_threshold":0.43,"block_threshold":0.48},
      context={"repo":"gitcube-lab","ref":"grid beta=0.2 noise=0.03 seed=3"},
      flower_cycle=[{"risk":0.4,"specH":0.2},{"risk":0.5,"specH":0.18},{"risk":0.42,"specH":0.21}],
  )
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .atom import MemoryAtom
from .store import MemoryStore


def build_report(
    *,
    kind: str,
    version: str = "0.4",
    verdict: str = "ALLOW",
    dna: str = "",
    band: Optional[int] = None,
    baseline: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    prev_metrics: Optional[Dict[str, Any]] = None,
    flower_cycle: Optional[List[Dict[str, Any]]] = None,
    flower_points: Optional[List[List[float]]] = None,
) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "kind": kind,
        "version": version,
        "verdict": (verdict or "ALLOW").upper(),
        "dna": dna or "",
        "baseline": baseline or {},
        "metrics": metrics or {},
    }

    if band is not None:
        report["band"] = int(band)

    if prev_metrics is not None:
        report["metrics_prev_window"] = dict(prev_metrics)

    # flower: either cycle points (risk/specH) or explicit points
    if flower_cycle:
        report["flower_cycle"] = list(flower_cycle)
    elif flower_points:
        report["flower"] = {"points": flower_points}

    return report


def record_crystal(
    *,
    store_path: str = "memory/memory.jsonl",
    kind: str,
    verdict: str = "ALLOW",
    dna: str = "",
    band: Optional[int] = None,
    baseline: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    prev_metrics: Optional[Dict[str, Any]] = None,
    flower_cycle: Optional[List[Dict[str, Any]]] = None,
    flower_points: Optional[List[List[float]]] = None,
    context: Optional[Dict[str, Any]] = None,
    key_len: int = 3,
    cusum_gate: float = 0.05,
) -> MemoryAtom:
    report = build_report(
        kind=kind,
        verdict=verdict,
        dna=dna,
        band=band,
        baseline=baseline,
        metrics=metrics,
        prev_metrics=prev_metrics,
        flower_cycle=flower_cycle,
        flower_points=flower_points,
    )

    ctx = context or {}
    atom = MemoryAtom.from_report(
        report,
        key_len=key_len,
        repo=ctx.get("repo"),
        ref=ctx.get("ref"),
        note=ctx.get("note"),
        cusum_gate=cusum_gate,
    )
    return MemoryStore(store_path).upsert(atom)
