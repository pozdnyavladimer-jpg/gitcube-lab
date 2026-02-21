# -*- coding: utf-8 -*-
"""
Append-only Memory Store (JSONL) — v0.2

Key properties:
- append-only JSONL (audit-friendly)
- query returns the most recent matches (tail), not the earliest ones
- supports exact dna_key lookup (indexed-style query)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from collections import deque
from typing import Any, Dict, Iterator, List, Optional

from .atom import MemoryAtom


@dataclass
class Query:
    verdict: Optional[str] = None  # ALLOW/WARN/BLOCK
    band_min: Optional[int] = None
    band_max: Optional[int] = None

    # exact match (preferred in v0.2)
    dna_key: Optional[str] = None

    # legacy substring fallback (optional; keep for migration)
    dna_contains: Optional[str] = None

    kind: Optional[str] = None
    limit: int = 50


class MemoryStore:
    def __init__(self, path: str) -> None:
        self.path = path

    def append(self, atom: MemoryAtom) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(atom.to_dict(), ensure_ascii=False) + "\n")

    def iter_atoms(self) -> Iterator[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return iter(())
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    # skip corrupted lines
                    continue

    def query(self, q: Query) -> List[Dict[str, Any]]:
        """
        Returns MOST RECENT matches (tail), up to limit.
        """
        lim = max(1, int(q.limit))
        buf = deque(maxlen=lim)

        for a in self.iter_atoms():
            if q.kind and a.get("kind") != q.kind:
                continue

            if q.verdict and str(a.get("verdict") or "").upper() != str(q.verdict).upper():
                continue

            band = int(a.get("band", 0) or 0)
            if q.band_min is not None and band < int(q.band_min):
                continue
            if q.band_max is not None and band > int(q.band_max):
                continue

            if q.dna_key:
                if (a.get("dna_key") or "") != q.dna_key:
                    continue
            elif q.dna_contains:
                if q.dna_contains not in (a.get("dna") or ""):
                    continue

            buf.append(a)

        # Return in chronological order among the tail
        return list(buf)
