# -*- coding: utf-8 -*-
import os
import json

from .schema import validate_task, validate_solution
from .scorer import GraphScorerV2

def _load_tasks(tasks_dir: str):
    items = []
    for fn in sorted(os.listdir(tasks_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(tasks_dir, fn)
        with open(path, "r", encoding="utf-8") as f:
            task = json.load(f)
        if validate_task(task):
            items.append(task)
    return items

def run():
    base_dir = os.path.dirname(__file__)
    tasks_dir = os.path.abspath(os.path.join(base_dir, "../../datasets/grapheval/tasks"))

    print("🚀 GraphEval v0.2 (6-edge grammar + numeric pain)")
    print(f"Tasks dir: {tasks_dir}")
    print("-" * 72)

    tasks = _load_tasks(tasks_dir)

    # Demo solutions (hand-made “agents”)
    SOL = {
        "task_001": {"id": "task_001", "edges": [
            ["UI","Service","SYNC_CALL"],
            ["Service","DB","DATA"],
            ["Service","Cache","DATA"],
        ]},
        "task_002": {"id": "task_002", "edges": [
            ["A","B","DEP"],
            ["B","A","DEP"],
        ]},
        "task_003": {"id": "task_003", "edges": [
            ["UI","Service","SYNC_CALL"],
            ["UI","DB","EVENT"],   # should be OK
        ]},
        "task_004": {"id": "task_004", "edges": [
            ["UI","Service","SYNC_CALL"],
            ["Service","UI","FEEDBACK"],  # legal upward channel
            ["Service","DB","DATA"],
        ]},
        "task_005": {"id": "task_005", "edges": [
            ["A","B","SYNC_CALL"], ["A","C","SYNC_CALL"], ["A","D","SYNC_CALL"],
            ["B","A","SYNC_CALL"], ["B","C","SYNC_CALL"], ["B","D","SYNC_CALL"],
            ["C","A","SYNC_CALL"], ["C","B","SYNC_CALL"], ["C","D","SYNC_CALL"],
            ["D","A","SYNC_CALL"], ["D","B","SYNC_CALL"], ["D","C","SYNC_CALL"],
        ]},
        "task_006": {"id": "task_006", "edges": [
            ["Service","Cache","OWN"],
            ["UI","Service","SYNC_CALL"],
            ["Service","DB","DATA"],
        ]},
        "task_007": {"id": "task_007", "edges": [
            ["UI","API","SYNC_CALL"],
            ["API","A","SYNC_CALL"],
            ["A","B","DATA"],
            ["B","DB","DATA"],
            ["A","Bus","EVENT"],
            ["Bus","B","EVENT"],
        ]},
        "task_008": {"id": "task_008", "edges": [
            ["UI","Gateway","SYNC_CALL"],
            ["Gateway","Auth","SYNC_CALL"],
            ["Gateway","Billing","SYNC_CALL"],
            ["Billing","Bus","EVENT"],
            ["Bus","Analytics","EVENT"],
            ["Analytics","DB","DATA"],
        ]},
    }

    for task in tasks:
        scorer = GraphScorerV2(task)
        sol = SOL.get(task["id"], {"id": task["id"], "edges": []})

        if not validate_solution(sol):
            print(f"❌ Invalid solution format for {task['id']}")
            continue

        res = scorer.score_solution(sol)

        print(f"Task: {res['task_id']} — {res['title']}")
        print(f"[{res['verdict']:^5}] score={res['score']:.3f} risk={res['risk']:.3f} dna={res['dna']}")
        print(f"violations={res['violations']} metrics={res['metrics']}")
        print("-" * 72)

if __name__ == "__main__":
    run()
