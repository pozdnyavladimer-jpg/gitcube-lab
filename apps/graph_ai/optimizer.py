# apps/graph_ai/optimizer.py

from apps.graph_school.cli import build_from_json
from apps.graph_school.policies import get_policy


def evaluate_graph(graph_data: dict, policy_name: str):
    policy = get_policy(policy_name)

    from apps.graph_school.sim_10_arch import GraphEnv

    g = GraphEnv(name=graph_data["name"], policy=policy)

    for n, l in graph_data["nodes"].items():
        g.add_node(n, l)

    for u, v in graph_data["edges"]:
        g.add_edge(u, v)

    return g.evaluate()


def auto_fix(graph_data: dict, policy_name: str):
    """
    Very naive structural fixer:
    - removes edges causing skip violations
    - removes cycle edges
    """

    result = evaluate_graph(graph_data, policy_name)

    if result.verdict == "ALLOW":
        return graph_data, result

    # Simple heuristic: remove last edge
    if graph_data["edges"]:
        graph_data["edges"].pop()

    return graph_data, evaluate_graph(graph_data, policy_name)
