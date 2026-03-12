# -*- coding: utf-8 -*-
"""Swarm schema for Agent Runtime v0.1.

Minimal typed contracts for:
- incoming task
- runtime state
- partial agent results
- final orchestrator output
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Task:
    kind: str
    intent: str
    context: str
    payload: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Task":
        return cls(
            kind=str(d.get("kind") or "AGENT_TASK"),
            intent=str(d.get("intent") or "unknown"),
            context=str(d.get("context") or "general"),
            payload=d.get("payload") if isinstance(d.get("payload"), dict) else {},
            constraints=d.get("constraints") if isinstance(d.get("constraints"), dict) else {},
            meta=d.get("meta") if isinstance(d.get("meta"), dict) else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "intent": self.intent,
            "context": self.context,
            "payload": self.payload,
            "constraints": self.constraints,
            "meta": self.meta,
        }


@dataclass
class SwarmState:
    mode: str = "DIRECT"
    verdict: str = "ALLOW"
    risk: float = 0.0
    score: float = 1.0
    dna: str = ""
    dna_key: str = ""
    band: int = 7
    shrink_factor: float = 1.0
    memory_hits: int = 0
    crystal_key: str = ""
    meta_control: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "verdict": self.verdict,
            "risk": self.risk,
            "score": self.score,
            "dna": self.dna,
            "dna_key": self.dna_key,
            "band": self.band,
            "shrink_factor": self.shrink_factor,
            "memory_hits": self.memory_hits,
            "crystal_key": self.crystal_key,
            "meta_control": self.meta_control,
        }


@dataclass
class PartialResult:
    role: str
    status: str = "ok"
    data: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "status": self.status,
            "data": self.data,
            "notes": self.notes,
        }


@dataclass
class FinalResult:
    task_id: Optional[str]
    mode: str
    verdict: str
    recommended_action: str
    confidence: float
    state: Dict[str, Any] = field(default_factory=dict)
    organs: List[Dict[str, Any]] = field(default_factory=list)
    partials: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "mode": self.mode,
            "verdict": self.verdict,
            "recommended_action": self.recommended_action,
            "confidence": self.confidence,
            "state": self.state,
            "organs": self.organs,
            "partials": self.partials,
            "notes": self.notes,
        }
