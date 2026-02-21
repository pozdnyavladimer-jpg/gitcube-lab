# -*- coding: utf-8 -*-
"""
Memory Atom (Topological Memory) — v0.2
- Deterministic atom_id (no timestamps / repo / ref included in hash)
- Indexed dna_key for fast, exact lookup
- Works for both DNA alphabets:
  - Structural DNA: C L D S H E P M
  - HFS DNA:        T R P S C F W M
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


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

    # Remove "DNA:" prefix if present
    if s.lower().startswith("dna:"):
        s = s.split(":", 1)[1].strip()

    # Tokenize by whitespace and keep tokens like "Xn"
    toks = []
    for t in s.replace(",", " ").split():
        t = t.strip()
        if not t:
            continue
        # minimal sanity: starts with letter, ends with digit
        if len(t) >= 2 and t[0].isalpha() and t[-1].isdigit():
            toks.append(t)

    toks = toks[: max(1, int(key_len))]
    return "|".join(toks)


def _band_from_verdict(verdict: str) -> int:
    """
    Band 1..7 (1 = hottest / most dangerous).
    If report already provides band, we use it. This is fallback.
    """
    v = (verdict or "").upper()
    if v == "BLOCK":
        return 1
    if v == "WARN":
        return 3
    return 6


@dataclass(frozen=True)
class MemoryAtom:
    kind: str
    version: str

    verdict: str
    dna: str
    dna_key: str

    band: int  # 1..7 (1 hottest)
    baseline: Dict[str, Any]
    metrics: Dict[str, Any]

    # Optional context (NOT hashed; safe to include for debugging)
    context: Dict[str, Any]

    atom_id: str

    @staticmethod
    def compute_atom_id(
        kind: str,
        version: str,
        verdict: str,
        dna_key: str,
        band: int,
        baseline: Dict[str, Any],
        metrics: Dict[str, Any],
    ) -> str:
        """
        Deterministic ID:
        - No timestamps
        - No repo/ref (context)
        - Hash only structural invariants.
        """
        # Only keep stable baseline fields if present (avoid accidental noise)
        bl = {
            "mu": baseline.get("mu"),
            "sigma": baseline.get("sigma"),
            "warn_threshold": baseline.get("warn_threshold"),
            "block_threshold": baseline.get("block_threshold"),
        }
        # Keep a small stable metrics subset if present
        mt = {
            "risk": metrics.get("risk", metrics.get("last_risk")),
            "specH": metrics.get("specH"),
            "cusum": metrics.get("cusum"),
        }

        payload = {
            "kind": kind,
            "version": version,
            "verdict": (verdict or "").upper(),
            "dna_key": dna_key,
            "band": int(band),
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
    ) -> "MemoryAtom":
        """
        Build a MemoryAtom from a GitCube/HFS report JSON.
        """
        kind = str(report.get("kind") or "NAVIGATOR_REPORT")
        version = str(report.get("version") or "0.2")

        verdict = str(report.get("verdict") or "ALLOW").upper()
        dna = str(report.get("dna") or "")
        dna_key = normalize_dna_key(dna, key_len=key_len)

        baseline = report.get("baseline") or {}
        metrics = {}

        # Support both styles:
        # - HFS demo: baseline.last_risk + metrics_last_window.risk (or similar)
        # - GitCube: may have metrics dict directly
        if "metrics" in report and isinstance(report["metrics"], dict):
            metrics = dict(report["metrics"])
        elif "metrics_last_window" in report and isinstance(report["metrics_last_window"], dict):
            metrics = dict(report["metrics_last_window"])

        # Add a unified risk field
        if "risk" not in metrics:
            if isinstance(baseline, dict) and ("last_risk" in baseline):
                metrics["risk"] = baseline.get("last_risk")
            else:
                metrics["risk"] = report.get("risk")

        band = report.get("band")
        if band is None:
            band = _band_from_verdict(verdict)
        band = int(band)
        if band < 1:
            band = 1
        if band > 7:
            band = 7

        context: Dict[str, Any] = {}
        if repo:
            context["repo"] = repo
        if ref:
            context["ref"] = ref
        if note:
            context["note"] = note

        atom_id = cls.compute_atom_id(
            kind=kind,
            version=version,
            verdict=verdict,
            dna_key=dna_key,
            band=band,
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
            baseline=baseline,
            metrics=metrics,
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
            "baseline": self.baseline,
            "metrics": self.metrics,
            "context": self.context,
        }
