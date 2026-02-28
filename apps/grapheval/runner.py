# apps/grapheval/runner.py

import os, json
from apps.grapheval.schema import validate_task, validate_solution
from apps.grapheval.scorer import GraphScorer

def run():
    base = os.path.dirname(__file__)
    tasks_dir = os.path.abspath(os.path.join(base, "../../datasets/grapheval/tasks"))

    print("🚀 GraphEval v0.3 (Antidote)")
    print("-" * 70)

    # demo “agent” solutions:
    solutions = {
        "task_009_antidote": {
            "id": "task_009_antidote",
            "edges": [
                ["UI", "Service", "SYNC_CALL"],
                ["Service", "DB", "DATA"],

                # attempt to cheat: rename SYNC to FEEDBACK
                ["DB", "UI", "FEEDBACK"],  # should be blocked by capability/quota/deadly-pair rules
            ],
        },
        "task_010_feedback_ok": {
            "id": "task_010_feedback_ok",
            "edges": [
                ["UI", "Service", "SYNC_CALL"],
                ["Service", "DB", "DATA"],
                # legal feedback via observability adapter (capability nodes)
                ["DB", "Observer", "EVENT"],
                ["Observer", "UI", "FEEDBACK"],
            ],
        },
    }

    for fn in sorted(os.listdir(tasks_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(tasks_dir, fn)
        with open(path, "r", encoding="utf-8") as f:
            task = json.load(f)

        if not validate_task(task):
            continue

        scorer = GraphScorer(task)
        sol = solutions.get(task["id"], {"id": task["id"], "edges": []})

        if not validate_solution(sol):
            print(f"❌ invalid solution format: {task['id']}")
            continue

        res = scorer.score_solution(sol)

        print(f"Task: {task['id']} | {task['title']}")
        print(f"[{res['verdict']:^5}] score={res['score']:.3f} risk={res['risk']:.3f} | {res['dna']}")
        print(f"metrics: {res['metrics']}")
        print(f"antidote: {res['antidote']}")
        print("-" * 70)

if __name__ == "__main__":
    run()
