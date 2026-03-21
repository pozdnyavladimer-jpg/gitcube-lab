import json
import subprocess
from typing import Dict, Any


def run_gitcube_risk(
    graph_payload: Dict[str, Any],
    gitcube_path: str = "/content/gitcube-lab"
) -> Dict[str, Any]:
    """
    Викликає GitCube bridge/export_risk.py через subprocess.
    """

    cmd = ["python", "bridge/export_risk.py"]

    proc = subprocess.run(
        cmd,
        input=json.dumps(graph_payload),
        text=True,
        capture_output=True,
        cwd=gitcube_path,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"GitCube risk export failed.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )

    return json.loads(proc.stdout)
