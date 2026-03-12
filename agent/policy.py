# -*- coding: utf-8 -*-
"""Execution policy for Swarm v0.1.

Uses:
- structural verdict / risk from GraphEval or HFS report
- memory meta-control shrink factor
- number of memory matches

Returns one of:
- DIRECT
- CAUTIOUS
- SANDBOXED
- BLOCKED
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from memory.meta import meta_shrink_factor


@dataclass
class PolicyDecision:
    mode: str
    adjusted_risk: float
    shrink_factor: float
    memory_hits: int
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "adjusted_risk": self.adjusted_risk,
            "shrink_factor": self.shrink_factor,
            "memory_hits": self.memory_hits,
            "reason": self.reason,
        }


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def choose_execution_mode(
    *,
    verdict: str,
    risk: float,
    shrink_factor: float,
    memory_hits: int,
) -> str:
    """
    Simple v0.1 policy:
    - BLOCK verdict always => BLOCKED
    - higher adjusted risk => stricter mode
    """
    verdict = str(verdict or "ALLOW").upper()
    risk = _clamp01(float(risk or 0.0))
    shrink_factor = float(shrink_factor or 1.0)
    memory_hits = int(memory_hits or 0)

    adjusted_risk = risk / max(0.65, shrink_factor)

    if verdict == "BLOCK":
        return "BLOCKED"
    if adjusted_risk >= 0.85:
        return "BLOCKED"
    if adjusted_risk >= 0.65 or memory_hits >= 3:
        return "SANDBOXED"
    if adjusted_risk >= 0.40 or memory_hits >= 1 or verdict == "WARN":
        return "CAUTIOUS"
    return "DIRECT"


def decide_policy(
    *,
    report: Dict[str, Any],
    store_path: Optional[str] = None,
    kind: Optional[str] = None,
    lookback: int = 200,
) -> PolicyDecision:
    """
    report is expected to contain at least:
      verdict, risk, dna, dna_key?, kind?
    """
    verdict = str(report.get("verdict") or "ALLOW").upper()
    risk = float(report.get("risk") or 0.0)

    dna_key = str(report.get("dna_key") or "").strip()
    kind = kind or str(report.get("kind") or "")

    shrink = 1.0
    matches = 0
    reason = "no memory effect"

    if store_path and dna_key:
        md = meta_shrink_factor(
            store_path=store_path,
            dna_key=dna_key,
            kind=kind or None,
            lookback=lookback,
        )
        shrink = float(md.shrink)
        matches = int(md.matches)
        reason = (
            f"memory-aware policy: matches={md.matches}, "
            f"block_rate={round(md.block_rate, 3)}, "
            f"hot_avg={round(md.hot_avg, 3)}, "
            f"reflex={round(md.reflex, 3)}"
        )

    adjusted_risk = _clamp01(risk / max(0.65, shrink))
    mode = choose_execution_mode(
        verdict=verdict,
        risk=risk,
        shrink_factor=shrink,
        memory_hits=matches,
    )

    if verdict == "BLOCK":
        reason = "structural verdict is BLOCK"
    elif mode == "SANDBOXED":
        reason = f"high adjusted risk or repeated hazardous memory ({reason})"
    elif mode == "CAUTIOUS":
        reason = f"moderate risk or weak memory warning ({reason})"
    elif mode == "DIRECT":
        reason = f"stable path ({reason})"

    return PolicyDecision(
        mode=mode,
        adjusted_risk=adjusted_risk,
        shrink_factor=shrink,
        memory_hits=matches,
        reason=reason,
    )
