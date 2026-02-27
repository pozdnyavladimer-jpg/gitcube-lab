# apps/graph_ai/run_ai_loop.py

from generator import generate_graph_from_prompt
from optimizer import evaluate_graph, auto_fix


def run(prompt: str, policy: str):
    graph = generate_graph_from_prompt(prompt)

    print("Initial graph:", graph)

    result = evaluate_graph(graph, policy)
    print("Initial verdict:", result.verdict, result.dna)

    steps = 0

    while result.verdict != "ALLOW" and steps < 5:
        graph, result = auto_fix(graph, policy)
        print("Fix step:", steps + 1, "→", result.verdict)
        steps += 1

    print("Final graph:", graph)
    print("Final verdict:", result.verdict)


if __name__ == "__main__":
    run("microservices app", "flat_microservices")
