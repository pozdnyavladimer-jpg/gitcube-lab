# apps/graph_ai/generator.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict


def generate_graph_from_prompt(prompt: str) -> Dict:
    """
    Mock AI generator.
    Replace with LLM call later.

    Current goal:
    - generate simple graphs that are structurally meaningful
    - avoid obviously toxic defaults unless explicitly requested
    """
    p = (prompt or "").lower()

    if "event" in p or "event-driven" in p or "broker" in p:
        return {
            "name": "EventDrivenSystem",
            "nodes": {
                "Producer": 1,
                "Broker": 1,
                "Consumer": 1
            },
            "edges": [
                ["Producer", "Broker"],
                ["Broker", "Consumer"]
            ]
        }

    if "microservice" in p or "microservices" in p:
        return {
            "name": "MicroservicesSystem",
            "nodes": {
                "Gateway": 1,
                "Orders": 1,
                "Billing": 1,
                "Catalog": 1
            },
            "edges": [
                ["Gateway", "Orders"],
                ["Orders", "Billing"],
                ["Orders", "Catalog"]
            ]
        }

    if "clean" in p or "onion" in p or "hexagonal" in p:
        return {
            "name": "CleanArchitecture",
            "nodes": {
                "Framework": 4,
                "Adapters": 3,
                "UseCases": 2,
                "Entities": 1
            },
            "edges": [
                ["Framework", "Adapters"],
                ["Adapters", "UseCases"],
                ["UseCases", "Entities"]
            ]
        }

    if "web app" in p or "webapp" in p or "layered" in p:
        return {
            "name": "WebApp",
            "nodes": {
                "UI": 1,
                "Service": 2,
                "DB": 3
            },
            "edges": [
                ["UI", "Service"],
                ["Service", "DB"]
            ]
        }

    # default fallback
    return {
        "name": "DefaultSystem",
        "nodes": {
            "Client": 1,
            "Core": 2,
            "Storage": 3
        },
        "edges": [
            ["Client", "Core"],
            ["Core", "Storage"]
        ]
    }
