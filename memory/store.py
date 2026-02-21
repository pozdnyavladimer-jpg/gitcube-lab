# -*- coding: utf-8 -*-
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
    def __init__(self, path: str = "memory/memory.jsonl"):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    # -------------------------
    # IO
    # -------------------------
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
                    # skip corrupted lines instead of dying
                    continue
        return rows

    def _write_all(self, rows: List[Dict[str, Any]]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # -------------------------
    # Merge / Upsert
    # -------------------------
    def append(self, atom: MemoryAtom) -> MemoryAtom:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(atom.to_dict(), ensure_ascii=False) + "\n")
        return atom

    def upsert(self, atom: MemoryAtom) -> MemoryAtom:
        """
        Merge by atom_id:
          - strength += 1
          - last_seen = now
          - keep first_seen minimal (oldest)
          - context: keep existing, fill missing keys from new
        """
        now = time.time()
        rows = self._read_all()

        idx = None
        for i, r in enumerate(rows):
            if str(r.get("atom_id", "")) == atom.atom_id:
                idx = i
                break

        if idx is None:
            # brand new
            a = atom
            # ensure timestamps exist
            d = a.to_dict()
            d["strength"] = int(d.get("strength", 1) or 1)
            d["first_seen"] = float(d.get("first_seen", now) or now)
            d["last_seen"] = float(d.get("last_seen", now) or now)
            rows.append(d)
            self._write_all(rows)
            return MemoryAtom.from_dict(d)

        # merge existing
        r = rows[idx]
        strength = int(r.get("strength", 1) or 1) + 1

        first_seen = float(r.get("first_seen", now) or now)
        last_seen = now

        # context merge: keep old, fill missing with new
        old_ctx = r.get("context") if isinstance(r.get("context"), dict) else {}
        new_ctx = atom.context if isinstance(atom.context, dict) else {}
        merged_ctx = dict(old_ctx)
        for k, v in new_ctx.items():
            if k not in merged_ctx:
                merged_ctx[k] = v

        r["strength"] = strength
        r["first_seen"] = first_seen
        r["last_seen"] = last_seen
        r["context"] = merged_ctx

        # Optional: refresh volatile fields if you want (safe defaults: keep old)
        # r["metrics"] = atom.metrics
        # r["baseline"] = atom.baseline

        rows[idx] = r
        self._write_all(rows)
        return MemoryAtom.from_dict(r)

    # -------------------------
    # Query / Stats
    # -------------------------
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
            if q.phase_state is not None and int(r.get("phase_state", -1) or -1) != int(q.phase_state):
                return False
            if q.kind and str(r.get("kind", "")) != str(q.kind):
                return False
            if q.dna_key and str(r.get("dna_key", "")) != str(q.dna_key):
                return False
            if q.dna_contains and str(q.dna_contains) not in str(r.get("dna", "")):
                return False
            if q.min_strength is not None and int(r.get("strength", 1) or 1) < int(q.min_strength):
                return False
            return True

        out = [r for r in rows if ok(r)]
        out.sort(key=lambda r: (int(r.get("strength", 1) or 1), float(r.get("last_seen", 0.0) or 0.0)), reverse=True)
        return out[: int(q.limit or 50)]

    def stats(self) -> Dict[str, Any]:
        rows = self._read_all()
        if not rows:
            return {"count": 0, "strength_sum": 0, "strength_max": 0}
        strengths = [int(r.get("strength", 1) or 1) for r in rows]
        return {"count": len(rows), "strength_sum": sum(strengths), "strength_max": max(strengths)}
