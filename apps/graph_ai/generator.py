# apps/graph_ai/generator.py

from typing import Dict, List, Tuple

def generate_graph_from_prompt(prompt: str) -> Dict:
    """
    Mock AI generator.
    Replace with LLM call later.
    """

    if "web app" in prompt.lower():
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

    if "microservices" in prompt.lower():
        return {
            "name": "Micro",
            "nodes": {
                "Orders": 1,
                "Billing": 1,
                "Catalog": 1
            },
            "edges": [
                ["Orders", "Billing"],
                ["Billing", "Orders"]
            ]
        }

    # default fallback
    return {
        "name": "Default",
        "nodes": {
            "Core": 1
        },
        "edges": []
    }
