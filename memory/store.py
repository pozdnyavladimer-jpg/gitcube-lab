# -*- coding: utf-8 -*-
"""
JSONL Memory Store
- upsert (merge) by atom_id: strength++, last_seen updated
- query with filters, sorting by strength then last_seen
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .atom import MemoryAtom


@dataclass
class Query:
    verdict: Optional[str] = None
    band_min: Optional[int] = None
    band_max: Optional[int] = None
    phase_state: Optional[int] = None
    dna_contains: Optional[str] = None
    dna_key: Optional[str] = None
    kind: Optional[str] = None
    min_strength: Optional[int] = None
    limit: int = 50


class MemoryStore:
    def __init__(self, path: str):
        self.path = path

    def _ensure_parent(self) -> None:
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _read_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        rows: List[Dict[str, Any]] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    # ignore bad lines (or you can raise)
                    continue
        return rows

    def _write_all(self, rows: List[Dict[str, Any]]) -> None:
        self._ensure_parent()
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, self.path)

    def upsert(self, atom: MemoryAtom) -> MemoryAtom:
        """
        Merge policy:
        - If atom_id exists: strength += 1, last_seen updated
        - Otherwise: append as new (strength=1)
        """
        rows = self._read_all()
        now = time.time()

        for i, r in enumerate(rows):
            if str(r.get("atom_id", "")) == atom.atom_id:
                # merge
                strength = int(r.get("strength", 1)) + 1
                r["strength"] = strength
                r["last_seen"] = now
                # optionally keep newest metrics/baseline snapshot
                r["metrics"] = atom.metrics
                r["baseline"] = atom.baseline
                # keep context union (never overwrite existing keys unless new gives it)
                ctx = r.get("context") if isinstance(r.get("context"), dict) else {}
                for k, v in atom.context.items():
                    ctx.setdefault(k, v)
                r["context"] = ctx
                rows[i] = r
                self._write_all(rows)
                return MemoryAtom.from_dict(r)

        # not found: insert new
        d = atom.to_dict()
        d["strength"] = int(d.get("strength", 1))
        d["first_seen"] = float(d.get("first_seen", now))
        d["last_seen"] = float(d.get("last_seen", now))
        rows.append(d)
        self._write_all(rows)
        return atom

    def append(self, atom: MemoryAtom) -> None:
        """
        Legacy: raw append (no merge).
        Prefer upsert().
        """
        self._ensure_parent()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(atom.to_dict(), ensure_ascii=False) + "\n")

    def query(self, q: Query) -> List[Dict[str, Any]]:
        rows = self._read_all()

        def ok(r: Dict[str, Any]) -> bool:
            if q.verdict and str(r.get("verdict", "")).upper() != str(q.verdict).upper():
                return False
            band = int(r.get("band", 0) or 0)
            if q.band_min is not None and band < int(q.band_min):
                return False
            if q.band_max is not None and band > int(q.band_max):
                return False
            if q.phase_state is not None and int(r.get("phase_state", -1)) != int(q.phase_state):
                return False
            if q.kind and str(r.get("kind", "")) != str(q.kind):
                return False
            if q.dna_key and str(r.get("dna_key", "")) != str(q.dna_key):
                return False
            if q.dna_contains and (str(q.dna_contains) not in str(r.get("dna", ""))):
                return False
            if q.min_strength is not None and int(r.get("strength", 1)) < int(q.min_strength):
                return False
            return True

        out = [r for r in rows if ok(r)]

        # sort: strongest first, then newest
        out.sort(
            key=lambda r: (
                int(r.get("strength", 1)),
                float(r.get("last_seen", 0.0)),
            ),
            reverse=True,
        )

        return out[: int(q.limit)]

    def stats(self) -> Dict[str, Any]:
        rows = self._read_all()
        if not rows:
            return {"count": 0}
        strengths = [int(r.get("strength", 1)) for r in rows]
        return {
            "count": len(rows),
            "strength_sum": sum(strengths),
            "strength_max": max(strengths),
        }
