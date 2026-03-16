# scripts/run_benchmark.py

import json
import glob
import subprocess
import os

TASK_DIR = "datasets/grapheval/tasks"
AGENTS = [
    "random_agent",
    "greedy_agent",
    "rule_based_agent",
    "resonance_agent",
]

RESULTS = []


def run_agent(agent, task_path):
    cmd = [
        "python",
        "-m",
        f"graph_school.baselines.{agent}",
        "--task",
        task_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
        )

        if result.stdout.strip():
            return json.loads(result.stdout)
        else:
            return None

    except Exception as e:
        return {"error": str(e)}


def main():

    tasks = glob.glob(os.path.join(TASK_DIR, "*.json"))

    print("Running benchmark...")
    print("Tasks:", len(tasks))

    for agent in AGENTS:

        print("\nAgent:", agent)

        for task in tasks:

            print("  task:", task)

            out = run_agent(agent, task)

            if out is None:
                continue

            RESULTS.append(
                {
                    "agent": agent,
                    "task": task,
                    "result": out,
                }
            )

    os.makedirs("reports", exist_ok=True)

    with open("reports/benchmark_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2)

    print("\nBenchmark finished.")
    print("Saved to reports/benchmark_results.json")


if __name__ == "__main__":
    main()
