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
# Architecture Pain

Modern AI systems can generate code, but they rarely understand **architecture stability**.

Large language models optimize locally:

- functions
- classes
- files

But software systems fail at the **topology level**.

Typical architectural failures include:

- dependency cycles
- layer violations
- hidden feedback loops
- explosive coupling
- uncontrolled graph density

These failures often do not appear in unit tests or static linters.

They emerge only when the **system topology becomes unstable**.

---

## Why LLMs struggle with architecture

Most AI systems operate on **token probability**.

They are optimized to produce:
syntactically correct locally coherent test-passing code
But architecture stability depends on **global graph structure**.

For example:
A → B B → C C → A
This creates a cycle.

The code may compile.
Tests may pass.

But the architecture becomes **structurally unstable**.

LLMs do not naturally perceive this type of risk.

---
Conceptual Model
GitCube can also be understood through a geometric model of architectural space.
Flower of Life — Reference Lattice
The Flower represents the discrete space of possible architectures.
Each node in this lattice corresponds to a possible system topology.
Agents move through this space by applying structural mutations.
Sri Yantra — Attractor Field
The Sri Yantra represents the attractor field of stable architecture.
Instead of searching randomly, agents move along structural gradients toward lower-risk configurations.
GraphEval — Structural Energy
GraphEval measures the structural deviation between the current architecture and a stable attractor state.
This converts architecture stability into a continuous energy function:
E(topology) → risk ∈ [0..1]
In simplified terms:
Flower → architecture state space
Sri → navigation field
GraphEval → structural energy
Together these components transform architecture design into a navigable topology landscape.

## Architecture as a physical system

GitCube approaches software architecture as a **physical topology**.

Instead of reasoning about text, GitCube reasons about **graphs**.
nodes  = system components edges  = dependency relations topology = architecture structure
Structural invariants define system stability.

Examples:

- cycle pressure
- SCC expansion
- dependency density
- layer flow violations

These invariants are converted into a **continuous risk value**:
risk ∈ [0..1]
and a discrete verdict:
ALLOW WARN BLOCK
---

## Introducing Architectural Pain

GitCube introduces **numerical consequences** for structural mistakes.

Architectural errors produce measurable pressure:
cycle → critical risk layer breach → elevated risk dense mesh → quadratic penalty
This creates something missing in current AI systems:
architecture pain
Agents can now **feel when architecture becomes unstable**.

---

## From Code Generation to Architecture Reasoning

GitCube aims to shift AI development from:
code completion
to:
architecture reasoning
Instead of only writing code, agents must learn to:

- detect structural instability
- repair graph topology
- preserve architectural invariants
- converge to stable system design

Graph School is the environment where agents learn this behavior.

---

In short:

**GitCube teaches AI to feel architectural pain before systems collapse.**
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
