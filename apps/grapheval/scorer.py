# apps/grapheval/scorer.py

import math
from collections import defaultdict

STRICT_TYPES = {"SYNC_CALL", "DEP", "DATA", "OWN"}
SOFT_TYPES = {"EVENT"}

DEFAULTS = {
    "allowed_layer_diff": [0, 1],
    "max_density": 0.40,

    # Anti-toxin knobs:
    "feedback_requires_capability": True,
    "feedback_capability_key": "can_feedback",   # node flag
    "event_capability_key": "can_event",         # optional
    "feedback_ratio_max": 0.05,                  # <= 5% of strict edges
    "deadly_pairs_block": True,                  # SYNC_CALL A->B + FEEDBACK B->A
    "event_to_core_block": False,                # optional: block EVENT hitting protected nodes
    "protected_nodes_key": "is_core",            # node flag for "core"
}

def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


class GraphScorer:
    def __init__(self, task_def: dict):
        self.task = task_def

        # nodes: id -> layer, and flags
        self.layers = {}
        self.flags = {}  # id -> dict flags
        for n in task_def["nodes"]:
            nid = n["id"]
            self.layers[nid] = n["layer"]
            self.flags[nid] = {k: v for k, v in n.items() if k not in ("id", "layer")}

        self.constraints = {**DEFAULTS, **(task_def.get("constraints") or {})}
        self.goal = task_def.get("goal") or {}

    def _find_strict_cycles_dfs(self, edges):
        # cycles only over strict edges
        adj = defaultdict(list)
        for u, v, t in edges:
            if t in STRICT_TYPES:
                adj[u].append(v)

        visited, stack, in_cycle = set(), set(), set()
        parent = {}

        def dfs(u):
            visited.add(u)
            stack.add(u)
            for w in adj[u]:
                if w not in visited:
                    parent[w] = u
                    dfs(w)
                elif w in stack:
                    cur = u
                    in_cycle.add(w)
                    while cur != w and cur in parent:
                        in_cycle.add(cur)
                        cur = parent[cur]
                    in_cycle.add(cur)
            stack.remove(u)

        for n in self.layers.keys():
            if n not in visited:
                dfs(n)
        return len(in_cycle)

    def _goal_failed(self, edges):
        # goals operate on (u,v,type?) – support both 2 and 3 tuples
        must_have = self.goal.get("must_have_edges", [])
        must_not = self.goal.get("must_not_have_edges", [])

        edge_set_2 = set((u, v) for (u, v, _t) in edges)
        edge_set_3 = set((u, v, t) for (u, v, t) in edges)

        failed = False
        for e in must_have:
            if len(e) == 2:
                if (e[0], e[1]) not in edge_set_2:
                    failed = True
            else:
                if (e[0], e[1], e[2]) not in edge_set_3:
                    failed = True

        for e in must_not:
            if len(e) == 2:
                if (e[0], e[1]) in edge_set_2:
                    failed = True
            else:
                if (e[0], e[1], e[2]) in edge_set_3:
                    failed = True
        return failed

    def score_solution(self, solution: dict):
        edges = solution.get("edges") or []
        # filter unknown nodes (ignore)
        edges = [e for e in edges if len(e) >= 3 and e[0] in self.layers and e[1] in self.layers]

        N = len(self.layers)
        E = len(edges)

        allowed_diffs = set(self.constraints["allowed_layer_diff"])
        max_density = float(self.constraints["max_density"])

        # --- anti-toxin knobs ---
        feedback_requires_cap = bool(self.constraints["feedback_requires_capability"])
        feedback_key = str(self.constraints["feedback_capability_key"])
        event_key = str(self.constraints["event_capability_key"])
        feedback_ratio_max = float(self.constraints["feedback_ratio_max"])
        deadly_pairs_block = bool(self.constraints["deadly_pairs_block"])
        event_to_core_block = bool(self.constraints["event_to_core_block"])
        protected_nodes_key = str(self.constraints["protected_nodes_key"])

        # --- counters ---
        layer_viol = 0
        feedback_count = 0
        strict_count = 0
        event_count = 0

        # For deadly pair check
        sync_pairs = set()
        feedback_pairs = set()

        # Capability violations
        feedback_cap_viol = 0
        event_cap_viol = 0
        event_core_hits = 0

        for u, v, t in edges:
            lu, lv = self.layers[u], self.layers[v]
            diff = lv - lu

            if t in STRICT_TYPES:
                strict_count += 1
            if t == "FEEDBACK":
                feedback_count += 1
                feedback_pairs.add((u, v))
            if t == "SYNC_CALL":
                sync_pairs.add((u, v))
            if t == "EVENT":
                event_count += 1

            # --- capability gate ---
            if t == "FEEDBACK" and feedback_requires_cap:
                # require can_feedback on BOTH ends (sender + receiver)
                if not self.flags.get(u, {}).get(feedback_key, False) or not self.flags.get(v, {}).get(feedback_key, False):
                    feedback_cap_viol += 1

            if t == "EVENT":
                # optional: require can_event if present in task nodes
                # (if key absent everywhere — no penalty)
                any_event_key_defined = any(event_key in self.flags.get(nid, {}) for nid in self.flags)
                if any_event_key_defined:
                    if not self.flags.get(u, {}).get(event_key, False):
                        event_cap_viol += 1

                # optional: block EVENT hitting protected/core nodes
                if event_to_core_block and self.flags.get(v, {}).get(protected_nodes_key, False):
                    event_core_hits += 1

            # --- layer grammar ---
            if t in SOFT_TYPES:
                # EVENT is "light touch": no layer violation by default
                continue

            if t == "FEEDBACK":
                # FEEDBACK may go upward (diff < 0) legally, BUT must be "small"
                # we only penalize if it jumps too far (e.g., layer 3 -> layer 1)
                if diff < 0 and abs(diff) <= 1:
                    continue
                # else treat as violation
                if diff not in allowed_diffs:
                    layer_viol += 1
                continue

            # strict edges must obey allowed diffs
            if diff not in allowed_diffs:
                layer_viol += 1

        # --- Strict cycle detection ---
        strict_cycle_nodes = self._find_strict_cycles_dfs(edges)

        # --- Deadly pair detection ---
        deadly_pairs = 0
        if deadly_pairs_block:
            # if A->B is SYNC_CALL and B->A is FEEDBACK => deadly
            for (a, b) in sync_pairs:
                if (b, a) in feedback_pairs:
                    deadly_pairs += 1

        # --- Feedback quota ---
        feedback_quota_viol = 0
        if strict_count > 0:
            if feedback_count > math.ceil(feedback_ratio_max * strict_count):
                feedback_quota_viol = feedback_count - math.ceil(feedback_ratio_max * strict_count)
        else:
            # if no strict edges, any FEEDBACK is suspicious
            feedback_quota_viol = feedback_count

        # --- density + entropy ---
        density = (E / (N * (N - 1))) if N > 1 else 0.0
        entropy = (-density * math.log(density + 1e-12)) if density > 0 else 0.0

        # --- risk components ---
        cyc_norm = _clamp01(strict_cycle_nodes / max(1, N))
        lv_norm = _clamp01(layer_viol / max(1, E)) if E > 0 else 0.0

        # Quadratic pain beyond max_density
        d_ratio = (density / max_density) if max_density > 0 else 0.0
        d_pen = _clamp01((d_ratio - 1.0) ** 2) if d_ratio > 1.0 else 0.0

        # Base risk
        risk = (0.55 * cyc_norm) + (0.25 * lv_norm) + (0.20 * d_pen)
        risk = _clamp01(risk)

        # --- Risk floors (pain) ---
        # Layer breach must hurt in digits:
        if layer_viol > 0:
            risk_floor = 0.45 + 0.10 * min(4, layer_viol)  # 0.45 .. 0.85
            risk = max(risk, risk_floor)

        # Strict cycle is near-death:
        if strict_cycle_nodes > 0:
            risk = max(risk, 0.85)

        # Deadly pair is near-death:
        if deadly_pairs > 0:
            risk = max(risk, 0.90)

        # Anti-toxin violations also hurt:
        if feedback_cap_viol > 0:
            risk = max(risk, 0.80)
        if feedback_quota_viol > 0:
            risk = max(risk, 0.75)
        if event_cap_viol > 0:
            risk = max(risk, 0.60)
        if event_core_hits > 0:
            risk = max(risk, 0.85)

        # Goals
        goal_failed = self._goal_failed(edges)
        if goal_failed:
            risk = max(risk, 0.80)

        # Verdict
        if strict_cycle_nodes > 0 or deadly_pairs > 0 or event_core_hits > 0:
            verdict = "BLOCK"
        elif risk >= 0.70:
            verdict = "BLOCK"
        elif risk >= 0.45:
            verdict = "WARN"
        else:
            verdict = "ALLOW"

        score = _clamp01(1.0 - risk)
        if goal_failed:
            score *= 0.20

        dna = (
            f"C{min(9, int(_clamp01(cyc_norm) * 9))} "
            f"L{min(9, int(_clamp01(lv_norm) * 9))} "
            f"D{min(9, int(_clamp01(d_pen) * 9))} "
            f"H{min(9, int(_clamp01(entropy) * 9))}"
        )

        return {
            "task_id": self.task["id"],
            "verdict": verdict,
            "risk": round(risk, 3),
            "score": round(score, 3),
            "dna": dna,
            "metrics": {
                "N": N, "E": E,
                "density": round(density, 3),
                "entropy": round(entropy, 3),
                "strict_cycle_nodes": strict_cycle_nodes,
                "layer_viol": layer_viol,
                "deadly_pairs": deadly_pairs,
                "strict_count": strict_count,
                "feedback_count": feedback_count,
                "event_count": event_count,
            },
            "antidote": {
                "feedback_cap_viol": feedback_cap_viol,
                "feedback_quota_viol": feedback_quota_viol,
                "event_cap_viol": event_cap_viol,
                "event_core_hits": event_core_hits,
            },
            "violations": {
                "goal_failed": goal_failed,
            },
        }
