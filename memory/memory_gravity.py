# -*- coding: utf-8 -*-
"""
memory_gravity.py

Compute attraction / repulsion between current report and stored MemoryAtoms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from memory.atom import MemoryAtom, normalize_dna_key


@dataclass
class GravityHit:
    atom_id: str
    crystal_key: str
    verdict: str
    similarity: float
    gravity: float
    strength: int
    phase_state: int


VERDICT_WEIGHT = {
    "ALLOW": 1.0,
    "WARN": 0.4,
    "BLOCK": -0.8,
}


def dna_similarity(current_dna: str, atom_dna: str) -> float:
    """
    Very simple similarity:
    compare normalized DNA tokens by overlap.
    """
    a = set(normalize_dna_key(current_dna, key_len=8).split("|"))
    b = set(normalize_dna_key(atom_dna, key_len=8).split("|"))

    a.discard("")
    b.discard("")

    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0

    inter = len(a & b)
    union = len(a | b)
    return float(inter / max(1, union))


def risk_similarity(current_risk: float, atom_risk: float) -> float:
    diff = abs(float(current_risk) - float(atom_risk))
    return max(0.0, 1.0 - diff)


def flower_similarity(current_area: float, atom_area: float) -> float:
    denom = max(1e-9, max(abs(current_area), abs(atom_area), 1.0))
    diff = abs(current_area - atom_area) / denom
    return max(0.0, 1.0 - diff)


def atom_gravity(report: Dict, atom: MemoryAtom) -> GravityHit:
    current_dna = str(report.get("dna", ""))
    current_risk = float(report.get("risk", 1.0))
    current_area = float(report.get("flower", {}).get("petal_area", 0.0))

    atom_risk = float(atom.metrics.get("risk", atom.metrics.get("last_risk", 1.0)))
    atom_area = float(atom.flower.get("petal_area", 0.0))

    sim_dna = dna_similarity(current_dna, atom.dna)
    sim_risk = risk_similarity(current_risk, atom_risk)
    sim_flower = flower_similarity(current_area, atom_area)

    similarity = 0.55 * sim_dna + 0.30 * sim_risk + 0.15 * sim_flower

    verdict_weight = VERDICT_WEIGHT.get(atom.verdict.upper(), 0.0)
    gravity = similarity * max(1.0, float(atom.strength)) * verdict_weight

    return GravityHit(
        atom_id=atom.atom_id,
        crystal_key=atom.crystal_key,
        verdict=atom.verdict,
        similarity=round(similarity, 6),
        gravity=round(gravity, 6),
        strength=int(atom.strength),
        phase_state=int(atom.phase_state),
    )


def rank_atoms(report: Dict, atoms: List[MemoryAtom], top_k: int = 5) -> List[GravityHit]:
    hits = [atom_gravity(report, a) for a in atoms]
    hits.sort(key=lambda x: x.gravity, reverse=True)
    return hits[: max(1, int(top_k))]


def select_best_attractor(report: Dict, atoms: List[MemoryAtom]) -> GravityHit | None:
    hits = rank_atoms(report, atoms, top_k=1)
    return hits[0] if hits else None
