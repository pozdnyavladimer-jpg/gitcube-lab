# -*- coding: utf-8 -*-
import math
from collections import defaultdict

STRICT_TYPES = {"SYNC_CALL", "DEP", "DATA", "OWN"}   # create structural traps
SOFT_TYPES   = {"EVENT"}                            # does NOT create fatal structural cycles
FEEDBACK     = "FEEDBACK"

class GraphScorerV2:
    """
    v0.2: 6-edge-type grammar + "pain must be numeric"

    Key rules:
    - strict cycles (DEP/SYNC/DATA/OWN) => BLOCK + high risk (>= 0.85)
    - layer violations => WARN and risk floor (>= 0.45 + 0.10*viol, capped)
    - density overload => sharp penalty (quadratic beyond max_density)
    - EVENT edges are exempt from layer diff checks (light touch)
    - FEEDBACK edges allow upward layer diff (legal control channel)
    """

    def __init__(self, task_def: dict):
        self.task = task_def
        self.nodes = {n["id"]: int(n["layer"]) for n in task_def["nodes"]}
        self.constraints = task_def.get("constraints", {}) or {}
        self.goal = task_def.get("goal", {}) or {}

        self.allowed_diffs = set(self.constraints.get("allowed_layer_diff", [0, 1]))
        self.max_density = float(self.constraints.get("max_density", 0.40))
        self.max_density = max(0.05, min(1.0, self.max_density))

    def _strict_cycle_nodes(self, edges):
        adj = defaultdict(list)
        for u, v, t in edges:
            if t in STRICT_TYPES:
                adj[u].append(v)

        visited, stack = set(), set()
        in_cycle = set()
        parent = {}

        def dfs(u):
            visited.add(u)
            stack.add(u)
            for v in adj[u]:
                if v not in visited:
                    parent[v] = u
                    dfs(v)
                elif v in stack:
                    # back-edge found => collect cycle nodes
                    cur = u
                    in_cycle.add(v)
                    while cur != v and cur in parent:
                        in_cycle.add(cur)
                        cur = parent[cur]
                    in_cycle.add(cur)
            stack.remove(u)

        for n in self.nodes.keys():
            if n not in visited:
                dfs(n)

        return len(in_cycle)

    def _goal_failed(self, edges):
        must_have = self.goal.get("must_have_edges", [])
        must_not  = self.goal.get("must_not_have_edges", [])

        # normalize edges to tuple form for comparison
        edge_set = set((u, v, t) for (u, v, t) in edges)

        for e in must_have:
            if isinstance(e, list) and len(e) == 3:
                if tuple(e) not in edge_set:
                    return True
        for e in must_not:
            if isinstance(e, list) and len(e) == 3:
                if tuple(e) in edge_set:
                    return True
        return False

    def score_solution(self, solution: dict) -> dict:
        edges = solution.get("edges", []) or []
        N = len(self.nodes)
        E = len(edges)

        # ---------- 1) Layer violations (semantic by edge type)
        layer_viol = 0
        unknown_nodes = 0

        for (u, v, t) in edges:
            if u not in self.nodes or v not in self.nodes:
                unknown_nodes += 1
                continue
            du = self.nodes[u]
            dv = self.nodes[v]
            diff = dv - du

            if t in SOFT_TYPES:
                # EVENT is a tangent touch; allow jumps (logging/telemetry/etc)
                continue

            if t == FEEDBACK and diff < 0:
                # FEEDBACK is a legal upward channel
                continue

            # strict-ish structural edges must obey layer gravity
            if diff not in self.allowed_diffs:
                layer_viol += 1

        # ---------- 2) Strict cycles
        strict_cycle_nodes = self._strict_cycle_nodes(edges)

        # ---------- 3) Density + entropy (structure overload)
        density = E / (N * (N - 1)) if N > 1 else 0.0
        entropy = (-density * math.log(density + 1e-12)) if density > 0 else 0.0

        # sharp density penalty beyond max_density
        d_ratio = density / self.max_density
        if d_ratio <= 1.0:
            d_pen = 0.0
        else:
            # quadratic blow-up
            d_pen = min(1.0, (d_ratio - 1.0) ** 2)

        # ---------- 4) Goals
        goal_failed = self._goal_failed(edges)

        # ---------- 5) Risk (continuous)
        cyc_norm = min(1.0, strict_cycle_nodes / max(1, N))
        lv_norm  = min(1.0, layer_viol / max(1, max(E, 1)))

        # base risk (smooth)
        risk = (0.70 * cyc_norm) + (0.25 * lv_norm) + (0.20 * d_pen)
        risk = min(1.0, risk)

        # ---------- 6) Pain floors (discrete physics -> numeric truth)
        # strict cycles are lethal
        if strict_cycle_nodes > 0:
            risk = max(risk, 0.85)

        # layer breach must "hurt"
        if layer_viol > 0:
            # minimum ~0.45, then grows per violation
            risk_floor = 0.45 + 0.10 * min(4, layer_viol)
            risk = max(risk, min(0.80, risk_floor))

        # failing the goal is also a big pain
        if goal_failed:
            risk = max(risk, 0.75)

        # clamp
        risk = float(max(0.0, min(1.0, risk)))

        # ---------- 7) Verdict (discrete)
        if strict_cycle_nodes > 0:
            verdict = "BLOCK"
        elif goal_failed:
            verdict = "WARN"
        elif layer_viol > 0:
            verdict = "WARN"
        elif risk > 0.70:
            verdict = "BLOCK"
        elif risk > 0.40:
            verdict = "WARN"
        else:
            verdict = "ALLOW"

        # ---------- 8) Score + DNA
        score = 1.0 - risk
        if verdict == "BLOCK":
            score *= 0.50
        if goal_failed:
            score *= 0.50

        # DNA tokens (0..9)
        c_tok = min(9, int(round(cyc_norm * 9)))
        l_tok = min(9, int(round(lv_norm  * 9)))
        # use density ratio vs max_density for D token
        d_tok = min(9, int(round(min(1.0, d_ratio) * 9)))
        h_tok = min(9, int(round(min(1.0, entropy / 0.70) * 9)))  # 0.70 is a soft normalizer

        dna = f"C{c_tok} L{l_tok} D{d_tok} H{h_tok}"

        return {
            "task_id": self.task["id"],
            "title": self.task.get("title", ""),
            "verdict": verdict,
            "risk": round(risk, 3),
            "score": round(score, 3),
            "dna": dna,
            "metrics": {
                "N": N,
                "E": E,
                "density": round(density, 3),
                "entropy": round(entropy, 3),
                "d_ratio": round(d_ratio, 3),
            },
            "violations": {
                "strict_cycle_nodes": strict_cycle_nodes,
                "layer_viol": layer_viol,
                "goal_failed": goal_failed,
                "unknown_nodes": unknown_nodes,
            },
        }
