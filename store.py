# -*- coding: utf-8 -*-
"""Append-only Memory Store (JSONL).

Why JSONL:
- easy diff
- append-only (audit-friendly)
- streamable

File format: one MemoryAtom dict per line.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional

from .atom import MemoryAtom


@dataclass
class Query:
    verdict: Optional[str] = None  # ALLOW/WARN/BLOCK
    band_min: Optional[int] = None
    band_max: Optional[int] = None
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
        out: List[Dict[str, Any]] = []
        for a in self.iter_atoms():
            if q.kind and a.get("kind") != q.kind:
                continue
            if q.verdict and a.get("verdict") != q.verdict:
                continue
            band = int(a.get("band", 0) or 0)
            if q.band_min is not None and band < q.band_min:
                continue
            if q.band_max is not None and band > q.band_max:
                continue
            if q.dna_contains and q.dna_contains not in (a.get("dna") or ""):
                continue
            out.append(a)
            if len(out) >= max(1, int(q.limit)):
                break
        return out
