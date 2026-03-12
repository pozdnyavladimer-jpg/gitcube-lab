# -*- coding: utf-8 -*-
"""Functional organ blocks for Swarm v0.1.

Idea:
- OrganBlock = stable functional unit
- orchestrator selects organs first
- organs activate one or more runtime roles
- roles are still simple in v0.1 (no heavy ML)

This is a control abstraction, not biology.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass(frozen=True)
class OrganBlock:
    organ_id: str
    name: str
    purpose: str
    required_roles: List[str] = field(default_factory=list)
    allowed_modes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------
# Built-in organs
# ---------------------------------------------------------

ORG_EXPLORE = OrganBlock(
    organ_id="ORG_EXPLORE",
    name="Explore",
    purpose="Generate candidate options / branches.",
    required_roles=["scout"],
    allowed_modes=["DIRECT", "CAUTIOUS", "SANDBOXED"],
    tags=["search", "options", "discovery"],
)

ORG_SIMULATE = OrganBlock(
    organ_id="ORG_SIMULATE",
    name="Simulate",
    purpose="Run hypothetical scenarios before action.",
    required_roles=["simulator"],
    allowed_modes=["SANDBOXED"],
    tags=["simulation", "future", "branching"],
)

ORG_CRITIQUE = OrganBlock(
    organ_id="ORG_CRITIQUE",
    name="Critique",
    purpose="Find weak points, contradictions, rule violations, and failure paths.",
    required_roles=["critic"],
    allowed_modes=["CAUTIOUS", "SANDBOXED"],
    tags=["risk", "failure", "critique"],
)

ORG_RECALL = OrganBlock(
    organ_id="ORG_RECALL",
    name="Recall",
    purpose="Query structural memory and retrieve relevant prior atoms.",
    required_roles=["memory_agent"],
    allowed_modes=["CAUTIOUS", "SANDBOXED"],
    tags=["memory", "history", "patterns"],
)

ORG_SYNTHESIZE = OrganBlock(
    organ_id="ORG_SYNTHESIZE",
    name="Synthesize",
    purpose="Assemble final answer / recommendation from partial results.",
    required_roles=["builder"],
    allowed_modes=["DIRECT", "CAUTIOUS", "SANDBOXED"],
    tags=["fusion", "summary", "result"],
)

ORG_VALIDATE = OrganBlock(
    organ_id="ORG_VALIDATE",
    name="Validate",
    purpose="Cross-check consistency before final recommendation.",
    required_roles=["critic", "builder"],
    allowed_modes=["CAUTIOUS", "SANDBOXED"],
    tags=["validation", "consistency"],
)

ORG_SANDBOX = OrganBlock(
    organ_id="ORG_SANDBOX",
    name="Sandbox",
    purpose="Force isolated execution / simulation-only exploration.",
    required_roles=["simulator", "critic", "memory_agent"],
    allowed_modes=["SANDBOXED"],
    tags=["isolation", "sandbox", "safe-mode"],
)

ORG_ROUTE = OrganBlock(
    organ_id="ORG_ROUTE",
    name="Route",
    purpose="Choose branch priority / execution route.",
    required_roles=["scout", "critic"],
    allowed_modes=["DIRECT", "CAUTIOUS", "SANDBOXED"],
    tags=["routing", "priority", "selection"],
)


ORGANS: Dict[str, OrganBlock] = {
    org.organ_id: org
    for org in [
        ORG_EXPLORE,
        ORG_SIMULATE,
        ORG_CRITIQUE,
        ORG_RECALL,
        ORG_SYNTHESIZE,
        ORG_VALIDATE,
        ORG_SANDBOX,
        ORG_ROUTE,
    ]
}


# ---------------------------------------------------------
# Selection logic
# ---------------------------------------------------------

def organ_ids_for_mode(mode: str) -> List[str]:
    mode = (mode or "").upper()

    if mode == "DIRECT":
        return [
            "ORG_EXPLORE",
            "ORG_SYNTHESIZE",
        ]

    if mode == "CAUTIOUS":
        return [
            "ORG_EXPLORE",
            "ORG_CRITIQUE",
            "ORG_RECALL",
            "ORG_SYNTHESIZE",
            "ORG_VALIDATE",
        ]

    if mode == "SANDBOXED":
        return [
            "ORG_EXPLORE",
            "ORG_SIMULATE",
            "ORG_CRITIQUE",
            "ORG_RECALL",
            "ORG_SYNTHESIZE",
            "ORG_VALIDATE",
            "ORG_SANDBOX",
            "ORG_ROUTE",
        ]

    if mode == "BLOCKED":
        return []

    return []


def refine_organs_for_task(intent: str, context: str, organ_ids: List[str]) -> List[str]:
    """Small task-aware refinement.

    v0.1 intentionally stays simple.
    """
    intent = (intent or "").lower()
    context = (context or "").lower()

    selected: Set[str] = set(organ_ids)

    # Graph / code / architecture tasks benefit from critique + recall
    if any(k in intent for k in ["graph", "refactor", "architecture", "feedback", "topology", "score"]):
        selected.add("ORG_CRITIQUE")
        selected.add("ORG_RECALL")
        selected.add("ORG_VALIDATE")

    if context in {"code", "repo", "graph", "architecture"}:
        selected.add("ORG_CRITIQUE")
        selected.add("ORG_RECALL")

    # Search / planning / strategy tasks benefit from routing
    if any(k in intent for k in ["search", "plan", "route", "strategy", "analyze_position"]):
        selected.add("ORG_ROUTE")

    # Sandbox isolation keeps all sandbox organs
    return [oid for oid in ORGANS.keys() if oid in selected]


def select_organs(intent: str, context: str, mode: str) -> List[OrganBlock]:
    base_ids = organ_ids_for_mode(mode)
    final_ids = refine_organs_for_task(intent, context, base_ids)
    return [ORGANS[oid] for oid in final_ids if oid in ORGANS]


def required_roles_from_organs(organs: List[OrganBlock]) -> List[str]:
    seen: Set[str] = set()
    roles: List[str] = []

    for organ in organs:
        for role in organ.required_roles:
            if role not in seen:
                seen.add(role)
                roles.append(role)

    return roles


def describe_organs(organs: List[OrganBlock]) -> List[dict]:
    return [
        {
            "organ_id": organ.organ_id,
            "name": organ.name,
            "purpose": organ.purpose,
            "required_roles": organ.required_roles,
            "allowed_modes": organ.allowed_modes,
            "tags": organ.tags,
        }
        for organ in organs
    ]
