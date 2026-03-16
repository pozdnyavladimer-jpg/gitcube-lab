# apps/graph_ai/task_templates.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict


# ---------------------------------------------------------
# Architecture templates
# ---------------------------------------------------------

LAYERED_TEMPLATE = {
    "allowed_layer_diff": [0, 1],
    "max_density": 0.40,
    "feedback_requires_capability": True,
    "feedback_capability_key": "can_feedback",
    "event_capability_key": "can_event",
    "feedback_ratio_max": 0.10,
    "deadly_pairs_block": True,
    "event_to_core_block": True,
    "protected_nodes_key": "is_core",
}

MICROSERVICES_TEMPLATE = {
    "allowed_layer_diff": [0],
    "max_density": 0.60,
    "feedback_requires_capability": False,
    "feedback_capability_key": "can_feedback",
    "event_capability_key": "can_event",
    "feedback_ratio_max": 0.20,
    "deadly_pairs_block": False,
    "event_to_core_block": False,
    "protected_nodes_key": "is_core",
}

EVENT_DRIVEN_TEMPLATE = {
    "allowed_layer_diff": [0],
    "max_density": 0.70,
    "feedback_requires_capability": False,
    "feedback_capability_key": "can_feedback",
    "event_capability_key": "can_event",
    "feedback_ratio_max": 0.30,
    "deadly_pairs_block": False,
    "event_to_core_block": False,
    "protected_nodes_key": "is_core",
}

CLEAN_ARCH_TEMPLATE = {
    "allowed_layer_diff": [0, -1],
    "max_density": 0.35,
    "feedback_requires_capability": True,
    "feedback_capability_key": "can_feedback",
    "event_capability_key": "can_event",
    "feedback_ratio_max": 0.10,
    "deadly_pairs_block": True,
    "event_to_core_block": True,
    "protected_nodes_key": "is_core",
}


# ---------------------------------------------------------
# Prompt classifier
# ---------------------------------------------------------

def detect_architecture(prompt: str) -> str:
    """
    Very simple keyword classifier.

    Later this can be replaced with LLM reasoning.
    """

    p = (prompt or "").lower()

    if "microservice" in p or "microservices" in p:
        return "microservices"

    if "event" in p or "event-driven" in p or "broker" in p:
        return "event_driven"

    if "clean" in p or "onion" in p or "hexagonal" in p:
        return "clean_arch"

    if "layered" in p or "web app" in p:
        return "layered"

    return "layered"


# ---------------------------------------------------------
# Template loader
# ---------------------------------------------------------

def get_template(prompt: str) -> Dict:
    arch = detect_architecture(prompt)

    if arch == "microservices":
        return MICROSERVICES_TEMPLATE

    if arch == "event_driven":
        return EVENT_DRIVEN_TEMPLATE

    if arch == "clean_arch":
        return CLEAN_ARCH_TEMPLATE

    return LAYERED_TEMPLATE
