from .state_cell import StateCell
from .gitcube_bridge import run_gitcube_risk


def encode_risk_to_state(risk_info):
    risk = risk_info["risk"]
    verdict = risk_info["verdict"]
    density = risk_info.get("density", 0.0)
    has_cycle = risk_info.get("has_cycle_2", False)
    layer_violations = risk_info.get("layer_violations", 0)

    red_mass = 0.10 + risk * 0.40
    orange_flow = 0.18 - risk * 0.08
    yellow_struct = 0.18 + max(0.0, 0.15 - density * 0.2)
    green_balance = 0.18 - risk * 0.10
    blue_law = 0.16 + min(layer_violations * 0.03, 0.12)
    violet_future = 0.12 + (0.06 if verdict == "WARN" else 0.03)

    if has_cycle:
        red_mass += 0.10
        green_balance -= 0.04
        orange_flow -= 0.02

    state = {
        "red_mass": max(red_mass, 0.0),
        "orange_flow": max(orange_flow, 0.0),
        "yellow_struct": max(yellow_struct, 0.0),
        "green_balance": max(green_balance, 0.0),
        "blue_law": max(blue_law, 0.0),
        "violet_future": max(violet_future, 0.0),
    }

    total = sum(state.values())
    if total > 0:
        state = {k: v / total for k, v in state.items()}

    return state


def run_canonical_pipeline(graph_payload, gitcube_path="/content/gitcube-lab"):
    # 1. real structural signal from GitCube
    risk_info = run_gitcube_risk(graph_payload, gitcube_path=gitcube_path)

    # 2. encode risk → state
    state = encode_risk_to_state(risk_info)

    # 3. build StateCell
    cell = StateCell(
        cell_id="demo",
        state_vector=state,
        graph_context=risk_info,
        active_agents=["planner", "stabilizer", "critic"]
    )

    # 4. simple coalition logic
    if risk_info["risk"] >= 0.6:
        decision = {
            "coalition": "planner+stabilizer",
            "status": "COMMIT"
        }
        metrics = {
            "shadow": 0.06,
            "coherence": 0.88,
            "target_fit": 0.58,
            "vitality": 0.38
        }
    elif risk_info["risk"] >= 0.3:
        decision = {
            "coalition": "planner+critic",
            "status": "SOFT_COMMIT"
        }
        metrics = {
            "shadow": 0.09,
            "coherence": 0.84,
            "target_fit": 0.55,
            "vitality": 0.33
        }
    else:
        decision = {
            "coalition": "planner+explorer",
            "status": "COMMIT"
        }
        metrics = {
            "shadow": 0.03,
            "coherence": 0.91,
            "target_fit": 0.63,
            "vitality": 0.46
        }

    cell.set_decision(decision)
    cell.update_metrics(metrics)
    cell.add_trace({
        "step": 0,
        "event": "gitcube_to_gsl_commit",
        "risk_info": risk_info,
    })

    return cell


if __name__ == "__main__":
    example_graph = {
        "nodes": ["A", "B", "C"],
        "edges": [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "A"},
            {"from": "B", "to": "C"},
        ],
        "layer_violations": 1
    }

    result = run_canonical_pipeline(example_graph)

    print("Graph context:", result.graph_context)
    print("State vector:", result.state_vector)
    print("Decision:", result.last_decision)
    print("Metrics:", result.metrics)
