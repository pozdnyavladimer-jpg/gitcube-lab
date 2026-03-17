# GitCube Lab — System Map

GitCube Lab is a structural learning system for software architecture.

It does not treat architecture as plain text.
It treats architecture as:

```text
graph -> risk -> mutation -> memory -> policy -> next action

The system already contains a closed adaptive loop:

structural scoring

repair mutations

transition memory

memory-guided policy

runtime orchestration



---

1. Core Flow

Task
  ↓
Initial Solution
  ↓
GraphEval Scorer
  ↓
Episode / Mutation Loop
  ↓
Best Attempt
  ↓
Transition Memory
  ↓
Crystal / Atom Memory
  ↓
Memory Policy
  ↓
Core / Orchestrator Decision


---

2. High-Level Architecture

apps/grapheval/
    scorer.py
        ↓
agent/gym.py
    ↙           ↘
mutations.py   memory_policy.py
    ↓               ↓
solution edits   action ranking / prediction
    ↘               ↙
      memory/transitions.py
              ↓
      memory/atom.py
      memory/store.py
      memory/crystal_memory.py
      memory/memory_gravity.py
              ↓
agent/core.py
agent/run_core.py
agent/orchestrator.py


---

3. Main Layers

3.1 Geometry Layer

Architecture is represented as a directed typed graph.

Nodes

components

services

adapters

protected/core units


Edges

SYNC_CALL

DATA

FEEDBACK

EVENT


This layer is the spatial form of the system.


---

3.2 Physics Layer

Location:

apps/grapheval/scorer.py

Purpose:

evaluate structural stability

detect architectural danger

convert topology into measurable pressure


Main outputs:

risk

score

verdict

dna

metrics:

density

entropy

strict cycles

layer violations

deadly pairs

feedback/event violations



This is the structural physics engine.


---

3.3 Mutation Layer

Location:

agent/mutations.py
agent/gym.py

Purpose:

generate candidate repairs

attempt local topology improvement

compare candidate states


Current mutation families:

remove forbidden edges

add required edges

remove reverse feedback deadly pairs

trim feedback without capability

reroute feedback via adapter


This layer is the system’s active repair mechanism.


---

3.4 Transition Memory Layer

Location:

memory/transitions.py
memory/transitions.jsonl

Purpose:

record what action was applied

record from-state and to-state

measure improvement via risk delta

accumulate practical structural experience


Transition memory stores:

from_dna
to_dna
from_risk
to_risk
risk_delta
action
task_id
phase transition

This layer stores movement, not only state.


---

3.5 Crystal / Atom Memory Layer

Location:

memory/atom.py
memory/store.py
memory/crystal_memory.py
memory/record_crystal.py
memory/memory_gravity.py

Purpose:

convert reports into stable memory objects

preserve structural attractors

encode symbolic and phase information

allow future gravity-based recall


Stored concepts include:

dna

dna_key

crystal_key

band

phase_state

flower.petal_area

strength

verdict

risk


This layer stores stabilized architectural knowledge.


---

3.6 Memory Policy Layer

Location:

agent/memory_policy.py

Purpose:

inspect transition history

estimate which action family works best

rank candidate mutators

move from passive logging to active guidance


Current role:

action family scoring

success-rate aggregation

risk-gain aggregation

mutator ranking from history

predictive bias by dna_key


This is the first real memory-to-action bridge.


---

3.7 Runtime / Decision Layer

Location:

agent/core.py
agent/run_core.py
agent/orchestrator.py
agent/organs.py
agent/policy.py

Purpose:

interpret structural state

call memory

build runtime recommendation

coordinate roles


Current agents / roles:

scout

critic

memory_agent

builder


This layer produces the final control output.


---

4. Functional Loop

The current adaptive loop is:

1. Build or receive graph task
2. Score current topology
3. Detect structural danger
4. Try candidate mutations
5. Keep only better attempt
6. Record transition
7. Record memory atom / crystal
8. Query memory policy
9. Bias next repair direction
10. Produce final recommendation


---

5. Current Data Objects

5.1 Report

Produced by GraphEval.

Contains:

task_id

verdict

risk

score

dna

metrics

antidote

violations



---

5.2 Attempt

Produced by Gym.

Contains:

step

action

solution

report



---

5.3 Transition

Produced by transition memory.

Contains:

task_id

action

from_report

to_report

risk_delta

optional predicted bias



---

5.4 Memory Atom

Produced from report.

Contains:

kind

verdict

dna

dna_key

band

phase_dir

phase_state

flower

crystal_key

strength



---

5.5 Gravity Guidance

Produced by memory gravity / core.

Contains:

mode_hint

memory_effect

confidence

gravity_mean

gravity_max

attractor_verdict

attractor_band

attractor_phase_state

recommended_bias



---

6. Current Behavioral Capabilities

GitCube Lab can already:

score architecture structurally

detect dangerous topology

try repair actions

compare candidate repairs

remember successful transitions

remember stable states

use memory as policy bias

produce role-based runtime recommendation


This means the system is no longer static analysis only.

It is now:

structural perception + repair + memory-guided behavior


---

7. What Is Already Working

Working now

GraphEval scoring

mutation loop

best-attempt selection

transition logging

atom/crystal memory

gravity-style memory guidance

role-based orchestration

memory-aware mutator ordering


Demonstrated outputs

successful repair of forbidden edge topology

memory bias toward stable attractor

ALLOW state convergence in solvable tasks

final recommendation generation



---

8. Current Limitation

The system still mostly does:

evaluate all candidate mutators
then choose best result

This is strong, but not yet full memory control.

Memory currently influences:

order

bias

recommendation


Memory does not yet fully choose:

direct single-step action without broad evaluation

long-horizon policy

generalized cross-task strategy



---

9. Next Evolution Stages

Stage 1 — Active Memory Control

Memory predicts which action family should be tried first for the current dna_key.

state -> predicted action -> mutation -> score

Stage 2 — Learned Repair Policy

System accumulates statistics across many tasks and begins selecting actions directly.

state class -> best historical action -> execute

Stage 3 — Attractor Navigation

System no longer thinks in isolated actions only, but in drift toward stable structural basins.

current state -> nearest attractor -> guided repair path

Stage 4 — General Structural Cognition

System learns architectural laws, not only examples.

local repair -> abstract rule -> reusable policy


---

10. Conceptual Identity

GitCube Lab is not just:

a linter

a benchmark

a rule engine

a memory log


It is becoming:

a structural cognition system for software architecture

Its operating principle is:

topology -> pressure -> mutation -> retention -> guidance -> stability


---

11. Minimal Repository Map

gitcube-lab/

apps/
  grapheval/
    scorer.py

agent/
  core.py
  run_core.py
  gym.py
  mutations.py
  memory_policy.py
  orchestrator.py
  organs.py
  policy.py

memory/
  atom.py
  store.py
  crystal_memory.py
  record_crystal.py
  memory_gravity.py
  transitions.py
  memory.jsonl
  transitions.jsonl

reports/
traces/
README.md
SYSTEM_MAP.md


---

12. One-Sentence Summary

GitCube Lab is a memory-guided structural repair engine that evaluates graph topology, learns from repair transitions, stores stable states as crystals, and moves future architectural decisions toward known attractors.
