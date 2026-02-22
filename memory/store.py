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
    crystal_key: Optional[str] = None
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
                    continue
        return rows

    def _write_all(self, rows: List[Dict[str, Any]]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # -------------------------
    # Append / Upsert
    # -------------------------
    def append(self, atom: MemoryAtom) -> MemoryAtom:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(atom.to_dict(), ensure_ascii=False) + "\n")
        return atom

    def upsert(self, atom: MemoryAtom) -> MemoryAtom:
        """
        Merge by crystal_key (NOT atom_id):
          - strength += 1
          - last_seen = now
          - keep first_seen minimal (oldest)
          - context: keep existing, fill missing keys from new
          - keep last snapshot atom_id
          - accumulate flower area:
              flower.area_sum += petal_area
              flower.area_max = max(area_max, petal_area)
        """
        now = time.time()
        rows = self._read_all()

        ck = str(getattr(atom, "crystal_key", "") or "").strip()
        if not ck:
            ck = f"{atom.kind}::(no_dna)"

        idx = None
        for i, r in enumerate(rows):
            if str(r.get("crystal_key", "")).strip() == ck:
                idx = i
                break

        petal_area = 0.0
        if isinstance(atom.flower, dict):
            try:
                petal_area = float(atom.flower.get("petal_area", 0.0) or 0.0)
            except Exception:
                petal_area = 0.0

        if idx is None:
            d = atom.to_dict()
            d["crystal_key"] = ck
            d["strength"] = int(d.get("strength", 1) or 1)
            d["first_seen"] = float(d.get("first_seen", now) or now)
            d["last_seen"] = float(d.get("last_seen", now) or now)

            # init flower accumulators
            fl = d.get("flower") if isinstance(d.get("flower"), dict) else {}
            fl.setdefault("petal_area", petal_area)
            fl["area_sum"] = float(petal_area)
            fl["area_max"] = float(petal_area)
            d["flower"] = fl

            rows.append(d)
            self._write_all(rows)
            return MemoryAtom.from_dict(d)

        # merge existing
        r = rows[idx]
        r["crystal_key"] = ck

        r["strength"] = int(r.get("strength", 1) or 1) + 1
        r["first_seen"] = float(r.get("first_seen", now) or now)
        r["last_seen"] = now

        # keep latest snapshot id + some fresh fields
        r["atom_id"] = atom.atom_id
        r["verdict"] = atom.verdict
        r["band"] = atom.band
        r["phase_dir"] = atom.phase_dir
        r["phase_state"] = atom.phase_state
        r["dna"] = atom.dna
        r["dna_key"] = atom.dna_key
        r["kind"] = atom.kind
        r["version"] = atom.version

        # context merge
        old_ctx = r.get("context") if isinstance(r.get("context"), dict) else {}
        new_ctx = atom.context if isinstance(atom.context, dict) else {}
        merged_ctx = dict(old_ctx)
        for k, v in new_ctx.items():
            if k not in merged_ctx:
                merged_ctx[k] = v
        r["context"] = merged_ctx

        # (optional) refresh metrics/baseline to latest snapshot
        r["metrics"] = atom.metrics
        r["baseline"] = atom.baseline

        # flower accumulation
        fl = r.get("flower") if isinstance(r.get("flower"), dict) else {}
        area_sum = float(fl.get("area_sum", 0.0) or 0.0) + float(petal_area)
        area_max = max(float(fl.get("area_max", 0.0) or 0.0), float(petal_area))
        fl["petal_area"] = float(petal_area)
        fl["area_sum"] = float(area_sum)
        fl["area_max"] = float(area_max)
        if isinstance(atom.flower, dict) and "points" in atom.flower:
            fl["points"] = atom.flower["points"]
        r["flower"] = fl

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
            if q.crystal_key and str(r.get("crystal_key", "")) != str(q.crystal_key):
                return False
            if q.dna_contains and str(q.dna_contains) not in str(r.get("dna", "")):
                return False
            if q.min_strength is not None and int(r.get("strength", 1) or 1) < int(q.min_strength):
                return False
            return True

        out = [r for r in rows if ok(r)]
        out.sort(
            key=lambda r: (
                int(r.get("strength", 1) or 1),
                float((r.get("flower") or {}).get("area_sum", 0.0) or 0.0),
                float(r.get("last_seen", 0.0) or 0.0),
            ),
            reverse=True,
        )
        return out[: int(q.limit or 50)]

    def stats(self) -> Dict[str, Any]:
        rows = self._read_all()
        if not rows:
            return {"count": 0, "strength_sum": 0, "strength_max": 0, "flower_area_sum": 0.0, "flower_area_max": 0.0}

        strengths = [int(r.get("strength", 1) or 1) for r in rows]
        area_sums = []
        area_maxs = []
        for r in rows:
            fl = r.get("flower") if isinstance(r.get("flower"), dict) else {}
            area_sums.append(float(fl.get("area_sum", 0.0) or 0.0))
            area_maxs.append(float(fl.get("area_max", 0.0) or 0.0))

        return {
            "count": len(rows),
            "strength_sum": sum(strengths),
            "strength_max": max(strengths),
            "flower_area_sum": float(sum(area_sums)),
            "flower_area_max": float(max(area_maxs) if area_maxs else 0.0),
        }
