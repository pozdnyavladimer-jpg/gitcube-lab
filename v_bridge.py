import json
import os
from datetime import datetime

class VBridge:
    def __init__(self, path="v_resonance.json"):
        self.path = path

    def read(self):
        if not os.path.exists(self.path):
            return None
        with open(self.path, "r") as f:
            return json.load(f)

    def write(self, data):
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    def update_flower(self, updates: dict):
        data = self.read()
        if not data:
            return
        data["flower"].update(updates)
        data["meta"]["step"] += 1
        data["meta"]["timestamp"] = str(datetime.utcnow())
        self.write(data)

    def set_signal(self, source, target, action, bond="NONE"):
        data = self.read()
        if not data:
            return
        data["signal"] = {
            "source": source,
            "target": target,
            "action": action,
            "bond": bond
        }
        self.write(data)

    def get_signal(self):
        data = self.read()
        return data.get("signal") if data else None
