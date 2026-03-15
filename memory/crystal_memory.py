# -*- coding: utf-8 -*-
"""
memory/crystal_memory.py

Crystal memory layer for GitCube Lab.

Purpose:
- convert GraphEval / pipeline reports into crystallized memory entries
- validate whether a state is stable enough to be stored
- enrich MemoryAtom-like records with:
    - color tags
    - octave / band naming
    - 42-state spectral indexing
    - neighbor links
    - assembly code
- save / load JSONL memory

This module is intentionally compatible with the existing memory/atom.py idea:
- band: 1..7
- phase_dir: 0..5
- phase_state: 1..42
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from memory.atom import MemoryAtom, normalize_dna_key


# ---------------------------------------------------------------------
# Spectral system: 7 octaves × 6 colors = 42 states
# ---------------------------------------------------------------------

OCTAVE_LABELS = {
    1: "CHAOS",
    2: "UNSTABLE",
    3: "FORMING",
    4: "STRUCTURAL",
    5: "STABLE",
    6: "RESONANT",
    7: "CRYSTAL",
}

# 6 color slots inside each octave
COLOR_SLOT_LABELS = {
    0: "DEEP",
    1: "HEAVY",
    2: "TENSE",
    3: "SHIFT",
    4: "SOFT",
    5: "CLEAR",
}

# simple 42-color palette placeholder:
# later you can replace with your exact 42 colors
COLOR_SPECTRUM = {
    1:  "#2b0000",
    2:  "#4a0000",
    3:  "#680000",
    4:  "#8a1100",
    5:  "#aa2a00",
    6:  "#c94700",

    7:  "#3a1400",
    8:  "#5a2200",
    9:  "#7a3300",
    10: "#9a4700",
    11: "#b95d00",
    12: "#d87700",

    13: "#4d3a00",
    14: "#6d5500",
    15: "#8c7000",
    16: "#aa8a00",
    17: "#c7a500",
    18: "#e1c000",

    19: "#304d00",
    20: "#456800",
    21: "#5d8300",
    22: "#729d00",
    23: "#89b800",
    24: "#a3d200",

    25: "#0f4a1f",
    26: "#17632b",
    27: "#237d38",
    28: "#34974c",
    29: "#4cb260",
    30: "#67cb78",

    31: "#003f4d",
    32: "#005969",
    33: "#007286",
    34: "#178ca3",
    35: "#35a7bf",
    36: "#58c1d9",

    37: "#1c2458",
    38: "#30398d",
    39: "#4b51b8",
    40: "#6e73d2",
    41: "#98a0ea",
    42: "#d7dcff",
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default


def _now() -> float:
    return time.time()


def ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)


def safe_json_loads(line: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(line)
    except Exception:
        return None


def phase_state_to_octave_and_color(phase_state: int) -> Tuple[int, int]:
    s = max(1, min(42, int(phase_state)))
    octave = ((s - 1) // 6) + 1
    color_slot = (s - 1) % 6
    return octave, color_slot


def color_tag_from_phase_state(phase_state: int) -> Dict[str, Any]:
    octave, color_slot = phase_state_to_octave_and_color(phase_state)
    return {
        "phase_state": int(phase_state),
        "octave": octave,
        "octave_label": OCTAVE_LABELS.get(octave, "UNKNOWN"),
        "color_slot": color_slot,
        "color_slot_label": COLOR_SLOT_LABELS.get(color_slot, "UNKNOWN"),
        "hex": COLOR_SPECTRUM.get(int(phase_state), "#888888"),
    }


# ---------------------------------------------------------------------
# Assembly Validator
# ---------------------------------------------------------------------

class AssemblyValidator:
    """
    Decide whether a graph/report is assembled enough to become a crystal.

    This is intentionally strict:
    - ALLOW required
    - low risk required
    - critical DNA faults forbidden
    """

    STABILITY_THRESHOLD = 0.05
    CRITICAL_TOKENS = {"C1", "C2", "L1", "L2", "T1", "T2"}

    @staticmethod
    def is_assembled(report: Dict[str, Any]) -> Tuple[bool, str]:
        verdict = str(report.get("verdict", "BLOCK")).upper()
        risk = _num(report.get("risk", 1.0), 1.0)
        dna = str(report.get("dna", "")).strip()

        if verdict != "ALLOW":
            return False, "verdict is not ALLOW"

        toks = set(dna.replace(",", " ").split())
        if toks & AssemblyValidator.CRITICAL_TOKENS:
            return False, "critical DNA tokens still present"

        if risk > AssemblyValidator.STABILITY_THRESHOLD:
            return False, "risk above assembly threshold"

        return True, "assembled"


# ---------------------------------------------------------------------
# Crystal record
# ---------------------------------------------------------------------

@dataclass
class CrystalRecord:
    atom_id: str
    crystal_key: str

    verdict: str
    risk: float
    dna: str
    dna_key: str

    band: int
    phase_dir: int
    phase_state: int

    spectral: Dict[str, Any]
    flower: Dict[str, Any]

    strength: int
    first_seen: float
    last_seen: float

    assembly_ok: bool
    assembly_reason: str

    neighbors: List[str] = field(default_factory=list)
    assembly_code: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "crystal_key": self.crystal_key,
            "verdict": self.verdict,
            "risk": self.risk,
            "dna": self.dna,
            "dna_key": self.dna_key,
            "band": self.band,
            "phase_dir": self.phase_dir,
            "phase_state": self.phase_state,
            "spectral": self.spectral,
            "flower": self.flower,
            "strength": self.strength,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "assembly_ok": self.assembly_ok,
            "assembly_reason": self.assembly_reason,
            "neighbors": self.neighbors,
            "assembly_code": self.assembly_code,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CrystalRecord":
        return cls(
            atom_id=str(d.get("atom_id", "")),
            crystal_key=str(d.get("crystal_key", "")),
            verdict=str(d.get("verdict", "ALLOW")),
            risk=_num(d.get("risk", 0.0), 0.0),
            dna=str(d.get("dna", "")),
            dna_key=str(d.get("dna_key", "")),
            band=int(d.get("band", 1)),
            phase_dir=int(d.get("phase_dir", 0)),
            phase_state=int(d.get("phase_state", 1)),
            spectral=d.get("spectral") if isinstance(d.get("spectral"), dict) else {},
            flower=d.get("flower") if isinstance(d.get("flower"), dict) else {},
            strength=int(d.get("strength", 1)),
            first_seen=_num(d.get("first_seen", _now()), _now()),
            last_seen=_num(d.get("last_seen", _now()), _now()),
            assembly_ok=bool(d.get("assembly_ok", False)),
            assembly_reason=str(d.get("assembly_reason", "")),
            neighbors=list(d.get("neighbors", [])),
            assembly_code=list(d.get("assembly_code", [])),
            context=d.get("context") if isinstance(d.get("context"), dict) else {},
        )


# ---------------------------------------------------------------------
# Crystal Memory
# ---------------------------------------------------------------------

class CrystalMemory:
    """
    JSONL-backed crystal memory.

    Stores only assembled states by default.
    """

    def __init__(self, store_path: str = "memory/crystal_memory.jsonl") -> None:
        self.store_path = store_path

    # -------------------------------------------------------------
    # IO
    # -------------------------------------------------------------

    def load_all(self) -> List[CrystalRecord]:
        if not os.path.exists(self.store_path):
            return []

        rows: List[CrystalRecord] = []
        with open(self.store_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = safe_json_loads(line)
                if not raw:
                    continue
                try:
                    rows.append(CrystalRecord.from_dict(raw))
                except Exception:
                    continue
        return rows

    def write_all(self, rows: List[CrystalRecord]) -> None:
        ensure_parent(self.store_path)
        with open(self.store_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

    def append(self, row: CrystalRecord) -> None:
        ensure_parent(self.store_path)
        with open(self.store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

    # -------------------------------------------------------------
    # Record creation
    # -------------------------------------------------------------

    def report_to_atom(
        self,
        report: Dict[str, Any],
        *,
        repo: Optional[str] = None,
        ref: Optional[str] = None,
        note: Optional[str] = None,
    ) -> MemoryAtom:
        return MemoryAtom.from_report(
            report,
            repo=repo,
            ref=ref,
            note=note,
        )

    def atom_to_crystal(
        self,
        atom: MemoryAtom,
        *,
        assembly_code: Optional[List[str]] = None,
        neighbors: Optional[List[str]] = None,
    ) -> CrystalRecord:
        assembly_ok, assembly_reason = AssemblyValidator.is_assembled(
            {
                "verdict": atom.verdict,
                "risk": atom.metrics.get("risk", atom.metrics.get("last_risk", 0.0)),
                "dna": atom.dna,
            }
        )

        spectral = color_tag_from_phase_state(atom.phase_state)

        return CrystalRecord(
            atom_id=atom.atom_id,
            crystal_key=atom.crystal_key,
            verdict=atom.verdict,
            risk=_num(atom.metrics.get("risk", atom.metrics.get("last_risk", 0.0)), 0.0),
            dna=atom.dna,
            dna_key=atom.dna_key,
            band=int(atom.band),
            phase_dir=int(atom.phase_dir),
            phase_state=int(atom.phase_state),
            spectral=spectral,
            flower=dict(atom.flower),
            strength=int(atom.strength),
            first_seen=float(atom.first_seen),
            last_seen=float(atom.last_seen),
            assembly_ok=assembly_ok,
            assembly_reason=assembly_reason,
            neighbors=list(neighbors or []),
            assembly_code=list(assembly_code or []),
            context=dict(atom.context),
        )

    def record_report(
        self,
        report: Dict[str, Any],
        *,
        repo: Optional[str] = None,
        ref: Optional[str] = None,
        note: Optional[str] = None,
        assembly_code: Optional[List[str]] = None,
        allow_unassembled: bool = False,
    ) -> Optional[CrystalRecord]:
        atom = self.report_to_atom(report, repo=repo, ref=ref, note=note)
        rows = self.load_all()

        neighbors = self.find_neighbors(atom.dna, rows, top_k=6)
        rec = self.atom_to_crystal(atom, assembly_code=assembly_code, neighbors=neighbors)

        if not rec.assembly_ok and not allow_unassembled:
            return None

        existing_idx = self._find_by_atom_id(rows, rec.atom_id)

        if existing_idx is None:
            self.append(rec)
            return rec

        # merge strength / timestamps
        old = rows[existing_idx]
        merged = CrystalRecord(
            atom_id=old.atom_id,
            crystal_key=old.crystal_key,
            verdict=rec.verdict,
            risk=rec.risk,
            dna=rec.dna,
            dna_key=rec.dna_key,
            band=rec.band,
            phase_dir=rec.phase_dir,
            phase_state=rec.phase_state,
            spectral=rec.spectral,
            flower=rec.flower,
            strength=int(old.strength) + 1,
            first_seen=float(old.first_seen),
            last_seen=_now(),
            assembly_ok=rec.assembly_ok,
            assembly_reason=rec.assembly_reason,
            neighbors=rec.neighbors,
            assembly_code=rec.assembly_code or old.assembly_code,
            context=rec.context or old.context,
        )

        rows[existing_idx] = merged
        self.write_all(rows)
        return merged

    # -------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------

    def _find_by_atom_id(self, rows: List[CrystalRecord], atom_id: str) -> Optional[int]:
        for i, r in enumerate(rows):
            if r.atom_id == atom_id:
                return i
        return None

    def find_by_crystal_key(self, crystal_key: str) -> List[CrystalRecord]:
        rows = self.load_all()
        return [r for r in rows if r.crystal_key == crystal_key]

    def find_neighbors(self, dna: str, rows: Optional[List[CrystalRecord]] = None, top_k: int = 6) -> List[str]:
        rows = rows if rows is not None else self.load_all()
        scored: List[Tuple[float, str]] = []

        cur = set(normalize_dna_key(dna, key_len=8).split("|"))
        cur.discard("")

        for r in rows:
            other = set(normalize_dna_key(r.dna, key_len=8).split("|"))
            other.discard("")
            if not cur and not other:
                sim = 1.0
            elif not cur or not other:
                sim = 0.0
            else:
                sim = len(cur & other) / max(1, len(cur | other))
            scored.append((sim, r.atom_id))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [atom_id for _, atom_id in scored[: max(1, int(top_k))]]

    def strongest(self, verdict: Optional[str] = None, limit: int = 10) -> List[CrystalRecord]:
        rows = self.load_all()
        if verdict:
            rows = [r for r in rows if r.verdict.upper() == verdict.upper()]
        rows.sort(key=lambda r: (r.strength, -r.risk), reverse=True)
        return rows[: max(1, int(limit))]

    def stats(self) -> Dict[str, Any]:
        rows = self.load_all()
        if not rows:
            return {
                "items": 0,
                "allow": 0,
                "warn": 0,
                "block": 0,
                "assembled": 0,
                "mean_strength": 0.0,
            }

        allow = sum(1 for r in rows if r.verdict == "ALLOW")
        warn = sum(1 for r in rows if r.verdict == "WARN")
        block = sum(1 for r in rows if r.verdict == "BLOCK")
        assembled = sum(1 for r in rows if r.assembly_ok)
        mean_strength = sum(r.strength for r in rows) / len(rows)

        return {
            "items": len(rows),
            "allow": allow,
            "warn": warn,
            "block": block,
            "assembled": assembled,
            "mean_strength": round(mean_strength, 4),
        }
