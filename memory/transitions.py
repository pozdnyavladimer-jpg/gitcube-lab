# memory/transitions.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class TransitionRecord:
    ts: float
    task_id: str
    action: str
    from_dna: str
    from_phase_state: int
    from_risk: float
    from_verdict: str
    to_dna: str
    to_phase_state: int
    to_risk: float
    to_verdict: str
    risk_delta: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ts": self.ts,
            "task_id": self.task_id,
            "action": self.action,
            "from_dna": self.from_dna,
            "from_phase_state": self.from_phase_state,
            "from_risk": self.from_risk,
            "from_verdict": self.from_verdict,
            "to_dna": self.to_dna,
            "to_phase_state": self.to_phase_state,
            "to_risk": self.to_risk,
            "to_verdict": self.to_verdict,
            "risk_delta": self.risk_delta,
        }


class TransitionStore:
    def __init__(self, path: str = "memory/transitions.jsonl") -> None:
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def append(self, rec: TransitionRecord) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")

    def load_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        out: List[Dict[str, Any]] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
        return out


def build_transition(
    *,
    task_id: str,
    action: str,
    from_report: Dict[str, Any],
    to_report: Dict[str, Any],
) -> TransitionRecord:
    return TransitionRecord(
        ts=time.time(),
        task_id=str(task_id),
        action=str(action),
        from_dna=str(from_report.get("dna", "")),
        from_phase_state=int(from_report.get("phase_state", 0) or 0),
        from_risk=float(from_report.get("risk", 1.0) or 1.0),
        from_verdict=str(from_report.get("verdict", "")),
        to_dna=str(to_report.get("dna", "")),
        to_phase_state=int(to_report.get("phase_state", 0) or 0),
        to_risk=float(to_report.get("risk", 1.0) or 1.0),
        to_verdict=str(to_report.get("verdict", "")),
        risk_delta=float(to_report.get("risk", 1.0) or 1.0) - float(from_report.get("risk", 1.0) or 1.0),
    )
