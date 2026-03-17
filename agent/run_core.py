from agent.core import CoreEngine
from agent.pipeline import demo_task

engine = CoreEngine()

result = engine.run(demo_task())

import json
print(json.dumps(result, indent=2, ensure_ascii=False))
