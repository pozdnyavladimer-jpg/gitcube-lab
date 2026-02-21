# -*- coding: utf-8 -*-
"""
Memory Atom (Topological Memory) — v0.3
- Deterministic atom_id (no timestamps / repo / ref included in hash)
- 42 phase states: 7 bands × 6 phase directions
- strength + last_seen for crystallization (merge/upsert in store)
- Works for both DNA alphabets:
  - Structural DNA: C L D S H E P M
  - HFS DNA:        T R P S C F W M
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


def _canon(obj: Any) -> str:
    """Canonical JSON for stable hashing."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_dna_key(dna: str, key_len: int = 3) -> str:
    """
    Normalize a DNA string into a compact deterministic key.

    Accepts:
      "DNA: T2 R1 P3 S1 C0 F0 W0 M1"
      "C1 L0 D2 S1 H0 E1 P1 M0"
    Returns (example):
      "T2|R1|P3" or "C1|L0|D2"
    """
    s = (dna or "").strip()
    if not s:
        return ""

    if s.lower().startswith("dna:"):
        s = s.split(":", 1)[1].strip()

    toks = []
    for t in s.replace(",", " ").split():
        t = t.strip()
        if not t:
            continue
        if len(t) >= 2 and t[0].isalpha() and t[-1].isdigit():
            toks.append(t)

    toks = toks[: max(1, int(key_len))]
    return "|".join(toks)


def _band_from_verdict(verdict: str) -> int:
    """Fallback band 1..7 (1 hottest)."""
    v = (verdict or "").upper()
    if v == "BLOCK":
        return 1
    if v == "WARN":
        return 3
    return 6


def _num(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _pick_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(report.get("metrics"), dict):
        return dict(report["metrics"])
    if isinstance(report.get("metrics_last_window"), dict):
        return dict(report["metrics_last_window"])
    return {}


def _pick_prev_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    # optional producer support
    if isinstance(report.get("metrics_prev_window"), dict):
        return dict(report["metrics_prev_window"])
    if isinstance(report.get("metrics_previous_window"), dict):
        return dict(report["metrics_previous_window"])
    return {}


def _get_metric(metrics: Dict[str, Any], *names: str, default: float = 0.0) -> float:
    for n in names:
        if n in metrics:
            return _num(metrics.get(n), default)
    return default


def infer_phase_dir(
    report: Dict[str, Any],
    *,
    cusum_gate: float = 0.05,
) -> Tuple[int, Dict[str, float]]:
    """
    Map gradients to 6 phase directions (0..5):

    Core (risk/specH):
      Dir 0:  Δrisk > 0 AND ΔspecH > 0  (Acute Chaos / Rupture)
      Dir 1:  Δrisk > 0 AND ΔspecH < 0  (Compression / Tunnel focus)
      Dir 4:  Δrisk < 0 AND ΔspecH > 0  (Exploration / Safe chaos)
      Dir 5:  Δrisk < 0 AND ΔspecH < 0  (Consolidation / Cooling)

    Shadow (cusum dominates if |Δcusum| >= gate):
      Dir 2:  Δcusum > 0 (Shadow accumulation / hidden debt)
      Dir 3:  Δcusum < 0 (Shadow release / cleansing)

    Returns: (phase_dir, deltas)
    """
    baseline = report.get("baseline") if isinstance(report.get("baseline"), dict) else {}
    metrics = _pick_metrics(report)
    prev = _pick_prev_metrics(report)

    # Current values
    risk = _get_metric(metrics, "risk", "last_risk", default=_num(report.get("risk"), 0.0))
    specH = _get_metric(metrics, "spectral_entropy", "specH", "entropy", default=0.0)
    cusum = _get_metric(metrics, "cusum", "cusum_score", default=_num(baseline.get("cusum"), 0.0))

    # Previous values (preferred)
    if prev:
        prev_risk = _get_metric(prev, "risk", "last_risk", default=risk)
        prev_specH = _get_metric(prev, "spectral_entropy", "specH", "entropy", default=specH)
        prev_cusum = _get_metric(prev, "cusum", "cusum_score", default=cusum)
        d_risk = risk - prev_risk
        d_specH = specH - prev_specH
        d_cusum = cusum - prev_cusum
    else:
        # Fallback: if no prev window exists, anchor to baseline / neutral
        mu = _num(baseline.get("mu"), 0.0)
        base_risk = _num(baseline.get("last_risk"), mu)
        d_risk = risk - base_risk

        # specH neutral anchor: 0.5 is a reasonable generic center if unknown
        d_specH = specH - _num(baseline.get("specH"), 0.5)

        # cusum is often drift-like; if missing, stays ~0
        d_cusum = cusum - _num(baseline.get("cusum"), 0.0)

    # Shadow override (dominant slow drift)
    if abs(d_cusum) >= float(cusum_gate):
        phase_dir = 2 if d_cusum > 0 else 3
    else:
        # Sign map for risk/specH
        if d_risk >= 0 and d_specH >= 0:
            phase_dir = 0
        elif d_risk >= 0 and d_specH < 0:
            phase_dir = 1
        elif d_risk < 0 and d_specH >= 0:
            phase_dir = 4
        else:
            phase_dir = 5

    deltas = {"d_risk": float(d_risk), "d_specH": float(d_specH), "d_cusum": float(d_cusum)}
    return int(phase_dir), deltas


def phase_state_from(band: int, phase_dir: int) -> int:
    """
    1..42 (human-friendly), stable mapping:
      (band-1)*6 + phase_dir + 1
    """
    b = int(band)
    d = int(phase_dir)
    b = 1 if b < 1 else (7 if b > 7 else b)
    d = 0 if d < 0 else (5 if d > 5 else d)
    return (b - 1) * 6 + d + 1


@dataclass(frozen=True)
class MemoryAtom:
    kind: str
    version: str

    verdict: str
    dna: str
    dna_key: str

    band: int  # 1..7

    phase_dir: int   # 0..5
    phase_state: int # 1..42

    baseline: Dict[str, Any]
    metrics: Dict[str, Any]

    # crystallization fields (NOT part of atom_id)
    strength: int
    first_seen: float
    last_seen: float

    # Optional context (NOT hashed)
    context: Dict[str, Any]

    atom_id: str

    @staticmethod
    def compute_atom_id(
        *,
        kind: str,
        version: str,
        verdict: str,
        dna_key: str,
        band: int,
        phase_state: int,
        baseline: Dict[str, Any],
        metrics: Dict[str, Any],
    ) -> str:
        # Keep stable baseline subset
        bl = {
            "mu": baseline.get("mu"),
            "sigma": baseline.get("sigma"),
            "warn_threshold": baseline.get("warn_threshold"),
            "block_threshold": baseline.get("block_threshold"),
        }
        # Keep stable metrics subset
        mt = {
            "risk": metrics.get("risk", metrics.get("last_risk")),
            "specH": metrics.get("specH", metrics.get("spectral_entropy")),
            "cusum": metrics.get("cusum"),
        }

        payload = {
            "kind": kind,
            "version": version,
            "verdict": (verdict or "").upper(),
            "dna_key": dna_key,
            "band": int(band),
            "phase_state": int(phase_state),
            "baseline": bl,
            "metrics": mt,
        }
        h = hashlib.sha256(_canon(payload).encode("utf-8")).hexdigest()
        return h

    @classmethod
    def from_report(
        cls,
        report: Dict[str, Any],
        *,
        key_len: int = 3,
        repo: Optional[str] = None,
        ref: Optional[str] = None,
        note: Optional[str] = None,
        cusum_gate: float = 0.05,
    ) -> "MemoryAtom":
        kind = str(report.get("kind") or report.get("type") or "NAVIGATOR_REPORT")
        version = str(report.get("version") or "0.3")

        verdict = str(report.get("verdict") or report.get("action") or "ALLOW").upper()
        dna = str(report.get("dna") or "")
        dna_key = normalize_dna_key(dna, key_len=key_len)

        baseline = report.get("baseline") if isinstance(report.get("baseline"), dict) else {}
        metrics = _pick_metrics(report)

        # ensure unified fields in metrics
        if "risk" not in metrics:
            if isinstance(baseline, dict) and ("last_risk" in baseline):
                metrics["risk"] = baseline.get("last_risk")
            else:
                metrics["risk"] = report.get("risk")

        if "specH" not in metrics and "spectral_entropy" in metrics:
            metrics["specH"] = metrics.get("spectral_entropy")

        phase_dir, deltas = infer_phase_dir(report, cusum_gate=cusum_gate)
        metrics.setdefault("deltas", deltas)

        band = report.get("band")
        if band is None:
            band = _band_from_verdict(verdict)
        band = int(band)
        if band < 1:
            band = 1
        if band > 7:
            band = 7

        ps = phase_state_from(band, phase_dir)

        context: Dict[str, Any] = {}
        if repo:
            context["repo"] = repo
        if ref:
            context["ref"] = ref
        if note:
            context["note"] = note

        now = time.time()

        atom_id = cls.compute_atom_id(
            kind=kind,
            version=version,
            verdict=verdict,
            dna_key=dna_key,
            band=band,
            phase_state=ps,
            baseline=baseline,
            metrics=metrics,
        )

        return cls(
            kind=kind,
            version=version,
            verdict=verdict,
            dna=dna,
            dna_key=dna_key,
            band=band,
            phase_dir=int(phase_dir),
            phase_state=int(ps),
            baseline=baseline,
            metrics=metrics,
            strength=1,
            first_seen=now,
            last_seen=now,
            context=context,
            atom_id=atom_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "version": self.version,
            "atom_id": self.atom_id,
            "verdict": self.verdict,
            "dna": self.dna,
            "dna_key": self.dna_key,
            "band": self.band,
            "phase_dir": self.phase_dir,
            "phase_state": self.phase_state,
            "baseline": self.baseline,
            "metrics": self.metrics,
            "strength": self.strength,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryAtom":
        # tolerate older entries
        now = time.time()
        return cls(
            kind=str(d.get("kind", "NAVIGATOR_REPORT")),
            version=str(d.get("version", "0.3")),
            verdict=str(d.get("verdict", "ALLOW")),
            dna=str(d.get("dna", "")),
            dna_key=str(d.get("dna_key", "")),
            band=int(d.get("band", 6)),
            phase_dir=int(d.get("phase_dir", 5)),
            phase_state=int(d.get("phase_state", phase_state_from(int(d.get("band", 6)), int(d.get("phase_dir", 5))))),
            baseline=d.get("baseline") if isinstance(d.get("baseline"), dict) else {},
            metrics=d.get("metrics") if isinstance(d.get("metrics"), dict) else {},
            strength=int(d.get("strength", 1)),
            first_seen=float(d.get("first_seen", now)),
            last_seen=float(d.get("last_seen", now)),
            context=d.get("context") if isinstance(d.get("context"), dict) else {},
            atom_id=str(d.get("atom_id", "")),
        )
