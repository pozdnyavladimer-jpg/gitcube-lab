import json
import sys


def simple_graph_risk(payload: dict) -> dict:
    """
    Тимчасовий bridge-layer.
    Якщо вже є справжній GraphEval API — потім замінимо цю функцію на реальний виклик.
    """

    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])
    layer_violations = payload.get("layer_violations", 0)

    node_count = len(nodes)
    edge_count = len(edges)

    # very simple cycle heuristic
    edge_set = {(e["from"], e["to"]) for e in edges if "from" in e and "to" in e}
    has_cycle_2 = any((b, a) in edge_set for (a, b) in edge_set)

    density = 0.0
    if node_count > 1:
        density = edge_count / (node_count * (node_count - 1))

    risk = 0.0
    risk += 0.45 if has_cycle_2 else 0.0
    risk += min(density * 0.7, 0.35)
    risk += min(layer_violations * 0.08, 0.20)

    risk = min(max(risk, 0.0), 1.0)

    if risk < 0.30:
        verdict = "ALLOW"
    elif risk < 0.60:
        verdict = "WARN"
    else:
        verdict = "BLOCK"

    return {
        "risk": round(risk, 3),
        "verdict": verdict,
        "node_count": node_count,
        "edge_count": edge_count,
        "density": round(density, 3),
        "has_cycle_2": has_cycle_2,
        "layer_violations": layer_violations,
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    result = simple_graph_risk(payload)
    print(json.dumps(result))
