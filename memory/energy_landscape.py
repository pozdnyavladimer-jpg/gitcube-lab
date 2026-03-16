# -*- coding: utf-8 -*-
"""
memory/energy_landscape.py

Architecture Energy Landscape for GitCube Lab.

Purpose:
- read structural memory from memory/memory.jsonl
- interpret memory atoms as points in an energy landscape
- aggregate states by (phase_state, band)
- estimate basins / unstable zones
- provide a simple landscape view for future visualization

Current simple model:
    energy = risk

Future extensions may include:
    energy =
        a * risk
      + b * cycle_pressure
      + c * density_pressure
      + d * feedback_toxicity
      + e * memory_repulsion
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from memory.store import MemoryStore, Query


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


def _int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def row_risk(row: Dict[str, Any]) -> float:
    metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
    return _num(metrics.get("risk", metrics.get("last_risk", row.get("risk", 1.0))), 1.0)


def row_band(row: Dict[str, Any]) -> int:
    return _int(row.get("band", 1), 1)


def row_phase_state(row: Dict[str, Any]) -> int:
    return _int(row.get("phase_state", 1), 1)


def row_strength(row: Dict[str, Any]) -> int:
    return max(1, _int(row.get("strength", 1), 1))


def row_verdict(row: Dict[str, Any]) -> str:
    return str(row.get("verdict", "WARN")).upper()


def row_dna(row: Dict[str, Any]) -> str:
    return str(row.get("dna", ""))


def row_flower_area(row: Dict[str, Any]) -> float:
    flower = row.get("flower") if isinstance(row.get("flower"), dict) else {}
    return _num(flower.get("petal_area", 0.0), 0.0)


def phase_state_to_octave(phase_state: int) -> Tuple[int, str]:
    s = max(1, min(42, int(phase_state)))
    octave = ((s - 1) // 6) + 1
    labels = {
        1: "CHAOS",
        2: "UNSTABLE",
        3: "FORMING",
        4: "STRUCTURAL",
        5: "STABLE",
        6: "RESONANT",
        7: "CRYSTAL",
    }
    return octave, labels.get(octave, "UNKNOWN")


def energy_from_row(row: Dict[str, Any]) -> float:
    """
    Current simple energy model.
    Lower = more stable.
    Higher = more unstable.
    """
    return clamp(row_risk(row), 0.0, 1.0)


# ---------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------

@dataclass
class LandscapePoint:
    phase_state: int
    band: int
    octave: int
    octave_label: str

    count: int
    strength_sum: int

    energy_mean: float
    energy_min: float
    energy_max: float

    flower_area_mean: float

    dominant_verdict: str
    sample_dna: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_state": self.phase_state,
            "band": self.band,
            "octave": self.octave,
            "octave_label": self.octave_label,
            "count": self.count,
            "strength_sum": self.strength_sum,
            "energy_mean": round(float(self.energy_mean), 6),
            "energy_min": round(float(self.energy_min), 6),
            "energy_max": round(float(self.energy_max), 6),
            "flower_area_mean": round(float(self.flower_area_mean), 6),
            "dominant_verdict": self.dominant_verdict,
            "sample_dna": self.sample_dna,
        }


@dataclass
class LandscapeSummary:
    items: int
    unique_cells: int
    lowest_energy_cell: Optional[Dict[str, Any]]
    highest_energy_cell: Optional[Dict[str, Any]]
    stable_basins: List[Dict[str, Any]]
    unstable_zones: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "unique_cells": self.unique_cells,
            "lowest_energy_cell": self.lowest_energy_cell,
            "highest_energy_cell": self.highest_energy_cell,
            "stable_basins": self.stable_basins,
            "unstable_zones": self.unstable_zones,
        }


# ---------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------

def dominant_verdict(verdicts: List[str]) -> str:
    if not verdicts:
        return "UNKNOWN"
    counts: Dict[str, int] = {}
    for v in verdicts:
        counts[v] = counts.get(v, 0) + 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[0][0]


def aggregate_landscape(rows: List[Dict[str, Any]]) -> List[LandscapePoint]:
    buckets: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}

    for row in rows:
        phase_state = row_phase_state(row)
        band = row_band(row)
        key = (phase_state, band)
        buckets.setdefault(key, []).append(row)

    out: List[LandscapePoint] = []

    for (phase_state, band), items in buckets.items():
        energies = [energy_from_row(r) for r in items]
        strengths = [row_strength(r) for r in items]
        flower_areas = [row_flower_area(r) for r in items]
        verdicts = [row_verdict(r) for r in items]

        octave, octave_label = phase_state_to_octave(phase_state)

        lp = LandscapePoint(
            phase_state=phase_state,
            band=band,
            octave=octave,
            octave_label=octave_label,
            count=len(items),
            strength_sum=sum(strengths),
            energy_mean=sum(energies) / max(1, len(energies)),
            energy_min=min(energies) if energies else 0.0,
            energy_max=max(energies) if energies else 0.0,
            flower_area_mean=sum(flower_areas) / max(1, len(flower_areas)),
            dominant_verdict=dominant_verdict(verdicts),
            sample_dna=row_dna(items[0]) if items else "",
        )
        out.append(lp)

    out.sort(key=lambda x: (x.energy_mean, -x.strength_sum, -x.count))
    return out


# ---------------------------------------------------------------------
# Basin / zone analysis
# ---------------------------------------------------------------------

def find_stable_basins(points: List[LandscapePoint], limit: int = 5) -> List[LandscapePoint]:
    """
    Stable basin heuristic:
    - dominant verdict should prefer ALLOW
    - lower energy is better
    - higher strength_sum means more confirmed
    """
    stable = [
        p for p in points
        if p.dominant_verdict == "ALLOW"
    ]

    stable.sort(key=lambda p: (p.energy_mean, -p.strength_sum, -p.count))
    return stable[: max(1, int(limit))]


def find_unstable_zones(points: List[LandscapePoint], limit: int = 5) -> List[LandscapePoint]:
    """
    Unstable zone heuristic:
    - dominant verdict BLOCK preferred
    - higher energy worse
    - higher strength_sum means repeated danger
    """
    bad = [
        p for p in points
        if p.dominant_verdict == "BLOCK"
    ]

    bad.sort(key=lambda p: (p.energy_mean, p.strength_sum, p.count), reverse=True)
    return bad[: max(1, int(limit))]


def summarize_landscape(points: List[LandscapePoint], total_items: int) -> LandscapeSummary:
    if not points:
        return LandscapeSummary(
            items=total_items,
            unique_cells=0,
            lowest_energy_cell=None,
            highest_energy_cell=None,
            stable_basins=[],
            unstable_zones=[],
        )

    lowest = min(points, key=lambda p: p.energy_mean)
    highest = max(points, key=lambda p: p.energy_mean)

    stable = find_stable_basins(points, limit=5)
    unstable = find_unstable_zones(points, limit=5)

    return LandscapeSummary(
        items=total_items,
        unique_cells=len(points),
        lowest_energy_cell=lowest.to_dict(),
        highest_energy_cell=highest.to_dict(),
        stable_basins=[p.to_dict() for p in stable],
        unstable_zones=[p.to_dict() for p in unstable],
    )


# ---------------------------------------------------------------------
# High-level API
# ---------------------------------------------------------------------

class EnergyLandscape:
    def __init__(self, store_path: str = "memory/memory.jsonl") -> None:
        self.store = MemoryStore(path=store_path)

    def load_rows(self) -> List[Dict[str, Any]]:
        return self.store.query(Query(limit=10000))

    def points(self) -> List[LandscapePoint]:
        rows = self.load_rows()
        return aggregate_landscape(rows)

    def summary(self) -> LandscapeSummary:
        rows = self.load_rows()
        points = aggregate_landscape(rows)
        return summarize_landscape(points, total_items=len(rows))

    def nearest_cell(self, *, phase_state: int, band: int) -> Optional[LandscapePoint]:
        points = self.points()
        if not points:
            return None

        best = min(
            points,
            key=lambda p: abs(p.phase_state - int(phase_state)) + abs(p.band - int(band)),
        )
        return best


# ---------------------------------------------------------------------
# Demo / CLI
# ---------------------------------------------------------------------

def main() -> None:
    import json

    landscape = EnergyLandscape(store_path="memory/memory.jsonl")

    points = landscape.points()
    summary = landscape.summary()

    out = {
        "summary": summary.to_dict(),
        "points": [p.to_dict() for p in points[:20]],  # show first 20
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
