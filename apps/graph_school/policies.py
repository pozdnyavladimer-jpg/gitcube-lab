# apps/graph_school/policies.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Set, Optional


@dataclass(frozen=True)
class Policy:
    """
    Policy = "graph language" (grammar) + hard gates.

    allowed_diffs:
      - Layer direction constraints expressed as (layer[v] - layer[u]) allowed values.
      - Example layered: {0, +1}
      - Example inward (clean/hex/microkernel): {0, -1}
      - Flat graphs (microservices/event): {0}

    Hard gates:
      - skip_viol (abs(diff) >= 2) => BLOCK (for layered/inward policies)
      - cycle_nodes_ratio >= cycle_block_ratio => BLOCK
      - any cycle => at least WARN (if cycle_warn=True)
      - any layer violation => at least WARN (if layer_warn=True)
    """
    name: str
    allowed_diffs: Set[int]

    # Hard gates
    cycle_warn: bool = True
    layer_warn: bool = True
    skip_block: bool = True
    cycle_block_ratio: float = 0.30  # if >= 30% nodes in cycles => BLOCK

    # Risk weights (tunable)
    w_cycle: float = 0.60
    w_layer: float = 0.35
    w_density: float = 0.05


# -------------------------
# Presets (5 "languages")
# -------------------------

LAYERED_3TIER = Policy(
    name="layered_3tier",
    allowed_diffs={0, 1},
    cycle_warn=True,
    layer_warn=True,
    skip_block=True,
    cycle_block_ratio=0.30,
)

INWARD_CLEAN_ONION = Policy(
    name="inward_clean_onion",
    allowed_diffs={0, -1},
    cycle_warn=True,
    layer_warn=True,
    skip_block=True,
    cycle_block_ratio=0.30,
)

INWARD_HEXAGONAL = Policy(
    name="inward_hexagonal",
    allowed_diffs={0, -1},
    cycle_warn=True,
    layer_warn=True,
    skip_block=True,
    cycle_block_ratio=0.30,
)

FLAT_MICROSERVICES = Policy(
    name="flat_microservices",
    allowed_diffs={0},
    # services can call each other; layering is not enforced here
    layer_warn=False,
    skip_block=False,
    cycle_warn=True,
    cycle_block_ratio=0.20,  # cycles between services are extra toxic: stricter
    w_cycle=0.75,
    w_layer=0.00,
    w_density=0.25,
)

EVENT_DRIVEN = Policy(
    name="event_driven",
    allowed_diffs={0},
    # event systems often have hubs; layering isn't the main thing
    layer_warn=False,
    skip_block=False,
    cycle_warn=True,
    cycle_block_ratio=0.35,  # cycles can exist (feedback), tolerate more
    w_cycle=0.65,
    w_layer=0.00,
    w_density=0.35,
)


def get_policy(name: str) -> Policy:
    n = (name or "").strip().lower()
    table = {
        LAYERED_3TIER.name: LAYERED_3TIER,
        INWARD_CLEAN_ONION.name: INWARD_CLEAN_ONION,
        INWARD_HEXAGONAL.name: INWARD_HEXAGONAL,
        FLAT_MICROSERVICES.name: FLAT_MICROSERVICES,
        EVENT_DRIVEN.name: EVENT_DRIVEN,
    }
    if n not in table:
        raise ValueError(
            "Unknown policy. Use one of: "
            + ", ".join(sorted(table.keys()))
        )
    return table[n]


def list_policies() -> Set[str]:
    return {
        LAYERED_3TIER.name,
        INWARD_CLEAN_ONION.name,
        INWARD_HEXAGONAL.name,
        FLAT_MICROSERVICES.name,
        EVENT_DRIVEN.name,
    }
