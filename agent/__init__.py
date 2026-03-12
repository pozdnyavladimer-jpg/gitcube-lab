# -*- coding: utf-8 -*-
"""Agent Runtime package for GitCube Lab.

Swarm v0.1:
- schema   : typed task / state / result contracts
- policy   : execution mode selection
- organs   : functional blocks for orchestrator
"""

from .schema import Task, SwarmState, PartialResult, FinalResult
from .policy import PolicyDecision, decide_policy, choose_execution_mode
from .organs import (
    OrganBlock,
    ORG_EXPLORE,
    ORG_SIMULATE,
    ORG_CRITIQUE,
    ORG_RECALL,
    ORG_SYNTHESIZE,
    ORG_VALIDATE,
    ORG_SANDBOX,
    ORG_ROUTE,
    ORGANS,
    organ_ids_for_mode,
    refine_organs_for_task,
    select_organs,
    required_roles_from_organs,
    describe_organs,
)

__all__ = [
    "Task",
    "SwarmState",
    "PartialResult",
    "FinalResult",
    "PolicyDecision",
    "decide_policy",
    "choose_execution_mode",
    "OrganBlock",
    "ORG_EXPLORE",
    "ORG_SIMULATE",
    "ORG_CRITIQUE",
    "ORG_RECALL",
    "ORG_SYNTHESIZE",
    "ORG_VALIDATE",
    "ORG_SANDBOX",
    "ORG_ROUTE",
    "ORGANS",
    "organ_ids_for_mode",
    "refine_organs_for_task",
    "select_organs",
    "required_roles_from_organs",
    "describe_organs",
]
