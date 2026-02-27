# apps/graph_school/env.py
# -*- coding: utf-8 -*-

from __future__ import annotations
import json
import math
from typing import Dict, List, Tuple, Set
from collections import defaultdict


class GraphSchoolEnv:

    def __init__(self, rules: dict):
        self.rules = rules

    # -----------------------------
    # Cycle detection
    # -----------------------------

    def _count_cycle_nodes(self, nodes: List[str], edges: List[Tuple[str, str]]) -> int:
        adj = defaultdict(list)
        for u, v in edges:
            adj[u].append(v)

        visited: Set[str] = set()
        stack: Set[str] = set()
        in_cycle: Set[str] = set()
        parent: Dict[str, str] = {}

        def dfs(u: str):
            visited.add(u)
            stack.add(u)
            for v in adj[u]:
                if v not in visited:
                    parent[v] = u
                    dfs(v)
                elif v in stack:
                    cur = u
                    in_cycle.add(v)
                    while cur != v and cur in parent:
                        in_cycle.add(cur)
                        cur = parent[cur]
                    in_cycle.add(cur)
            stack.remove(u)

        for n in nodes:
            if n not in visited:
                dfs(n)

        return len(in_cycle)

    # -----------------------------
    # Evaluation
    # -----------------------------

    def evaluate(self, graph: dict) -> dict:

        nodes = graph["nodes"]
        edges = graph["edges"]

        N = len(nodes)
        E = len(edges)

        allowed_diffs = set(self.rules["allowed_layer_diffs"])

        layer_viol = 0
        skip_viol = 0

        for u, v in edges:
            diff = nodes[v] - nodes[u]
            if diff not in allowed_diffs:
                layer_viol += 1
                if abs(diff) >= 2:
                    skip_viol += 1

        cycle_nodes = self._count_cycle_nodes(list(nodes.keys()), edges)
        cyc_ratio = cycle_nodes / max(1, N)

        density = E / (N * (N - 1)) if N > 1 else 0.0
        entropy = -density * math.log(density + 1e-12) if density > 0 else 0.0

        # Risk model
        w_cycle = self.rules["weights"]["cycle"]
        w_layer = self.rules["weights"]["layer"]
        w_density = self.rules["weights"]["density"]

        risk = min(
            1.0,
            w_cycle * cyc_ratio +
            w_layer * (layer_viol / max(1, E)) +
            w_density * density
        )

        verdict = "ALLOW"

        if self.rules["hard_gates"]["skip_block"] and skip_viol > 0:
            verdict = "BLOCK"
            risk = max(risk, 0.85)

        elif cyc_ratio >= self.rules["hard_gates"]["cycle_block_ratio"]:
            verdict = "BLOCK"
            risk = max(risk, 0.80)

        elif layer_viol > 0 or cycle_nodes > 0:
            verdict = "WARN"
            risk = max(risk, 0.55)

        dna = (
            f"C{min(9, int(round(cyc_ratio * 9)))} "
            f"L{min(9, int(round((layer_viol / max(1,E)) * 9)))} "
            f"D{min(9, int(round(density * 9)))} "
            f"H{min(9, int(round(entropy * 9)))}"
        )

        return {
            "verdict": verdict,
            "risk": round(risk, 3),
            "dna": dna,
            "cycle_nodes": cycle_nodes,
            "layer_violations": layer_viol,
            "skip_violations": skip_viol
        }
