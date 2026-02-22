# -*- coding: utf-8 -*-
"""
Memory Atom (Topological Memory) — v0.3 (stable + flower optional)
- Deterministic atom_id (no timestamps / repo / ref included in hash)
- 42 phase states: 7 bands × 6 phase directions
- strength + last_seen for crystallization (merge/upsert in store)
- Optional "flower" invariant:
    report["flower_cycle"] = [{"risk":..,"specH":..}, ...] (6 points)
    -> flower.petal_area computed and stored in atom
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

from .flower import flower_from_cycle


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_dna_key(dna: str, key_len: int = 3) -> str:
    s = (dna or "").strip()
    if not s:
        return ""

    if s.lower().startswith("dna:"):
        s = s.split(":", 1)[1].strip()

    toks = []
    for t in s.replace(",", " ").split():
        if len(t) >= 2 and t[0].isalpha() and t[-1].isdigit():
            toks.append(t)

    toks = toks[: max(1, int(key_len))]
    return "|".join(toks)


def _band_from_verdict(verdict: str) -> int:
    v = (verdict or "").upper()
    if v == "BLOCK":
        return 1
    if v == "WARN":
        return 3
    return 6


def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


def _pick_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(report.get("metrics"), dict):
        return dict(report["metrics"])
    if isinstance(report.get("metrics_last_window"), dict):
        return dict(report["metrics_last_window"])
    return {}


def _pick_prev_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
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


# -------------------------------------------------------------------
# Phase logic
# -------------------------------------------------------------------

def infer_phase_dir(
    report: Dict[str, Any],
    *,
    cusum_gate: float = 0.05,
) -> Tuple[int, Dict[str, float]]:

    baseline = report.get("baseline") if isinstance(report.get("baseline"), dict) else {}
    metrics = _pick_metrics(report)
    prev = _pick_prev_metrics(report)

    risk = _get_metric(metrics, "risk", "last_risk", default=_num(report.get("risk"), 0.0))
    specH = _get_metric(metrics, "spectral_entropy", "specH", "entropy", default=0.0)
    cusum = _get_metric(metrics, "cusum", default=_num(baseline.get("cusum"), 0.0))

    if prev:
        prev_risk = _get_metric(prev, "risk", default=risk)
        prev_specH = _get_metric(prev, "spectral_entropy", "specH", default=specH)
        prev_cusum = _get_metric(prev, "cusum", default=cusum)
        d_risk = risk - prev_risk
        d_specH = specH - prev_specH
        d_cusum = cusum - prev_cusum
    else:
        mu = _num(baseline.get("mu"), 0.0)
        base_risk = _num(baseline.get("last_risk"), mu)
        d_risk = risk - base_risk
        d_specH = specH - _num(baseline.get("specH"), 0.5)
        d_cusum = cusum - _num(baseline.get("cusum"), 0.0)

    if abs(d_cusum) >= float(cusum_gate):
        phase_dir = 2 if d_cusum > 0 else 3
    else:
        if d_risk >= 0 and d_specH >= 0:
            phase_dir = 0
        elif d_risk >= 0:
            phase_dir = 1
        elif d_specH >= 0:
            phase_dir = 4
        else:
            phase_dir = 5

    return int(phase_dir), {
        "d_risk": float(d_risk),
        "d_specH": float(d_specH),
        "d_cusum": float(d_cusum),
    }


def phase_state_from(band: int, phase_dir: int) -> int:
    b = max(1, min(7, int(band)))
    d = max(0, min(5, int(phase_dir)))
    return (b - 1) * 6 + d + 1


# -------------------------------------------------------------------
# Memory Atom
# -------------------------------------------------------------------

@dataclass(frozen=True)
class MemoryAtom:
    kind: str
    version: str

    verdict: str
    dna: str
    dna_key: str

    band: int
    phase_dir: int
    phase_state: int

    baseline: Dict[str, Any]
    metrics: Dict[str, Any]

    # Optional flower invariant (not part of atom_id)
    flower: Dict[str, Any]

    strength: int
    first_seen: float
    last_seen: float

    context: Dict[str, Any]

    atom_id: str

    # ---------------------------------------------------------------

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

        bl = {
            "mu": baseline.get("mu"),
            "sigma": baseline.get("sigma"),
            "warn_threshold": baseline.get("warn_threshold"),
            "block_threshold": baseline.get("block_threshold"),
        }

        mt = {
            "risk": metrics.get("risk", metrics.get("last_risk")),
            "specH": metrics.get("specH", metrics.get("spectral_entropy")),
            "cusum": metrics.get("cusum", baseline.get("cusum", 0.0)),
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

        return hashlib.sha256(_canon(payload).encode("utf-8")).hexdigest()

    # ---------------------------------------------------------------

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

        verdict = str(report.get("verdict") or "ALLOW").upper()
        dna = str(report.get("dna") or "")
        dna_key = normalize_dna_key(dna, key_len)

        baseline = report.get("baseline") if isinstance(report.get("baseline"), dict) else {}
        metrics = _pick_metrics(report)

        # phase
        phase_dir, deltas = infer_phase_dir(report, cusum_gate=cusum_gate)
        metrics.setdefault("deltas", deltas)

        band = int(report.get("band") or _band_from_verdict(verdict))
        band = max(1, min(7, band))

        phase_state = phase_state_from(band, phase_dir)

        # flower (optional)
        flower: Dict[str, Any] = {}
        if isinstance(report.get("flower_cycle"), list):
            flower = flower_from_cycle(report["flower_cycle"], x_key="risk", y_key="specH", take=6)
        else:
            flower = {"petal_area": 0.0, "points": []}

        now = time.time()

        atom_id = cls.compute_atom_id(
            kind=kind,
            version=version,
            verdict=verdict,
            dna_key=dna_key,
            band=band,
            phase_state=phase_state,
            baseline=baseline,
            metrics=metrics,
        )

        context: Dict[str, Any] = {}
        if repo:
            context["repo"] = repo
        if ref:
            context["ref"] = ref
        if note:
            context["note"] = note

        return cls(
            kind=kind,
            version=version,
            verdict=verdict,
            dna=dna,
            dna_key=dna_key,
            band=band,
            phase_dir=phase_dir,
            phase_state=phase_state,
            baseline=baseline,
            metrics=metrics,
            flower=flower,
            strength=1,
            first_seen=now,
            last_seen=now,
            context=context,
            atom_id=atom_id,
        )

    # ---------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        # frozen dataclass -> __dict__ ok
        return self.__dict__

    # ---------------------------------------------------------------

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryAtom":
        now = time.time()

        atom_id = str(d.get("atom_id", "")).strip()
        if not atom_id:
            atom_id = cls.compute_atom_id(
                kind=d.get("kind", "NAVIGATOR_REPORT"),
                version=d.get("version", "0.3"),
                verdict=str(d.get("verdict", "ALLOW")).upper(),
                dna_key=d.get("dna_key", ""),
                band=d.get("band", 6),
                phase_state=d.get("phase_state", 1),
                baseline=d.get("baseline", {}),
                metrics=d.get("metrics", {}),
            )

        flower = d.get("flower") if isinstance(d.get("flower"), dict) else {"petal_area": 0.0, "points": []}

        return cls(
            kind=d.get("kind", "NAVIGATOR_REPORT"),
            version=d.get("version", "0.3"),
            verdict=str(d.get("verdict", "ALLOW")).upper(),
            dna=d.get("dna", ""),
            dna_key=d.get("dna_key", ""),
            band=int(d.get("band", 6)),
            phase_dir=int(d.get("phase_dir", 5)),
            phase_state=int(d.get("phase_state", 1)),
            baseline=d.get("baseline", {}) if isinstance(d.get("baseline"), dict) else {},
            metrics=d.get("metrics", {}) if isinstance(d.get("metrics"), dict) else {},
            flower=flower,
            strength=int(d.get("strength", 1)),
            first_seen=float(d.get("first_seen", now)),
            last_seen=float(d.get("last_seen", now)),
            context=d.get("context", {}) if isinstance(d.get("context"), dict) else {},
            atom_id=atom_id,
        )
