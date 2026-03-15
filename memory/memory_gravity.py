# -*- coding: utf-8 -*-
"""
memory/memory_gravity.py

Memory Gravity for GitCube Lab.

Purpose:
- compare a current report with stored crystal memory
- compute attraction / repulsion from stored MemoryAtoms / CrystalRecords
- rank stable attractors
- provide a simple gravity field for future gravity_agent integration

Works with:
- memory.atom.MemoryAtom
- memory.crystal_memory.CrystalRecord
- report dicts from GraphEval / run_lab / agents
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from memory.atom import MemoryAtom, normalize_dna_key
from memory.crystal_memory import CrystalMemory, CrystalRecord


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
    return int(report.get("band", 1))


def report_phase_state(report: Dict[str, Any]) -> int:
    return int(report.get("phase_state", 1))


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


# ---------------------------------------------------------------------
# Canonical view
# ---------------------------------------------------------------------

def crystal_to_view(rec: CrystalRecord) -> Dict[str, Any]:
    return {
        "atom_id": rec.atom_id,
        "crystal_key": rec.crystal_key,
        "verdict": rec.verdict,
        "risk": rec.risk,
        "dna": rec.dna,
        "band": rec.band,
        "phase_state": rec.phase_state,
        "strength": rec.strength,
        "flower_area": _num(rec.flower.get("petal_area", 0.0), 0.0),
        "color_hex": str(rec.spectral.get("hex", "#888888")),
        "octave": int(rec.spectral.get("octave", 1)),
        "octave_label": str(rec.spectral.get("octave_label", "UNKNOWN")),
    }


def atom_to_view(atom: MemoryAtom) -> Dict[str, Any]:
    return {
        "atom_id": atom.atom_id,
        "crystal_key": atom.crystal_key,
        "verdict": atom.verdict,
        "risk": _num(atom.metrics.get("risk", atom.metrics.get("last_risk", 1.0)), 1.0),
        "dna": atom.dna,
        "band": atom.band,
        "phase_state": atom.phase_state,
        "strength": atom.strength,
        "flower_area": _num(atom.flower.get("petal_area", 0.0), 0.0),
        "color_hex": "#888888",
        "octave": ((int(atom.phase_state) - 1) // 6) + 1,
        "octave_label": "UNKNOWN",
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


def rank_crystals(
    report: Dict[str, Any],
    crystals: List[CrystalRecord],
    *,
    top_k: int = 5,
    only_assembled: bool = True,
) -> List[GravityHit]:
    hits: List[GravityHit] = []

    for rec in crystals:
        if only_assembled and not rec.assembly_ok:
            continue
        mv = crystal_to_view(rec)
        hits.append(compute_gravity(report, mv))

    hits.sort(key=lambda h: h.gravity, reverse=True)
    return hits[: max(1, int(top_k))]


def rank_atoms(
    report: Dict[str, Any],
    atoms: List[MemoryAtom],
    *,
    top_k: int = 5,
) -> List[GravityHit]:
    hits: List[GravityHit] = []

    for atom in atoms:
        mv = atom_to_view(atom)
        hits.append(compute_gravity(report, mv))

    hits.sort(key=lambda h: h.gravity, reverse=True)
    return hits[: max(1, int(top_k))]


def select_best_attractor(
    report: Dict[str, Any],
    crystals: List[CrystalRecord],
) -> Optional[GravityHit]:
    hits = rank_crystals(report, crystals, top_k=1, only_assembled=True)
    return hits[0] if hits else None


# ---------------------------------------------------------------------
# High-level memory interface
# ---------------------------------------------------------------------

class MemoryGravity:
    """
    Convenience wrapper over CrystalMemory.
    """

    def __init__(self, store_path: str = "memory/crystal_memory.jsonl") -> None:
        self.memory = CrystalMemory(store_path=store_path)

    def top_hits(self, report: Dict[str, Any], top_k: int = 5) -> List[GravityHit]:
        crystals = self.memory.load_all()
        return rank_crystals(report, crystals, top_k=top_k, only_assembled=True)

    def best_attractor(self, report: Dict[str, Any]) -> Optional[GravityHit]:
        crystals = self.memory.load_all()
        return select_best_attractor(report, crystals)

    def guidance_vector(self, report: Dict[str, Any]) -> Dict[str, float]:
        """
        Simple derived guidance signal:
        - positive means drift toward stored stable crystals
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
