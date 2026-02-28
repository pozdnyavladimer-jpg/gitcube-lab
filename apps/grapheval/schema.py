# -*- coding: utf-8 -*-

ALLOWED_EDGE_TYPES = {"SYNC_CALL", "DATA", "EVENT", "DEP", "OWN", "FEEDBACK"}

def validate_task(task: dict) -> bool:
    required = ["id", "title", "nodes", "constraints", "goal"]
    return isinstance(task, dict) and all(k in task for k in required)

def validate_solution(solution: dict) -> bool:
    if not isinstance(solution, dict):
        return False
    required = ["id", "edges"]
    if not all(k in solution for k in required):
        return False

    edges = solution.get("edges")
    if not isinstance(edges, list):
        return False

    for e in edges:
        # edge = [u, v, type]
        if not isinstance(e, list) or len(e) != 3:
            return False
        if not isinstance(e[0], str) or not isinstance(e[1], str) or not isinstance(e[2], str):
            return False
        if e[2] not in ALLOWED_EDGE_TYPES:
            return False
    return True
