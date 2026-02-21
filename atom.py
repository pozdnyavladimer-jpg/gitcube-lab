# -*- coding: utf-8 -*-
"""Topological Memory Atom.

A Memory Atom is a compact, append-only record of a structural event.
It stores *invariants*, not raw text.

Designed to be:
- explainable
- JSON-serializable
- safe for CI use

Works with both:
- GitCube structural DNA reports (C L D S H E P M)
- HFS navigator reports (T R P S C F W M)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import time


@dataclass
class MemoryAtom:
    # core identity
    t: float
    kind: str  # e.g. "GITCUBE_STRUCT" or "HFS_NAVIGATOR"

    # discrete crystallization
    verdict: str  # ALLOW | WARN | BLOCK
    dna: str
    band: int  # 1..7 energy band

    # continuous internals
    risk: float
    mu: float
    sigma: float
    warn_threshold: float
    block_threshold: float

    # optional anchors
    repo: Optional[str] = None
    ref: Optional[str] = None  # commit sha / PR id / session id
    note: Optional[str] = None

    # compact payload
    metrics: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # keep json small
        if d.get("metrics") is None:
            d.pop("metrics", None)
        if d.get("note") is None:
            d.pop("note", None)
        if d.get("repo") is None:
            d.pop("repo", None)
        if d.get("ref") is None:
            d.pop("ref", None)
        return d


def now_ts() -> float:
    return float(time.time())
