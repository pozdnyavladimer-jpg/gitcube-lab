# -*- coding: utf-8 -*-
"""
Memory Atom (Topological Memory) — v0.4 (flower-aware)

Adds:
- flower_cycle -> petal_area (Shoelace)
- crystal_key = kind + ":" + dna_key  (core key for crystallization)
- Backward-compatible loading from older JSONL (no crystal_key/flower)

Keeps:
- Deterministic atom_id (no timestamps / repo / ref included in hash)
- 42 phase states: 7 bands × 6 phase directions
- strength + first_seen/last_seen
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


def _q(x: Any, ndigits: int = 6) -> float:
    """Quantize floats to reduce atom_id explosion (still deterministic)."""
    try:
        return round(float(x), ndigits)
    except Exception:
        return 0.0


def normalize_dna_key(dna: str, key_len: int = 3) -> str:
    s = (dna or "").strip()
    if not s:
        return ""

    if s.lower().startswith("dna:"):
        s = s.split(":", 1)[1].strip()

    toks: List[str] = []
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
# Flower math (Shoelace)
# -------------------------------------------------------------------

def polygon_area(points: List[Tuple[float, float]]) -> float:
    """
    Shoelace formula. points: list[(x,y)] with at least 3 points.
    Returns absolute area.
    """
    if not points or len(points) < 3:
        return 0.0
    s = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def extract_flower(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accepts either:
      - report["flower_cycle"] = [{"risk":..,"specH":..}, ...]
      - or report["flower"]["points"] = [[x,y],...]
    Produces:
      {"petal_area": float, "points": [[x,y],...]}
    """
    points: List[Tuple[float, float]] = []

    cycle = report.get("flower_cycle")
    if isinstance(cycle, list) and cycle:
        for p in cycle:
            if isinstance(p, dict):
                x = _num(p.get("risk"), 0.0)
                y = _num(p.get("specH"), 0.0)
                points.append((x, y))

    if not points:
        flower = report.get("flower")
        if isinstance(flower, dict):
            pts = flower.get("points")
            if isinstance(pts, list) and pts:
                for xy in pts:
                    if isinstance(xy, (list, tuple)) and len(xy) >= 2:
                        points.append((_num(xy[0], 0.0), _num(xy[1], 0.0)))

    area = polygon_area(points) if len(points) >= 3 else 0.0

    return {
        "petal_area": float(area),
        "points": [[float(x), float(y)] for (x, y) in points],
    }


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
        prev_specH = _get_metric(prev, "spectral_entropy", default=specH)
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

    # flower invariant (petal area)
    flower: Dict[str, Any]

    # crystallization key (core)
    crystal_key: str

    strength: int
    first_seen: float
    last_seen: float

    context: Dict[str, Any]

    atom_id: str

    # ---------------------------------------------------------------

    @staticmethod
    def compute_crystal_key(kind: str, dna_key: str) -> str:
        k = str(kind or "").strip() or "NAVIGATOR_REPORT"
        d = str(dna_key or "").strip()
        return f"{k}:{d}" if d else k

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
        flower: Dict[str, Any],
    ) -> str:
        bl = {
            "mu": _q(baseline.get("mu"), 6),
            "sigma": _q(baseline.get("sigma"), 6),
            "warn_threshold": _q(baseline.get("warn_threshold"), 6),
            "block_threshold": _q(baseline.get("block_threshold"), 6),
        }

        mt = {
            "risk": _q(metrics.get("risk", metrics.get("last_risk")), 6),
            "specH": _q(metrics.get("specH", metrics.get("spectral_entropy")), 6),
            "cusum": _q(metrics.get("cusum", baseline.get("cusum", 0.0)), 6),
        }

        fl = {
            "petal_area": _q((flower or {}).get("petal_area", 0.0), 9),
        }

        payload = {
            "kind": str(kind),
            "version": str(version),
            "verdict": str(verdict),
            "dna_key": str(dna_key),
            "band": int(band),
            "phase_state": int(phase_state),
            "baseline": bl,
            "metrics": mt,
            "flower": fl,
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
        version = str(report.get("version") or "0.4")

        verdict = str(report.get("verdict") or "ALLOW").upper()
        dna = str(report.get("dna") or "")
        dna_key = normalize_dna_key(dna, key_len)

        baseline = report.get("baseline") if isinstance(report.get("baseline"), dict) else {}
        metrics = _pick_metrics(report)

        phase_dir, deltas = infer_phase_dir(report, cusum_gate=cusum_gate)
        metrics.setdefault("deltas", deltas)

        band = int(report.get("band") or _band_from_verdict(verdict))
        band = max(1, min(7, band))

        phase_state = phase_state_from(band, phase_dir)

        # flower invariant from report (uses flower_cycle points)
        flower = extract_flower(report)

        now = time.time()

        crystal_key = cls.compute_crystal_key(kind, dna_key)

        atom_id = cls.compute_atom_id(
            kind=kind,
            version=version,
            verdict=verdict,
            dna_key=dna_key,
            band=band,
            phase_state=phase_state,
            baseline=baseline,
            metrics=metrics,
            flower=flower,
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
            crystal_key=crystal_key,
            strength=1,
            first_seen=now,
            last_seen=now,
            context=context,
            atom_id=atom_id,
        )

    # ---------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

    # ---------------------------------------------------------------

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryAtom":
        now = time.time()

        kind = str(d.get("kind", "NAVIGATOR_REPORT"))
        version = str(d.get("version", "0.4"))
        verdict = str(d.get("verdict", "ALLOW")).upper()
        dna = str(d.get("dna", ""))
        dna_key = str(d.get("dna_key", ""))

        baseline = d.get("baseline") if isinstance(d.get("baseline"), dict) else {}
        metrics = d.get("metrics") if isinstance(d.get("metrics"), dict) else {}

        flower = d.get("flower") if isinstance(d.get("flower"), dict) else {"petal_area": 0.0, "points": []}
        if "petal_area" not in flower:
            flower["petal_area"] = 0.0
        if "points" not in flower:
            flower["points"] = []

        crystal_key = str(d.get("crystal_key", "")).strip()
        if not crystal_key:
            crystal_key = cls.compute_crystal_key(kind, dna_key)

        atom_id = str(d.get("atom_id", "")).strip()
        if not atom_id:
            atom_id = cls.compute_atom_id(
                kind=kind,
                version=version,
                verdict=verdict,
                dna_key=dna_key,
                band=int(d.get("band", 6)),
                phase_state=int(d.get("phase_state", 1)),
                baseline=baseline,
                metrics=metrics,
                flower=flower,
            )

        return cls(
            kind=kind,
            version=version,
            verdict=verdict,
            dna=dna,
            dna_key=dna_key,
            band=int(d.get("band", 6)),
            phase_dir=int(d.get("phase_dir", 5)),
            phase_state=int(d.get("phase_state", 1)),
            baseline=baseline,
            metrics=metrics,
            flower=flower,
            crystal_key=crystal_key,
            strength=int(d.get("strength", 1)),
            first_seen=float(d.get("first_seen", now)),
            last_seen=float(d.get("last_seen", now)),
            context=d.get("context") if isinstance(d.get("context"), dict) else {},
            atom_id=atom_id,
        )
