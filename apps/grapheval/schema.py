# apps/grapheval/schema.py

ALLOWED_EDGE_TYPES = {"SYNC_CALL", "DATA", "EVENT", "DEP", "OWN", "FEEDBACK"}
EDGE_TUPLE_LEN = 3  # [from, to, type]

def validate_task(task: dict) -> bool:
    required = ["id", "title", "nodes", "constraints", "goal"]
    if not all(k in task for k in required):
        return False

    # nodes: [{"id": "...", "layer": int, optional flags...}]
    if not isinstance(task["nodes"], list) or len(task["nodes"]) == 0:
        return False
    for n in task["nodes"]:
        if not isinstance(n, dict):
            return False
        if "id" not in n or "layer" not in n:
            return False
        if not isinstance(n["layer"], int):
            return False

    # constraints: optional knobs validated in scorer
    if not isinstance(task["constraints"], dict):
        return False

    # goal: allow empty dict
    if not isinstance(task["goal"], dict):
        return False

    return True


def validate_solution(solution: dict) -> bool:
    required = ["id", "edges"]
    if not all(k in solution for k in required):
        return False

    edges = solution["edges"]
    if not isinstance(edges, list):
        return False

    for e in edges:
        if not isinstance(e, list) or len(e) < EDGE_TUPLE_LEN:
            return False
        if e[2] not in ALLOWED_EDGE_TYPES:
            return False

    return True
