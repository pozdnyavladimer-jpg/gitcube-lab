# apps/graph_school/sim_10_arch.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Tuple, Set


def count_cycle_nodes(nodes: List[str], edges: List[Tuple[str, str]]) -> int:
    """
    Returns number of nodes that are part of at least one directed cycle.
    Lightweight DFS, no external deps.
    """
    adj: Dict[str, List[str]] = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)

    visited: Set[str] = set()
    stack: Set[str] = set()
    in_cycle: Set[str] = set()
    parent: Dict[str, str] = {}

    def dfs(u: str) -> None:
        visited.add(u)
        stack.add(u)
        for v in adj[u]:
            if v not in visited:
                parent[v] = u
                dfs(v)
            elif v in stack:
                # Back-edge: mark cycle path u -> ... -> v
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


@dataclass
class EvalResult:
    verdict: str
    risk: float
    dna: str
    cycle_nodes: int
    layer_viol: int
    skip_viol: int
    density: float


class GraphEnv:
    """
    Generic graph grammar evaluator with:
    - layer diff rules (allowed diffs)
    - hard gates (cycles / layer skips)
    """

    def __init__(self, *, allowed_diffs: Set[int], name: str):
        self.name = name
        self.allowed_diffs = set(allowed_diffs)
        self.nodes: Dict[str, int] = {}
        self.edges: List[Tuple[str, str]] = []

    def add_node(self, name: str, layer: int) -> None:
        self.nodes[name] = int(layer)

    def add_edge(self, u: str, v: str) -> None:
        if u not in self.nodes or v not in self.nodes:
            raise ValueError(f"Unknown node in edge: {u} -> {v}")
        self.edges.append((u, v))

    def evaluate(self) -> EvalResult:
        N = len(self.nodes)
        E = len(self.edges)

        # Layer violations + "skip" violations (diff magnitude >= 2)
        layer_viol = 0
        skip_viol = 0
        for u, v in self.edges:
            diff = self.nodes[v] - self.nodes[u]
            if diff not in self.allowed_diffs:
                layer_viol += 1
                if abs(diff) >= 2:
                    skip_viol += 1

        cycle_nodes = count_cycle_nodes(list(self.nodes.keys()), self.edges)

        density = E / (N * (N - 1)) if N > 1 else 0.0
        entropy = -density * math.log(density + 1e-12) if density > 0 else 0.0

        # Base risk
        cyc = cycle_nodes / max(1, N)
        lv = layer_viol / max(1, E)

        risk = min(
            1.0,
            0.60 * cyc
            + 0.35 * lv
            + 0.05 * density
        )

        # HARD GATES (this is what makes it “real”)
        if skip_viol > 0:
            verdict = "BLOCK"
            risk = max(risk, 0.85)
        elif cycle_nodes > 0 and cyc >= 0.30:
            verdict = "BLOCK"
            risk = max(risk, 0.80)
        elif layer_viol > 0 or cycle_nodes > 0:
            verdict = "WARN"
            risk = max(risk, 0.55)
        else:
            verdict = "ALLOW"

        dna = (
            f"C{min(9, int(round(cyc * 9)))} "
            f"L{min(9, int(round(lv * 9)))} "
            f"D{min(9, int(round(density * 9)))} "
            f"H{min(9, int(round(entropy * 9)))}"
        )

        return EvalResult(
            verdict=verdict,
            risk=float(risk),
            dna=dna,
            cycle_nodes=cycle_nodes,
            layer_viol=layer_viol,
            skip_viol=skip_viol,
            density=float(density),
        )


def make_cases() -> List[GraphEnv]:
    cases: List[GraphEnv] = []

    # 1) Layered: allowed diffs {0, +1} (same layer or next layer)
    # Layers: UI=1, Service=2, DB=3
    g = GraphEnv(name="Layered (good)", allowed_diffs={0, 1})
    for n, l in [("UI", 1), ("Service", 2), ("DB", 3)]:
        g.add_node(n, l)
    g.add_edge("UI", "Service")
    g.add_edge("Service", "DB")
    cases.append(g)

    g = GraphEnv(name="Layered (UI→DB skip)", allowed_diffs={0, 1})
    for n, l in [("UI", 1), ("Service", 2), ("DB", 3)]:
        g.add_node(n, l)
    g.add_edge("UI", "DB")          # skip violation (+2) => BLOCK
    g.add_edge("UI", "Service")
    g.add_edge("Service", "DB")
    cases.append(g)

    # 2) Clean/Onion: dependencies point inward => allowed diffs {0, -1}
    # Outer=4 -> ... -> Inner=1
    g = GraphEnv(name="Clean/Onion (good inward)", allowed_diffs={0, -1})
    for n, l in [("Frameworks", 4), ("Adapters", 3), ("UseCases", 2), ("Entities", 1)]:
        g.add_node(n, l)
    g.add_edge("Frameworks", "Adapters")
    g.add_edge("Adapters", "UseCases")
    g.add_edge("UseCases", "Entities")
    cases.append(g)

    g = GraphEnv(name="Clean/Onion (bad outward dep)", allowed_diffs={0, -1})
    for n, l in [("Frameworks", 4), ("Adapters", 3), ("UseCases", 2), ("Entities", 1)]:
        g.add_node(n, l)
    g.add_edge("UseCases", "Entities")
    g.add_edge("Entities", "Adapters")  # outward (+2) => BLOCK
    cases.append(g)

    # 3) Hexagonal: Adapters -> Ports -> Domain (inward)
    g = GraphEnv(name="Hexagonal (good)", allowed_diffs={0, -1})
    for n, l in [("WebAdapter", 3), ("DBAdapter", 3), ("Ports", 2), ("Domain", 1)]:
        g.add_node(n, l)
    g.add_edge("WebAdapter", "Ports")
    g.add_edge("DBAdapter", "Ports")
    g.add_edge("Ports", "Domain")
    cases.append(g)

    g = GraphEnv(name="Hexagonal (bad Domain→DBAdapter)", allowed_diffs={0, -1})
    for n, l in [("WebAdapter", 3), ("DBAdapter", 3), ("Ports", 2), ("Domain", 1)]:
        g.add_node(n, l)
    g.add_edge("WebAdapter", "Ports")
    g.add_edge("Ports", "Domain")
    g.add_edge("Domain", "DBAdapter")   # outward (+2) => BLOCK
    cases.append(g)

    # 4) Microservices (no layer grammar) => allowed diffs {0}, we check cycles/density
    g = GraphEnv(name="Microservices (sparse)", allowed_diffs={0})
    for n in ["Auth", "Billing", "Orders", "Catalog", "Gateway"]:
        g.add_node(n, 1)
    g.add_edge("Gateway", "Auth")
    g.add_edge("Gateway", "Catalog")
    g.add_edge("Orders", "Billing")
    g.add_edge("Orders", "Catalog")
    cases.append(g)

    g = GraphEnv(name="Microservices (cycle Orders↔Billing)", allowed_diffs={0})
    for n in ["Orders", "Billing", "Catalog"]:
        g.add_node(n, 1)
    g.add_edge("Orders", "Billing")
    g.add_edge("Billing", "Orders")     # cycle => WARN/BLOCK depending size
    g.add_edge("Orders", "Catalog")
    cases.append(g)

    # 5) Event-driven with broker hub (no cycle, low density)
    g = GraphEnv(name="Event-driven (broker hub)", allowed_diffs={0})
    for n in ["ProducerA", "ProducerB", "ConsumerX", "ConsumerY", "Broker"]:
        g.add_node(n, 1)
    g.add_edge("ProducerA", "Broker")
    g.add_edge("ProducerB", "Broker")
    g.add_edge("ConsumerX", "Broker")
    g.add_edge("ConsumerY", "Broker")
    cases.append(g)

    # 6) Microkernel / Plugins: Plugins -> Kernel (inward)
    g = GraphEnv(name="Microkernel/Plugins (good)", allowed_diffs={0, -1})
    for n, l in [("PluginA", 2), ("PluginB", 2), ("Kernel", 1)]:
        g.add_node(n, l)
    g.add_edge("PluginA", "Kernel")
    g.add_edge("PluginB", "Kernel")
    cases.append(g)

    return cases


def main() -> None:
    cases = make_cases()
    print("=== GitCube Graph School: 10 Architecture Graphs Simulation ===")
    for g in cases:
        r = g.evaluate()
        print(
            f"- {g.name:35s} | {r.verdict:5s} | "
            f"risk={r.risk:.3f} | {r.dna} | "
            f"cycles={r.cycle_nodes} | L={r.layer_viol} | skip={r.skip_viol}"
        )


if __name__ == "__main__":
    main()
