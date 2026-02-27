# apps/graph_school/runner.py
# -*- coding: utf-8 -*-

import json
import os

from .env import GraphSchoolEnv


BASE_DIR = os.path.dirname(__file__)
LESSONS_DIR = os.path.join(BASE_DIR, "lessons")
RULES_PATH = os.path.join(BASE_DIR, "rubrics", "rules_v1.json")


def load_rules():
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_lessons():
    lessons = []
    for file in sorted(os.listdir(LESSONS_DIR)):
        if file.endswith(".json"):
            path = os.path.join(LESSONS_DIR, file)
            with open(path, "r", encoding="utf-8") as f:
                lessons.append(json.load(f))
    return lessons


def run():
    rules = load_rules()
    env = GraphSchoolEnv(rules)

    lessons = load_lessons()

    print("=== Graph School Runner ===\n")

    for lesson in lessons:
        print(f"Lesson: {lesson['name']}")
        result = env.evaluate(lesson["graph"])
        print("Verdict:", result["verdict"])
        print("Risk:", result["risk"])
        print("DNA:", result["dna"])
        print("Cycles:", result["cycle_nodes"])
        print("Layer violations:", result["layer_violations"])
        print("-" * 40)


if __name__ == "__main__":
    run()
