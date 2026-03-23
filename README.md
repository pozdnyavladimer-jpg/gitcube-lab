# GitCube Lab

GitCube Lab is a research environment for architecture-level reasoning over software systems.

It models code as a dependency graph, measures structural instability as risk, and trains agents to repair unsafe architectures.

---

👉 Control layer (GSL):
https://github.com/pozdnyavladimer-jpg/geometric-state-navigator

GSL builds on top of GitCube and uses these structural signals to regulate decisions.

---

## What this repo is

This is not a single tool.

This is a **research environment** that includes:

- graph-based architecture analysis  
- structural risk modeling  
- agent-based repair (Graph School)  
- topological memory  

---

## What this repo is NOT

- not a code generator  
- not a linter  
- not a static analyzer  

It operates at the **architecture topology level**.

---

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
Location:
memory/

---

## Resonance / Adaptive Memory Layer

Higher-order adaptive memory layer that goes beyond static scoring.

Combines:

- hexagram-based state encoding  
- ring-weighted memory  
- adaptive exploration  
- self-rewrite behavior control  

📄 Documentation:  
docs/RESONANCE_MEMORY.md

---

## Quickstart

Clone repository:

```bash
git clone https://github.com/pozdnyavladimer-jpg/gitcube-lab.git
cd gitcube-lab
```
Verify environment:
PYTHONPATH=. python -c "import apps.grapheval; print('OK')"
Run GraphEval:
PYTHONPATH=. python -m apps.grapheval.runner
Run benchmark:
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
docs/RESONANCE_MEMORY.md
docs/MAP.md
docs/NOW.md
# GitCube Lab

GitCube Lab is the experimental layer of the system.

It generates ideas.

It does not define truth.

---

## 🧪 What Lab does

- explores new agents  
- experiments with metrics  
- tests environments  
- creates candidate logic  
- produces new patterns  

---

## ⚠️ Important Rule

Lab is not runtime.

Nothing from Lab goes directly into OS.

Everything must pass through Navigator.

---

## 🔁 Promotion Flow

1. Lab generates idea  
2. Navigator interprets and formalizes  
3. OS executes and validates  

Only what survives runtime becomes canonical.

---

## 🧠 Example Outputs

- new agent behaviors  
- alternative scoring systems  
- experimental environments  
- state representations  

---

## 🔗 System Architecture

GitCube Lab is part of a 3-layer system:

- GitCube Lab → exploration (this repo)  
- Geometry Navigator → canonical meaning  
- GitCube OS → runtime execution  

Flow:

Lab → Navigator → OS  

---

## ⚡ One-line

Lab explores possibilities. It does not decide what is real.
