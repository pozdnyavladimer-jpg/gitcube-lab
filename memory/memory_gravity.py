# -*- coding: utf-8 -*-
"""
memory/memory_gravity.py

Memory Gravity for GitCube Lab.

Purpose:
- compare a current report with stored MemoryAtoms from memory/memory.jsonl
- compute attraction / repulsion from stored structural memory
- rank stable attractors
- provide a simple guidance vector for future gravity_agent integration

Works with:
- memory.atom.MemoryAtom
- memory.store.MemoryStore
- report dicts from GraphEval / pipeline / agents
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from memory.atom import normalize_dna_key
from memory.store import MemoryStore, Query


# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------

VERDICT_WEIGHT = {
    "ALLOW": 1.00,
    "WARN": 0.35,
    "BLOCK": -0.80,
}

DEFAULT_COMPONENT_WEIGHTS = {
    "dna": 0.55,
    "risk": 0.20,
    "flower": 0.10,
    "phase": 0.10,
    "band": 0.05,
}


# ---------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------

@dataclass
class GravityHit:
    atom_id: str
    crystal_key: str
    verdict: str

    similarity: float
    gravity: float

    risk_similarity: float
    dna_similarity: float
    flower_similarity: float
    phase_similarity: float
    band_similarity: float

    strength: int
    phase_state: int
    band: int

    color_hex: str = "#888888"
    octave: int = 1
    octave_label: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "crystal_key": self.crystal_key,
            "verdict": self.verdict,
            "similarity": round(self.similarity, 6),
            "gravity": round(self.gravity, 6),
            "risk_similarity": round(self.risk_similarity, 6),
            "dna_similarity": round(self.dna_similarity, 6),
            "flower_similarity": round(self.flower_similarity, 6),
            "phase_similarity": round(self.phase_similarity, 6),
            "band_similarity": round(self.band_similarity, 6),
            "strength": self.strength,
            "phase_state": self.phase_state,
            "band": self.band,
            "color_hex": self.color_hex,
            "octave": self.octave,
            "octave_label": self.octave_label,
        }


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def report_dna(report: Dict[str, Any]) -> str:
    return str(report.get("dna", "")).strip()


def report_risk(report: Dict[str, Any]) -> float:
    return _num(report.get("risk", 1.0), 1.0)


def report_flower_area(report: Dict[str, Any]) -> float:
    flower = report.get("flower")
    if isinstance(flower, dict):
        return _num(flower.get("petal_area", 0.0), 0.0)
    return 0.0


def report_band(report: Dict[str, Any]) -> int:
    v = report.get("band", 1)
    try:
        return int(v)
    except Exception:
        return 1


def report_phase_state(report: Dict[str, Any]) -> int:
    v = report.get("phase_state", 1)
    try:
        return int(v)
    except Exception:
        return 1


def jaccard_similarity(a: Sequence[str], b: Sequence[str]) -> float:
    sa = set([x for x in a if x])
    sb = set([x for x in b if x])

    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0

    return len(sa & sb) / max(1, len(sa | sb))


def dna_similarity(current_dna: str, memory_dna: str) -> float:
    a = normalize_dna_key(current_dna, key_len=8).split("|")
    b = normalize_dna_key(memory_dna, key_len=8).split("|")
    return float(jaccard_similarity(a, b))


def risk_similarity(current_risk: float, memory_risk: float) -> float:
    diff = abs(float(current_risk) - float(memory_risk))
    return clamp(1.0 - diff, 0.0, 1.0)


def flower_similarity(current_area: float, memory_area: float) -> float:
    scale = max(1.0, abs(current_area), abs(memory_area))
    diff = abs(current_area - memory_area) / scale
    return clamp(1.0 - diff, 0.0, 1.0)


def phase_similarity(current_phase: int, memory_phase: int) -> float:
    diff = abs(int(current_phase) - int(memory_phase))
    # max distance in 42-state space = 41
    return clamp(1.0 - (diff / 41.0), 0.0, 1.0)


def band_similarity(current_band: int, memory_band: int) -> float:
    diff = abs(int(current_band) - int(memory_band))
    # max distance in 7-band space = 6
    return clamp(1.0 - (diff / 6.0), 0.0, 1.0)


def verdict_weight(verdict: str) -> float:
    return VERDICT_WEIGHT.get(str(verdict).upper(), 0.0)


def phase_state_to_octave_and_color(phase_state: int) -> Tuple[int, str]:
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


def default_color_for_band(band: int) -> str:
    palette = {
        1: "#680000",
        2: "#9a4700",
        3: "#c7a500",
        4: "#729d00",
        5: "#237d38",
        6: "#007286",
        7: "#4b51b8",
    }
    return palette.get(int(band), "#888888")


# ---------------------------------------------------------------------
# Canonical view
# ---------------------------------------------------------------------

def atom_row_to_view(row: Dict[str, Any]) -> Dict[str, Any]:
    phase_state = int(row.get("phase_state", 1) or 1)
    band = int(row.get("band", 1) or 1)
    octave, octave_label = phase_state_to_octave_and_color(phase_state)

    flower = row.get("flower") if isinstance(row.get("flower"), dict) else {}

    return {
        "atom_id": str(row.get("atom_id", "")),
        "crystal_key": str(row.get("crystal_key", "")),
        "verdict": str(row.get("verdict", "WARN")),
        "risk": _num(
            (row.get("metrics") or {}).get("risk", (row.get("metrics") or {}).get("last_risk", 1.0)),
            1.0,
        ),
        "dna": str(row.get("dna", "")),
        "band": band,
        "phase_state": phase_state,
        "strength": int(row.get("strength", 1) or 1),
        "flower_area": _num(flower.get("petal_area", 0.0), 0.0),
        "color_hex": default_color_for_band(band),
        "octave": octave,
        "octave_label": octave_label,
    }


# ---------------------------------------------------------------------
# Gravity engine
# ---------------------------------------------------------------------

def compute_similarity(
    report: Dict[str, Any],
    memory_view: Dict[str, Any],
    *,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, Dict[str, float]]:
    w = dict(DEFAULT_COMPONENT_WEIGHTS)
    if weights:
        w.update(weights)

    sim_dna = dna_similarity(report_dna(report), str(memory_view.get("dna", "")))
    sim_risk = risk_similarity(report_risk(report), _num(memory_view.get("risk", 1.0), 1.0))
    sim_flower = flower_similarity(report_flower_area(report), _num(memory_view.get("flower_area", 0.0), 0.0))
    sim_phase = phase_similarity(report_phase_state(report), int(memory_view.get("phase_state", 1)))
    sim_band = band_similarity(report_band(report), int(memory_view.get("band", 1)))

    sim = (
        w["dna"] * sim_dna
        + w["risk"] * sim_risk
        + w["flower"] * sim_flower
        + w["phase"] * sim_phase
        + w["band"] * sim_band
    )

    parts = {
        "dna": sim_dna,
        "risk": sim_risk,
        "flower": sim_flower,
        "phase": sim_phase,
        "band": sim_band,
    }
    return float(sim), parts


def compute_gravity(
    report: Dict[str, Any],
    memory_view: Dict[str, Any],
    *,
    weights: Optional[Dict[str, float]] = None,
    strength_power: float = 1.0,
) -> GravityHit:
    similarity, parts = compute_similarity(report, memory_view, weights=weights)

    strength = max(1, int(memory_view.get("strength", 1)))
    v_weight = verdict_weight(str(memory_view.get("verdict", "WARN")))
    gravity = similarity * (strength ** float(strength_power)) * v_weight

    return GravityHit(
        atom_id=str(memory_view.get("atom_id", "")),
        crystal_key=str(memory_view.get("crystal_key", "")),
        verdict=str(memory_view.get("verdict", "WARN")),
        similarity=float(similarity),
        gravity=float(gravity),
        risk_similarity=float(parts["risk"]),
        dna_similarity=float(parts["dna"]),
        flower_similarity=float(parts["flower"]),
        phase_similarity=float(parts["phase"]),
        band_similarity=float(parts["band"]),
        strength=int(strength),
        phase_state=int(memory_view.get("phase_state", 1)),
        band=int(memory_view.get("band", 1)),
        color_hex=str(memory_view.get("color_hex", "#888888")),
        octave=int(memory_view.get("octave", 1)),
        octave_label=str(memory_view.get("octave_label", "UNKNOWN")),
    )


def rank_rows(
    report: Dict[str, Any],
    rows: List[Dict[str, Any]],
    *,
    top_k: int = 5,
) -> List[GravityHit]:
    hits: List[GravityHit] = []

    for row in rows:
        mv = atom_row_to_view(row)
        hits.append(compute_gravity(report, mv))

    hits.sort(key=lambda h: h.gravity, reverse=True)
    return hits[: max(1, int(top_k))]


def select_best_attractor(
    report: Dict[str, Any],
    rows: List[Dict[str, Any]],
) -> Optional[GravityHit]:
    hits = rank_rows(report, rows, top_k=1)
    return hits[0] if hits else None


# ---------------------------------------------------------------------
# High-level memory interface
# ---------------------------------------------------------------------

class MemoryGravity:
    """
    Convenience wrapper over MemoryStore.

    Reads from memory/memory.jsonl by default.
    """

    def __init__(self, store_path: str = "memory/memory.jsonl") -> None:
        self.store = MemoryStore(path=store_path)

    def _load_rows(self) -> List[Dict[str, Any]]:
        return self.store.query(Query(limit=10000))

    def top_hits(self, report: Dict[str, Any], top_k: int = 5) -> List[GravityHit]:
        rows = self._load_rows()
        return rank_rows(report, rows, top_k=top_k)

    def best_attractor(self, report: Dict[str, Any]) -> Optional[GravityHit]:
        rows = self._load_rows()
        return select_best_attractor(report, rows)

    def guidance_vector(self, report: Dict[str, Any]) -> Dict[str, float]:
        """
        Simple derived guidance signal:
        - positive means drift toward stored stable atoms
        - negative / weak means memory is not informative yet
        """
        hits = self.top_hits(report, top_k=5)
        if not hits:
            return {
                "gravity_mean": 0.0,
                "gravity_max": 0.0,
                "confidence": 0.0,
            }

        g_values = [h.gravity for h in hits]
        s_values = [h.similarity for h in hits]

        gravity_mean = sum(g_values) / len(g_values)
        gravity_max = max(g_values)
        confidence = sum(s_values) / len(s_values)

        return {
            "gravity_mean": round(float(gravity_mean), 6),
            "gravity_max": round(float(gravity_max), 6),
            "confidence": round(float(confidence), 6),
        }


# ---------------------------------------------------------------------
# Demo / CLI
# ---------------------------------------------------------------------

def main() -> None:
    import json

    demo_report = {
        "kind": "GRAPH_EVAL",
        "verdict": "ALLOW",
        "risk": 0.12,
        "dna": "C0 L0 D1 H1",
        "band": 6,
        "phase_state": 35,
        "flower": {
            "petal_area": 0.08,
        },
    }

    mg = MemoryGravity(store_path="memory/memory.jsonl")

    hits = mg.top_hits(demo_report, top_k=5)
    guidance = mg.guidance_vector(demo_report)
    best = mg.best_attractor(demo_report)

    out = {
        "demo_report": demo_report,
        "best_attractor": best.to_dict() if best else None,
        "guidance": guidance,
        "top_hits": [h.to_dict() for h in hits],
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
