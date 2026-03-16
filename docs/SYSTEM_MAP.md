

GitCube Lab — System Map

GitCube Lab is a structural reasoning system for software architecture.

Instead of treating software as text, GitCube models systems as graph topologies and evaluates their structural stability through a closed reasoning loop.

The system learns over time by evaluating architectures, repairing them, storing structural states, and using memory to guide future decisions.


---

System Overview

The core reasoning loop of GitCube is:

STATE
↓
STRUCTURAL EVALUATION
↓
SYMBOLIC STATE (DNA)
↓
REPAIR ATTEMPTS
↓
MEMORY STORAGE
↓
MEMORY GRAVITY
↓
CONTROL DECISION
↓
NEW STATE

This creates a closed-loop architecture reasoning system.


---

System Layers

GitCube consists of several cooperating layers.

INPUT → GRAPH → PHYSICS → SYMBOL → REPAIR → MEMORY → CONTROL

Each layer transforms the architecture representation.


---

1. Input Layer

Initial tasks and architecture descriptions.

Location:

datasets/grapheval/tasks/
apps/graph_ai/

Purpose:

define architecture tasks

generate initial graphs

create experiment scenarios


Example sources:

datasets/grapheval/tasks/
apps/graph_ai/generator.py
apps/graph_ai/pipeline_bridge.py


---

2. Graph Representation Layer

Converts architecture into a formal graph structure.

Location:

apps/grapheval/schema.py
apps/graph_school/env.py
apps/graph_school/sim_10_arch.py

Responsibilities:

represent modules as nodes

represent dependencies as edges

enforce graph schema


Output:

graph topology


---

3. Structural Physics Layer

Evaluates the safety of the architecture.

Location:

apps/grapheval/scorer.py
apps/grapheval/runner.py

Detects:

cycles

layer violations

density overload

unsafe feedback channels

structural entropy


Output:

risk ∈ [0..1]
verdict ∈ {ALLOW, WARN, BLOCK}
dna representation

This layer acts as the physics engine of architecture.


---

4. Symbolic State Layer

Converts metrics into symbolic structural states.

Example encoding:

Cx Lx Dx Hx

Or extended state vectors.

Fields include:

dna
dna_key
band
phase_state
flower invariant

Purpose:

compress architecture condition

enable symbolic reasoning

enable memory indexing



---

5. Repair Environment (Graph School)

GitCube can attempt to repair unsafe architectures.

Location:

agent/

Main components:

agent/gym.py
agent/mutations.py
agent/train.py
agent/benchmark.py

Repair loop:

graph
↓
mutation
↓
rescore
↓
accept improvement

Possible actions:

remove edges

add edges

split modules

remove feedback loops

reduce density


This environment acts as a training school for architecture repair agents.


---

6. Memory Layer

Stores structural states as Memory Atoms.

Location:

memory/

Main components:

memory/atom.py
memory/store.py
memory/crystal_memory.py
memory/record_crystal.py
memory/flower.py

Example memory atom:

{
  "dna": "C0 L0 D1",
  "risk": 0.64,
  "verdict": "WARN",
  "band": 3
}

Memory stores:

structural patterns

repair outcomes

architecture states


These records form compressed architectural experience.


---

7. Memory Field (Gravity)

Memory is not only storage.
It forms a navigation field for the system.

Location:

memory/memory_gravity.py
agent/gravity_agent.py

Responsibilities:

similarity detection
↓
attractor ranking
↓
guidance vector

The system computes:

structural similarity

attraction toward stable states

repulsion from dangerous states


Output example:

gravity_mean
gravity_max
confidence

This creates a memory-driven attractor field.


---

8. Control Plane

Coordinates reasoning agents and decision making.

Location:

agent/

Main modules:

agent/policy.py
agent/orchestrator.py
agent/organs.py
agent/schema.py
agent/pipeline.py
agent/gravity_agent.py

Responsibilities:

interpret structural risk

interpret memory signals

choose repair strategy

select system mode


Example policy modes:

DIRECT
CAUTIOUS
SANDBOXED
BLOCKED

The control plane acts as the decision layer of the system.


---

9. Observation Layer

Stores traces and experiment results.

Locations:

traces/
reports/
docs/

Examples:

traces/train_traces.jsonl
reports/benchmark_report.json

Purpose:

analyze system behavior

evaluate agents

track learning progress



---

10. Research Layer

Experimental components and future directions.

Examples:

kuramoto13.py
teleport.py
simulator/
hfs/

Research topics:

oscillator models

resonance systems

attractor dynamics

spatial system navigation


This layer connects GitCube with the broader V-Kernel research direction.


---

Repository Structure

Example simplified structure:

gitcube-lab/

README.md
ARCHITECTURE.md

apps/
    grapheval/

agent/
    gym.py
    mutations.py
    train.py
    benchmark.py
    orchestrator.py
    policy.py
    gravity_agent.py

memory/
    atom.py
    store.py
    crystal_memory.py
    memory_gravity.py

datasets/
    grapheval/
        tasks/

docs/
    SYSTEM_MAP.md


---

Conceptual Model

GitCube can be understood as a layered reasoning system.

Input Layer
    tasks / architecture

Geometry Layer
    graph topology

Physics Layer
    structural risk

Symbol Layer
    structural DNA

Dynamics Layer
    repair environment

Memory Layer
    crystal memory atoms

Navigation Layer
    memory gravity field

Control Layer
    policy + orchestrator


---

Core Idea

GitCube teaches AI systems to reason about architecture, not just generate code.

It provides:

graph-based system perception

structural risk physics

architecture repair environments

memory of architectural states

policy-aware decision control


In simple terms:

GitCube teaches AI to think like an architect.


---
