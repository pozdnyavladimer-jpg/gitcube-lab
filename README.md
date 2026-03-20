# GitCube Lab

GitCube Lab is a research environment for architecture-level AI reasoning.

It helps agents detect structural instability in software systems, repair unsafe dependency graphs, and accumulate architectural memory over time.

---

## Core Problem

Modern AI systems can generate code, but they rarely understand **architecture stability**.

They optimize locally:

- functions
- classes
- files

But real software often fails at the **topology level**.

Typical failures include:

- dependency cycles
- layer violations
- hidden feedback loops
- explosive coupling
- uncontrolled graph density

These issues may not appear in unit tests or linters.
They emerge when the **graph structure itself becomes unstable**.

---

## Core Idea

GitCube treats software architecture as a **physical graph system**.

Instead of reasoning only about tokens or files, it reasons about:

- nodes = components
- edges = dependencies
- topology = architecture structure

This allows architectural instability to be measured as structural risk.

---

## System Loop

Architecture
→ Dependency Graph
→ GraphEval
→ Structural Risk
→ WARN / BLOCK
→ Graph School
→ Mutation / Repair
→ Memory
→ Swarm Orchestrator

---

## Main Components

### GraphEval
Structural risk engine for architecture graphs.

Detects:

- cycles
- layer violations
- SCC expansion
- dependency density
- architectural entropy

Location:
`apps/grapheval/`

---

### Graph School
Environment where agents learn to repair unstable architecture graphs.

Loop:
graph → mutate → rescore → keep improvement

Location:
`agent/`

Benchmark:
`python -m agent.benchmark`

---

### Topological Memory
Stores architecture states as reusable memory atoms.

Example:

```json
{
  "dna": "G1 P1 C1",
  "risk": 0.61,
  "verdict": "WARN"
}
```
Location: memory/
Resonance / Adaptive Memory Layer
Higher-order adaptive memory layer that goes beyond static scoring.
Combines:
hexagram-based state encoding
ring-weighted memory
adaptive exploration
self-rewrite behavior control
Documentation: docs/RESONANCE_MEMORY.md
Quickstart
Clone repository:
git clone https://github.com/pozdnyavladimer-jpg/gitcube-lab.git
cd gitcube-lab
Verify environment:
PYTHONPATH=. python -c "import apps.grapheval; print('OK')"
Run GraphEval:
PYTHONPATH=. python -m agent.benchmark
Repository Navigation
Core
apps/
agent/
memory/
kernel/
Learning / Graph School
graph_school/
lessons/
rubrics/
Experiments / Simulation
simulator/
traces/
reports/
Documentation
ARCHITECTURE.md
SYSTEM_MAP.md
docs/graph_school_benchmark.md
docs/RESONANCE_MEMORY.md
docs/NOW.md
docs/MAP.md
Conceptual Model
GitCube can also be read as a geometric architecture model:
Flower → architecture state space
Sri → attractor field of stable design
GraphEval → structural energy / risk
Together these components turn architecture into a navigable topology landscape.
Vision
GitCube aims to train AI systems that can:
understand architecture topology
detect structural risk
repair unstable graph designs
accumulate architectural knowledge
In short:
GitCube teaches AI to think like a software architect.
