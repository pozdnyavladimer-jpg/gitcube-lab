# Graph School

Graph School is the **benchmark and training environment** inside GitCube Lab.

It is designed to evaluate whether AI agents can **reason about software architecture as graph topology**.

Instead of testing code generation, Graph School tests:

- architecture stability
- topology repair
- structural reasoning
- constraint satisfaction

In short:

task → graph → score → repair → benchmark

---

# Purpose

Modern AI systems can generate code, but they often fail at **architecture-level reasoning**.

Common failures include:

- dependency cycles
- layer violations
- unsafe feedback loops
- hidden coupling
- density explosions

Graph School evaluates whether an agent can detect and repair these structural risks.

---

# Where tasks live

Current task dataset:

datasets/grapheval/tasks/

These JSON files define architectural problems that agents must solve.

Example tasks include:

- breaking dependency cycles
- restoring layer boundaries
- reducing graph density
- satisfying must-have edges
- avoiding forbidden edges

---

# Benchmark Loop

The canonical evaluation loop is:

task  
↓  
agent proposes graph  
↓  
GraphEval scores topology  
↓  
if risky → repair loop  
↓  
best topology  
↓  
benchmark metrics

GraphEval is implemented in:

apps/grapheval/scorer.py

---

# Running the Benchmark

The current benchmark runner is:

agent/benchmark.py

Run it with:

python -m agent.benchmark

The benchmark loads tasks, evaluates agent proposals, and produces a report.

Output report:

reports/benchmark_report.json

---

# Metrics

Graph School uses the following metrics:

pass_at_1  
pass_at_3  
pass_at_6  

mean_initial_score  
mean_best_score  

repair_gain_mean  

block_escape_rate  

goal_satisfaction_rate  

hard_failures  

These metrics evaluate whether an agent can **improve unsafe architecture graphs**.

---

# Difficulty Levels

Tasks can be grouped into three levels.

### Easy

Single structural issue:

- one cycle
- one layer violation
- one forbidden edge

### Medium

Multiple interacting risks:

- cycle + layering
- feedback + capability
- density + goal constraints

### Hard

Multi-step repair problems:

- fix one risk without creating another
- satisfy goals while preserving topology
- several repair steps required

---

# Baseline Agents

Graph School compares multiple agent strategies.

Baseline agents include:

Random Mutator  
Greedy Repair Agent  
Rule-Based Repairer  

Future agents may include:

LLM-guided topology agents  
Memory-aware agents

---

# Architecture Gym

Graph School behaves like a **reinforcement-style environment**.

Mapping:

state → graph / structural DNA  
action → mutation  
reward → score improvement  
episode → repair loop  
memory → structural atoms

This allows experimentation with different reasoning systems.

---

# Relationship to GitCube

Graph School is built on top of the GitCube core stack.

GitCube layers:

GraphEval → structural risk engine  
Graph School → repair and training environment  
Crystal Memory → storage of structural states  
Swarm Runtime → agent orchestration

Together these form a system for **architecture-aware AI agents**.

---
# Conceptual Model

Graph School can be understood through two complementary geometric models.

Flower of Life → Reference Lattice

This represents the discrete state space of possible architectures.  
Every valid architecture is a point in this lattice.

Sri Yantra → Attractor Field

This represents the dynamic navigation field guiding agents toward stable architectures.

Agents do not search randomly.  
They move along structural pressure gradients toward lower-risk configurations.

GraphEval measures the structural deviation between the current topology and a stable attractor state.

In simplified terms:

Lattice → possible states  
Attractor → direction of improvement  
GraphEval → distance to stability

This framing allows Graph School to function not only as a benchmark, but also as an architecture navigation system.
# Long-Term Vision

Graph School aims to become a benchmark for **AI architecture reasoning**.

Future AI systems will not only generate code but also design stable system topologies.

Graph School provides the environment to test and train that capability.
