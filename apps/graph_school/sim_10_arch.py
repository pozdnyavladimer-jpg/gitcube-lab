# apps/graph_school/sim_10_arch.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Tuple, Set

from .policies import (
    Policy,
    LAYERED_3TIER,
    INWARD_CLEAN_ONION,
    INWARD_HEXAGONAL,
    FLAT_MICROSERVICES,
    EVENT_DRIVEN,
)


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
    policy: str


class GraphEnv:
    """
    Graph evaluator that uses a Policy as grammar.
    """

    def __init__(self, *, name: str, policy: Policy):
        self.name = name
        self.policy = policy
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

        layer_viol = 0
        skip_viol = 0

        for u, v in self.edges:
            diff = self.nodes[v] - self.nodes[u]
            if diff not in self.policy.allowed_diffs:
                layer_viol += 1
                if abs(diff) >= 2:
                    skip_viol += 1

        cycle_nodes = count_cycle_nodes(list(self.nodes.keys()), self.edges)

        density = E / (N * (N - 1)) if N > 1 else 0.0
        entropy = -density * math.log(density + 1e-12) if density > 0 else 0.0

        cyc_ratio = cycle_nodes / max(1, N)
        lv_ratio = layer_viol / max(1, E)

        # Base risk (policy-weighted)
        risk = min(
            1.0,
            self.policy.w_cycle * cyc_ratio
            + self.policy.w_layer * lv_ratio
            + self.policy.w_density * density
        )

        # HARD GATES (policy-driven)
        verdict = "ALLOW"

        if self.policy.skip_block and skip_viol > 0:
            verdict = "BLOCK"
            risk = max(risk, 0.85)

        elif cycle_nodes > 0 and cyc_ratio >= float(self.policy.cycle_block_ratio):
            verdict = "BLOCK"
            risk = max(risk, 0.80)

        elif (self.policy.cycle_warn and cycle_nodes > 0) or (self.policy.layer_warn and layer_viol > 0):
            verdict = "WARN"
            risk = max(risk, 0.55)

        dna = (
            f"C{min(9, int(round(cyc_ratio * 9)))} "
            f"L{min(9, int(round(lv_ratio * 9)))} "
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
            policy=self.policy.name,
        )


def make_cases() -> List[GraphEnv]:
    cases: List[GraphEnv] = []

    # 1) Layered good
    g = GraphEnv(name="Layered (good)", policy=LAYERED_3TIER)
    for n, l in [("UI", 1), ("Service", 2), ("DB", 3)]:
        g.add_node(n, l)
    g.add_edge("UI", "Service")
    g.add_edge("Service", "DB")
    cases.append(g)

    # 2) Layered bad skip
    g = GraphEnv(name="Layered (UI→DB skip)", policy=LAYERED_3TIER)
    for n, l in [("UI", 1), ("Service", 2), ("DB", 3)]:
        g.add_node(n, l)
    g.add_edge("UI", "DB")  # +2 => BLOCK
    g.add_edge("UI", "Service")
    g.add_edge("Service", "DB")
    cases.append(g)

    # 3) Clean/Onion good inward
    g = GraphEnv(name="Clean/Onion (good inward)", policy=INWARD_CLEAN_ONION)
    for n, l in [("Frameworks", 4), ("Adapters", 3), ("UseCases", 2), ("Entities", 1)]:
        g.add_node(n, l)
    g.add_edge("Frameworks", "Adapters")
    g.add_edge("Adapters", "UseCases")
    g.add_edge("UseCases", "Entities")
    cases.append(g)

    # 4) Clean/Onion bad outward
    g = GraphEnv(name="Clean/Onion (bad outward)", policy=INWARD_CLEAN_ONION)
    for n, l in [("Frameworks", 4), ("Adapters", 3), ("UseCases", 2), ("Entities", 1)]:
        g.add_node(n, l)
    g.add_edge("UseCases", "Entities")
    g.add_edge("Entities", "Adapters")  # +2 => BLOCK
    cases.append(g)

    # 5) Hexagonal good
    g = GraphEnv(name="Hexagonal (good)", policy=INWARD_HEXAGONAL)
    for n, l in [("WebAdapter", 3), ("DBAdapter", 3), ("Ports", 2), ("Domain", 1)]:
        g.add_node(n, l)
    g.add_edge("WebAdapter", "Ports")
    g.add_edge("DBAdapter", "Ports")
    g.add_edge("Ports", "Domain")
    cases.append(g)

    # 6) Hexagonal bad outward
    g = GraphEnv(name="Hexagonal (bad Domain→DBAdapter)", policy=INWARD_HEXAGONAL)
    for n, l in [("WebAdapter", 3), ("DBAdapter", 3), ("Ports", 2), ("Domain", 1)]:
        g.add_node(n, l)
    g.add_edge("WebAdapter", "Ports")
    g.add_edge("Ports", "Domain")
    g.add_edge("Domain", "DBAdapter")  # +2 => BLOCK
    cases.append(g)

    # 7) Microservices sparse
    g = GraphEnv(name="Microservices (sparse)", policy=FLAT_MICROSERVICES)
    for n in ["Auth", "Billing", "Orders", "Catalog", "Gateway"]:
        g.add_node(n, 1)
    g.add_edge("Gateway", "Auth")
    g.add_edge("Gateway", "Catalog")
    g.add_edge("Orders", "Billing")
    g.add_edge("Orders", "Catalog")
    cases.append(g)

    # 8) Microservices with cycle
    g = GraphEnv(name="Microservices (cycle Orders↔Billing)", policy=FLAT_MICROSERVICES)
    for n in ["Orders", "Billing", "Catalog"]:
        g.add_node(n, 1)
    g.add_edge("Orders", "Billing")
    g.add_edge("Billing", "Orders")  # cycle
    g.add_edge("Orders", "Catalog")
    cases.append(g)

    # 9) Event-driven hub
    g = GraphEnv(name="Event-driven (broker hub)", policy=EVENT_DRIVEN)
    for n in ["ProducerA", "ProducerB", "ConsumerX", "ConsumerY", "Broker"]:
        g.add_node(n, 1)
    g.add_edge("ProducerA", "Broker")
    g.add_edge("ProducerB", "Broker")
    g.add_edge("ConsumerX", "Broker")
    g.add_edge("ConsumerY", "Broker")
    cases.append(g)

    # 10) Event-driven with feedback (tolerated more)
    g = GraphEnv(name="Event-driven (feedback loop)", policy=EVENT_DRIVEN)
    for n in ["ServiceA", "ServiceB", "Broker"]:
        g.add_node(n, 1)
    g.add_edge("ServiceA", "Broker")
    g.add_edge("Broker", "ServiceB")
    g.add_edge("ServiceB", "Broker")  # small feedback loop
    cases.append(g)

    return cases


def main() -> None:
    cases = make_cases()
    print("=== GitCube Graph School: 10 Graphs (policy-driven) ===")
    for g in cases:
        r = g.evaluate()
        print(
            f"- {g.name:36s} | policy={r.policy:20s} | {r.verdict:5s} | "
            f"risk={r.risk:.3f} | {r.dna} | "
            f"cycles={r.cycle_nodes} | L={r.layer_viol} | skip={r.skip_viol}"
        )


if __name__ == "__main__":
    main()
