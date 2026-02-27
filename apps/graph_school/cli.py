# apps/graph_school/cli.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from typing import Dict, List, Tuple

from .policies import get_policy, list_policies
from .sim_10_arch import GraphEnv


# ---------------------------
# Built-in demo cases
# ---------------------------

def build_demo_case(name: str, policy_name: str) -> GraphEnv:
    policy = get_policy(policy_name)
    g = GraphEnv(name=name, policy=policy)

    name = name.lower()

    if name == "layered_good":
        g.add_node("UI", 1)
        g.add_node("Service", 2)
        g.add_node("DB", 3)
        g.add_edge("UI", "Service")
        g.add_edge("Service", "DB")

    elif name == "layered_bad":
        g.add_node("UI", 1)
        g.add_node("Service", 2)
        g.add_node("DB", 3)
        g.add_edge("UI", "DB")  # skip
        g.add_edge("Service", "DB")

    elif name == "micro_cycle":
        for n in ["Orders", "Billing", "Catalog"]:
            g.add_node(n, 1)
        g.add_edge("Orders", "Billing")
        g.add_edge("Billing", "Orders")  # cycle
        g.add_edge("Orders", "Catalog")

    elif name == "clean_good":
        g.add_node("Framework", 4)
        g.add_node("Adapters", 3)
        g.add_node("UseCases", 2)
        g.add_node("Entities", 1)
        g.add_edge("Framework", "Adapters")
        g.add_edge("Adapters", "UseCases")
        g.add_edge("UseCases", "Entities")

    elif name == "clean_bad":
        g.add_node("Framework", 4)
        g.add_node("Adapters", 3)
        g.add_node("UseCases", 2)
        g.add_node("Entities", 1)
        g.add_edge("UseCases", "Entities")
        g.add_edge("Entities", "Adapters")  # outward

    else:
        raise ValueError(
            "Unknown demo case. Use: layered_good, layered_bad, "
            "micro_cycle, clean_good, clean_bad"
        )

    return g


# ---------------------------
# JSON loader
# ---------------------------

def build_from_json(path: str, policy_name: str) -> GraphEnv:
    policy = get_policy(policy_name)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    g = GraphEnv(name=data.get("name", "custom_graph"), policy=policy)

    nodes: Dict[str, int] = data["nodes"]
    edges: List[Tuple[str, str]] = data["edges"]

    for name, layer in nodes.items():
        g.add_node(name, layer)

    for u, v in edges:
        g.add_edge(u, v)

    return g


# ---------------------------
# CLI
# ---------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Graph School CLI — evaluate graph topology via policy grammar"
    )

    parser.add_argument(
        "--policy",
        required=True,
        help=f"Policy name. Available: {', '.join(sorted(list_policies()))}"
    )

    parser.add_argument(
        "--demo",
        help="Run built-in demo case: layered_good, layered_bad, micro_cycle, clean_good, clean_bad"
    )

    parser.add_argument(
        "--file",
        help="Path to JSON file describing graph"
    )

    args = parser.parse_args()

    if not args.demo and not args.file:
        parser.error("You must provide either --demo or --file")

    if args.demo:
        graph = build_demo_case(args.demo, args.policy)
    else:
        graph = build_from_json(args.file, args.policy)

    result = graph.evaluate()

    print("=" * 60)
    print(f"Graph:   {graph.name}")
    print(f"Policy:  {result.policy}")
    print("-" * 60)
    print(f"Verdict: {result.verdict}")
    print(f"Risk:    {result.risk:.3f}")
    print(f"DNA:     {result.dna}")
    print("-" * 60)
    print(f"Cycle nodes:      {result.cycle_nodes}")
    print(f"Layer violations: {result.layer_viol}")
    print(f"Skip violations:  {result.skip_viol}")
    print("=" * 60)


if __name__ == "__main__":
    main()
