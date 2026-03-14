# GitCube Lab

Structural Risk Control, Topological Memory & Graph Architecture Benchmark.

GitCube Lab is an experimental system for **architecture reasoning using graph topology**.

Instead of analyzing code line-by-line, GitCube treats software systems as **graphs** and evaluates their structural stability.

---

# TL;DR

GitCube turns architecture into a physical model:

```
graph topology
→ structural DNA
→ risk score (0..1)
→ ALLOW / WARN / BLOCK
→ repair loop
→ benchmark metrics
→ structural memory
```

The goal is to train AI agents that can **detect and repair architectural instability**.

---

# System Map

```
Architecture
      │
      ▼
Dependency Graph
      │
      ▼
GraphEval
Structural Risk Engine
      │
      ▼
risk ∈ [0..1]
      │
 ┌────┴─────┐
 ▼          ▼
ALLOW     WARN/BLOCK
             │
             ▼
        Graph School
      mutation repair
             │
             ▼
        Crystal Memory
             │
             ▼
       Swarm Orchestrator
```

---

# Core Components

## GraphEval — Structural Risk Engine

Location:

```
apps/grapheval/
```

Responsible for detecting:

- dependency cycles
- layer violations
- structural density
- SCC expansion
- architectural entropy

Output:

```
risk score
ALLOW / WARN / BLOCK
```

---

## Graph School — Architecture Repair Benchmark

Location:

```
agent/
```

Graph School trains agents to repair unsafe architecture graphs.

Loop:

```
graph
→ mutate
→ rescore
→ keep improvement
```

Benchmark runner:

```
python -m agent.benchmark
```

Dataset:

```
datasets/grapheval/tasks/
```

---

## Topological Memory

Location:

```
memory/
```

Stores architecture states as **MemoryAtoms**.

Example:

```
{
  "dna": "G1 P1 C1",
  "risk": 0.61,
  "verdict": "WARN"
}
```

This allows GitCube to accumulate **structural experience over time**.

---

# Quickstart

Clone repository:

```
git clone https://github.com/pozdnyavladimer-jpg/gitcube-lab.git
cd gitcube-lab
```

Verify environment:

```
PYTHONPATH=. python -c "import apps.grapheval; print('OK')"
```

Run GraphEval:

```
PYTHONPATH=. python -m apps.grapheval.runner
```

Run benchmark:

```
PYTHONPATH=. python -m agent.benchmark
```

---

# Documentation

Additional documentation:

```
ARCHITECTURE.md
SYSTEM_MAP.md
docs/graph_school_benchmark.md
```

Useful navigation files:

```
docs/NOW.md
docs/MAP.md
docs/HISTORY.md
docs/IDEAS_INBOX.md
```

---

# Vision

Modern AI can write code but often fails at **architecture-level reasoning**.

GitCube aims to train AI systems that can:

- understand architecture topology
- detect structural risk
- repair unstable designs
- accumulate architectural knowledge

In short:

**GitCube teaches AI to think like a software architect.**
