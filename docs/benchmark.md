# Graph School Benchmark

## What is Graph School?

Graph School is a benchmark and training environment for **architecture reasoning** in AI systems.

Instead of evaluating models only on code generation or bug fixing, Graph School evaluates whether an agent can:

- read a software topology as a graph
- detect structural risk
- repair unsafe graph patterns
- satisfy task constraints
- converge toward a stable architecture

In short:

```
task → graph → score → repair → benchmark
```

---

# Motivation

Modern AI systems can generate code, but they often do not understand **macro-architecture**.

They may produce:

- cycles
- layer violations
- density overload
- unsafe feedback channels
- hidden coupling growth

Graph School exists to test whether an AI system can move from:

```
code completion
```

to:

```
architecture reasoning
```

---

# Core idea

A task defines:

- nodes
- layers
- constraints
- goals

An agent proposes a graph topology.

GraphEval scores that topology using structural risk physics:

- cycles
- layer violations
- density
- anti-toxin rules
- goal satisfaction

If the result is risky, the repair environment applies mutations and searches for a safer topology.

This creates a full loop:

```
task
→ initial solution
→ GraphEval
→ mutation-based repair
→ best topology
→ benchmark metrics
```

---

# Why this benchmark is different

Most AI benchmarks measure:

- correctness of answers
- code generation quality
- test pass rate
- factual knowledge

Graph School measures something else:

```
structural stability
```

The benchmark asks:

- Can the model build a safe topology?
- Can it detect dangerous graph patterns?
- Can it repair a blocked architecture?
- Can it satisfy constraints without creating new structural debt?

This makes Graph School closer to:

- planning
- control
- systems design
- architecture optimization

than to ordinary coding benchmarks.

---

# Benchmark structure

Each benchmark item contains:

- `id`
- `title`
- `nodes`
- `constraints`
- `goal`

Example task:

```json
{
  "id": "task_001",
  "title": "Add cache without breaking layers",
  "nodes": [
    {"id": "UI", "layer": 1},
    {"id": "Service", "layer": 2},
    {"id": "DB", "layer": 3},
    {"id": "Cache", "layer": 3}
  ],
  "constraints": {
    "allowed_layer_diff": [0, 1],
    "max_density": 0.40
  },
  "goal": {
    "must_have_edges": [["Service", "Cache", "DATA"]],
    "must_not_have_edges": [["UI", "Cache", "SYNC_CALL"]]
  }
}
```

Agent solution example:

```json
{
  "id": "task_001",
  "edges": [
    ["UI", "Service", "SYNC_CALL"],
    ["Service", "DB", "DATA"],
    ["Service", "Cache", "DATA"]
  ]
}
```

---

# Evaluation engine

Graph School uses:

```
apps/grapheval/scorer.py
```

as the structural risk engine.

The scorer evaluates:

### 1. Strict cycles

Cycles over strict edges are near-fatal and usually lead to `BLOCK`.

### 2. Layer violations

Edges that break allowed layer flow increase structural risk.

### 3. Density overload

Excessive edge density causes architectural pressure.

### 4. Anti-toxin rules

Special guards prevent unsafe patterns:

- illegal FEEDBACK
- FEEDBACK without capability
- deadly pairs (`SYNC_CALL A→B` + `FEEDBACK B→A`)
- unsafe EVENT routing

### 5. Goal satisfaction

Tasks may require or forbid specific edges.

---

# Structural DNA

Every evaluated graph produces a compact structural signature:

```
Cx Lx Dx Hx
```

Current DNA dimensions represent:

- `C` — cycle pressure
- `L` — layer violation pressure
- `D` — density penalty
- `H` — entropy proxy

This DNA is a compact symbolic state of the architecture.

---

# Repair environment

Graph School includes a mutation-based repair loop.

Possible mutations:

- remove forbidden edges
- add required edges
- remove deadly feedback pairs
- trim illegal feedback
- reduce unsafe density

General loop:

```
graph
→ mutate
→ rescore
→ keep best improvement
```

This makes Graph School both:

- a benchmark
- a training environment.

---

# Benchmark metrics

### Pass@1
Agent produces an `ALLOW` topology immediately.

### Pass@3
Agent reaches `ALLOW` within 3 repair steps.

### Pass@6
Agent reaches `ALLOW` within 6 repair steps.

### Mean initial score
Average score of the first proposed topology.

### Mean best score
Average best score after repair.

### Repair gain
Difference between best score and initial score.

### Block escape rate
How often the agent escapes `BLOCK`.

### Goal satisfaction rate
How often task goals are satisfied.

### Hard failures
Tasks that remain `BLOCK`.

---

# Example benchmark report

```json
{
  "benchmark": "Graph School v0.1",
  "tasks": 10,
  "pass_at_1": 0.7,
  "pass_at_3": 0.8,
  "pass_at_6": 0.9,
  "mean_initial_score": 0.61,
  "mean_best_score": 0.84,
  "repair_gain_mean": 0.23,
  "block_escape_rate": 0.67,
  "goal_satisfaction_rate": 0.9,
  "hard_failures": ["task_010"]
}
```

---

# Difficulty levels

### Easy
Single structural issue.

### Medium
Multiple interacting risks.

### Hard
Multi-step topology reasoning.

---

# Agent types

Graph School can compare:

- random mutator
- greedy repair agent
- rule-based agent
- LLM guided agent
- memory-aware agent

---

# Graph School as Architecture Gym

Mapping to reinforcement learning:

| RL concept | Graph School |
|---|---|
| state | graph / Structural DNA |
| action | mutation |
| reward | score improvement |
| episode | repair loop |
| memory | structural atoms |

---

# Long-term vision

Graph School is not only a benchmark.

It is the educational layer of **GitCube Lab**.

Pipeline:

```
task
→ graph
→ structural risk
→ repair loop
→ benchmark
→ memory
→ policy
→ architecture-aware agent
```

---

# Summary

Graph School evaluates whether AI can:

- understand topology
- detect instability
- repair unsafe architectures
- satisfy constraints
- converge to stable system design

In one line:

```
Graph School tests whether AI can think like an architect, not only code like a programmer.
```
