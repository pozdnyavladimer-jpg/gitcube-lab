# -*- coding: utf-8 -*-
"""
Topological Memory Atom (network-ready)
License: AGPL-3.0
Author: Володимир Поздняк

Goal:
- Build a compact, verifiable "Memory Atom" from a report.json
- Generate a stable cryptographic atom_id (sha256) from canonical content
- Keep schema versioned for future federation
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import hashlib
import json
import time


ATOM_SCHEMA_VERSION = "0.2"  # bump when canonical fields change


def _canon(obj: Any) -> Any:
    """
    Canonicalize objects so that hashing is stable:
    - dict keys sorted
    - floats rounded to stable precision
    """
    if isinstance(obj, dict):
        return {k: _canon(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_canon(x) for x in obj]
    if isinstance(obj, float):
        # stable rounding (avoid tiny float differences)
        return round(obj, 8)
    return obj


def canonical_json(obj: Any) -> str:
    """
    Deterministic JSON string for hashing.
    """
    return json.dumps(_canon(obj), ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def safe_get(d: Dict[str, Any], path: str, default=None):
    """
    safe_get(report, "baseline.warn_threshold")
    """
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part, default)
    return cur


@dataclass
class MemoryAtom:
    schema: str
    created_ts: float

    # identity / reference (not part of id hash by default)
    repo: str
    ref: str  # e.g. PR#12, commit sha, session id

    # core decision
    kind: str            # e.g. "HFS_NAVIGATOR_REPORT" / "GITCUBE_REPORT"
    version: str         # report version
    verdict: str         # ALLOW/WARN/BLOCK
    dna: str             # compact signature

    # thresholds (baseline)
    mu: float
    sigma: float
    warn_threshold: float
    block_threshold: float
    last_risk: float

    # energy band 1..7 (optional)
    band: Optional[int] = None

    # wave fields (optional)
    specH: Optional[float] = None
    cusum_drift: Optional[bool] = None

    # hash id
    atom_id: str = ""

    def core_for_hash(self) -> Dict[str, Any]:
        """
        Only include fields that define the structural truth.
        Exclude repo/ref/created_ts to make atoms comparable across nodes.
        """
        return {
            "schema": self.schema,
            "kind": self.kind,
            "version": self.version,
            "verdict": self.verdict,
            "dna": self.dna,
            "baseline": {
                "mu": self.mu,
                "sigma": self.sigma,
                "warn_threshold": self.warn_threshold,
                "block_threshold": self.block_threshold,
                "last_risk": self.last_risk,
            },
            "band": self.band,
            "wave": {
                "specH": self.specH,
                "cusum_drift": self.cusum_drift,
            },
        }

    def finalize_id(self) -> None:
        self.atom_id = sha256_hex(canonical_json(self.core_for_hash()))


def _derive_band(verdict: str, last_risk: float, warn: float, block: float) -> Optional[int]:
    """
    Simple 1..7 "energy band" heuristic.
    1 = hottest / highest risk, 7 = calm / low risk.
    """
    try:
        if verdict == "BLOCK":
            return 1
        if verdict == "WARN":
            # map how close to block
            if block <= 1e-9:
                return 3
            x = clamp((last_risk - warn) / max(1e-9, (block - warn)), 0.0, 1.0)
            return 3 if x < 0.5 else 2
        # ALLOW: map how far below warn
        if warn <= 1e-9:
            return 7
        x = clamp(last_risk / warn, 0.0, 1.0)
        return 7 if x < 0.35 else 6 if x < 0.60 else 5
    except Exception:
        return None


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def atom_from_report(report: Dict[str, Any], repo: str, ref: str) -> MemoryAtom:
    """
    Supports HFS reports and (optionally) GitCube reports,
    as long as they provide verdict/dna/baseline thresholds.

    Expected minimal fields:
      - kind, version, verdict
      - dna (or "dna" in a different key can be mapped)
      - baseline: mu, sigma, warn_threshold, block_threshold, last_risk
    """

    kind = str(report.get("kind", "UNKNOWN_REPORT"))
    version = str(report.get("version", "unknown"))

    verdict = str(report.get("verdict", "UNKNOWN"))
    dna = str(report.get("dna", report.get("structural_dna", "N/A")))

    # baseline layout (HFS v0.2-wave: baseline holds these keys)
    mu = float(safe_get(report, "baseline.mu", 0.0) or 0.0)
    sigma = float(safe_get(report, "baseline.sigma", 0.0) or 0.0)
    warn = float(safe_get(report, "baseline.warn_threshold", 0.0) or 0.0)
    block = float(safe_get(report, "baseline.block_threshold", 0.0) or 0.0)
    last_risk = float(safe_get(report, "baseline.last_risk", 0.0) or 0.0)

    # wave fields: from metrics_last_window.spectral_entropy or direct
    specH = safe_get(report, "metrics_last_window.spectral_entropy", None)
    if specH is None:
        specH = safe_get(report, "specH", None)
    if specH is not None:
        specH = float(specH)

    cusum = safe_get(report, "baseline.cusum_drift", None)
    if cusum is None:
        cusum = safe_get(report, "cusum_drift", None)
    if cusum is not None:
        cusum = bool(cusum)

    # derive band if not present
    band = report.get("band", None)
    if band is None:
        band = _derive_band(verdict, last_risk, warn, block)
    if band is not None:
        band = int(band)

    atom = MemoryAtom(
        schema=ATOM_SCHEMA_VERSION,
        created_ts=time.time(),
        repo=str(repo),
        ref=str(ref),
        kind=kind,
        version=version,
        verdict=verdict,
        dna=dna,
        mu=mu,
        sigma=sigma,
        warn_threshold=warn,
        block_threshold=block,
        last_risk=last_risk,
        band=band,
        specH=specH,
        cusum_drift=cusum,
        atom_id="",
    )
    atom.finalize_id()
    return atom


def atom_to_json(atom: MemoryAtom) -> str:
    return json.dumps(_canon(asdict(atom)), ensure_ascii=False)


def atom_to_dict(atom: MemoryAtom) -> Dict[str, Any]:
    return _canon(asdict(atom))
