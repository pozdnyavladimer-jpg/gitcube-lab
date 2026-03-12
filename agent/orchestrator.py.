# -*- coding: utf-8 -*-
"""Swarm orchestrator for GitCube Lab v0.1.

Pipeline:
- task -> report
- policy -> execution mode
- organs -> roles
- roles -> partial results
- final result

This is intentionally simple:
- no heavy ML
- no async runtime
- no external services
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent.schema import Task, SwarmState, PartialResult, FinalResult
from agent.policy import decide_policy
from agent.organs import (
    select_organs,
    required_roles_from_organs,
    describe_organs,
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _normalize_dna_key(dna: str, key_len: int = 3) -> str:
    s = (dna or "").strip()
    if not s:
        return ""
    if s.lower().startswith("dna:"):
        s = s.split(":", 1)[1].strip()
    toks = [t for t in s.replace(",", " ").split() if t and t[0].isalpha() and t[-1].isdigit()]
    return "|".join(toks[: max(1, int(key_len))])


def _band_from_verdict(verdict: str) -> int:
    v = (verdict or "").upper()
    if v == "BLOCK":
        return 1
    if v == "WARN":
        return 3
    return 6


# ---------------------------------------------------------
# Role implementations (minimal v0.1)
# ---------------------------------------------------------

def run_scout(task: Task, state: SwarmState, report: Dict[str, Any]) -> PartialResult:
    options: List[str] = []

    if task.context in {"graph", "architecture", "code", "repo"}:
        options = [
            "check layer grammar",
            "check capability constraints",
            "check forbidden edges",
        ]
    else:
        options = [
            "collect candidate branches",
            "rank possible paths",
            "keep low-risk option first",
        ]

    return PartialResult(
        role="scout",
        status="ok",
        data={
            "intent": task.intent,
            "context": task.context,
            "options": options,
        },
        notes=["Scout generated candidate directions."],
    )


def run_simulator(task: Task, state: SwarmState, report: Dict[str, Any]) -> PartialResult:
    return PartialResult(
        role="simulator",
        status="ok",
        data={
            "mode": state.mode,
            "risk": state.risk,
            "simulation": "sandbox-only hypothetical evaluation",
        },
        notes=["Simulation kept isolated from direct execution."],
    )


def run_critic(task: Task, state: SwarmState, report: Dict[str, Any]) -> PartialResult:
    notes: List[str] = []

    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    antidote = report.get("antidote") if isinstance(report.get("antidote"), dict) else {}
    violations = report.get("violations") if isinstance(report.get("violations"), dict) else {}

    if int(metrics.get("strict_cycle_nodes", 0) or 0) > 0:
        notes.append("strict cycle detected")
    if int(metrics.get("layer_viol", 0) or 0) > 0:
        notes.append("layer breach detected")
    if int(metrics.get("deadly_pairs", 0) or 0) > 0:
        notes.append("deadly pair detected")
    if int(antidote.get("feedback_cap_viol", 0) or 0) > 0:
        notes.append("feedback capability violation")
    if int(antidote.get("feedback_quota_viol", 0) or 0) > 0:
        notes.append("feedback quota violation")
    if int(antidote.get("event_cap_viol", 0) or 0) > 0:
        notes.append("event capability violation")
    if int(antidote.get("event_core_hits", 0) or 0) > 0:
        notes.append("event hit protected core")
    if bool(violations.get("goal_failed", False)):
        notes.append("goal failed")

    if not notes:
        notes.append("no critical structural issues found")

    return PartialResult(
        role="critic",
        status="ok",
        data={
            "risk": state.risk,
            "verdict": state.verdict,
            "issues": notes,
        },
        notes=["Critic evaluated structural failure paths."],
    )


def run_memory_agent(task: Task, state: SwarmState, report: Dict[str, Any]) -> PartialResult:
    meta = state.meta_control or {}
    return PartialResult(
        role="memory_agent",
        status="ok",
        data={
            "dna_key": state.dna_key,
            "memory_hits": state.memory_hits,
            "shrink_factor": state.shrink_factor,
            "meta_control": meta,
        },
        notes=["Memory agent inspected prior structural atoms."],
    )


def run_builder(task: Task, state: SwarmState, report: Dict[str, Any], partials: List[PartialResult]) -> PartialResult:
    action = recommend_action(task=task, state=state, report=report, partials=partials)

    return PartialResult(
        role="builder",
        status="ok",
        data={
            "recommended_action": action,
            "confidence": confidence_from_state(state),
        },
        notes=["Builder assembled final recommendation."],
    )


ROLE_RUNNERS = {
    "scout": run_scout,
    "simulator": run_simulator,
    "critic": run_critic,
    "memory_agent": run_memory_agent,
}


# ---------------------------------------------------------
# Recommendation / confidence
# ---------------------------------------------------------

def confidence_from_state(state: SwarmState) -> float:
    base = 1.0 - float(state.risk or 0.0)
    if state.mode == "BLOCKED":
        base *= 0.40
    elif state.mode == "SANDBOXED":
        base *= 0.70
    elif state.mode == "CAUTIOUS":
        base *= 0.85
    return max(0.05, min(0.99, round(base, 3)))


def recommend_action(
    *,
    task: Task,
    state: SwarmState,
    report: Dict[str, Any],
    partials: List[PartialResult],
) -> str:
    if state.mode == "BLOCKED":
        return "Block execution. Remove hazardous topology and re-evaluate."

    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    antidote = report.get("antidote") if isinstance(report.get("antidote"), dict) else {}

    if int(metrics.get("deadly_pairs", 0) or 0) > 0:
        return "Remove deadly pair and replace reverse control with safe adapter."
    if int(metrics.get("strict_cycle_nodes", 0) or 0) > 0:
        return "Break strict cycle before proceeding."
    if int(metrics.get("layer_viol", 0) or 0) > 0:
        return "Repair layer violations before expanding topology."
    if int(antidote.get("feedback_cap_viol", 0) or 0) > 0:
        return "Route FEEDBACK only through capability-enabled nodes."
    if int(antidote.get("event_core_hits", 0) or 0) > 0:
        return "Prevent EVENT delivery into protected core nodes."
    if state.mode == "SANDBOXED":
        return "Proceed only in sandbox mode and validate proposed edges."
    if state.mode == "CAUTIOUS":
        return "Proceed cautiously with validation and memory-aware checks."

    return "Proceed with low-risk path."


# ---------------------------------------------------------
# Report -> runtime state
# ---------------------------------------------------------

def swarm_state_from_report(
    report: Dict[str, Any],
    *,
    store_path: Optional[str] = None,
    lookback: int = 200,
) -> SwarmState:
    verdict = str(report.get("verdict") or "ALLOW").upper()
    risk = float(report.get("risk") or 0.0)
    score = float(report.get("score") or (1.0 - risk))
    dna = str(report.get("dna") or "")
    dna_key = str(report.get("dna_key") or "").strip()

    if not dna_key:
        dna_key = _normalize_dna_key(dna)

    kind = str(report.get("kind") or "")
    pd = decide_policy(
        report={
            **report,
            "dna_key": dna_key,
            "kind": kind,
        },
        store_path=store_path,
        kind=kind or None,
        lookback=lookback,
    )

    crystal_key = f"{kind}:{dna_key}" if kind and dna_key else (dna_key or "")

    return SwarmState(
        mode=pd.mode,
        verdict=verdict,
        risk=risk,
        score=score,
        dna=dna,
        dna_key=dna_key,
        band=int(report.get("band") or _band_from_verdict(verdict)),
        shrink_factor=float(pd.shrink_factor),
        memory_hits=int(pd.memory_hits),
        crystal_key=crystal_key,
        meta_control=pd.to_dict(),
    )


# ---------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------

def orchestrate_report(
    *,
    task: Task,
    report: Dict[str, Any],
    store_path: Optional[str] = None,
    lookback: int = 200,
) -> FinalResult:
    state = swarm_state_from_report(
        report,
        store_path=store_path,
        lookback=lookback,
    )

    organs = select_organs(task.intent, task.context, state.mode)
    roles = required_roles_from_organs(organs)

    partials: List[PartialResult] = []

    if state.mode != "BLOCKED":
        for role in roles:
            if role == "builder":
                continue
            runner = ROLE_RUNNERS.get(role)
            if runner is None:
                partials.append(
                    PartialResult(
                        role=role,
                        status="skip",
                        data={},
                        notes=[f"no runner defined for role={role}"],
                    )
                )
                continue
            partials.append(runner(task, state, report))

    builder_result = run_builder(task, state, report, partials)
    partials.append(builder_result)

    recommended_action = str(builder_result.data.get("recommended_action") or "")
    confidence = float(builder_result.data.get("confidence") or confidence_from_state(state))

    task_id = (
        task.meta.get("task_id")
        or task.payload.get("task_id")
        or report.get("task_id")
    )

    notes = [str(state.meta_control.get("reason") or "")] if state.meta_control else []

    return FinalResult(
        task_id=task_id,
        mode=state.mode,
        verdict=state.verdict,
        recommended_action=recommended_action,
        confidence=confidence,
        state=state.to_dict(),
        organs=describe_organs(organs),
        partials=[p.to_dict() for p in partials],
        notes=[n for n in notes if n],
    )


def orchestrate_task_dict(
    *,
    task_dict: Dict[str, Any],
    report: Dict[str, Any],
    store_path: Optional[str] = None,
    lookback: int = 200,
) -> Dict[str, Any]:
    task = Task.from_dict(task_dict)
    result = orchestrate_report(
        task=task,
        report=report,
        store_path=store_path,
        lookback=lookback,
    )
    return result.to_dict()
