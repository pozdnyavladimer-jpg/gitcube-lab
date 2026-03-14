# MAP

High level map of the GitCube Lab repository.

This file explains what each subsystem is responsible for.

---

# apps/grapheval

Main structural risk engine.

Evaluates graphs as architectural systems.

Measures:

cycles  
layer violations  
density  
entropy

Produces:

risk score  
verdict (ALLOW / WARN / BLOCK)  
DNA signature

---

# apps/graph_school

Architecture learning environment.

Contains:

policy grammars  
demo architectures  
training cases

Used to teach the system what different architectural styles look like.

Examples:

layered architecture  
clean/onion architecture  
hexagonal architecture  
microservices  
event-driven systems

---

# apps/graph_ai

Bridge between language models and architecture graphs.

Pipeline:

prompt  
→ graph generator  
→ structural evaluation  
→ auto repair

Future direction:

LLM produces candidate architectures
Graph engine validates them.

---

# agent

Agent runtime.

Responsible for:

mutation operators  
repair episodes  
policy control  
benchmark evaluation

This layer performs structural improvement.

---

# memory

Long term structural memory.

Stores:

architecture atoms  
evaluation traces  
cycle dynamics

Includes:

flower invariant (trajectory shape in risk space)

Memory helps the system learn structural reflexes.

---

# simulator

Experimental dynamics.

Contains research ideas such as:

phase transitions  
three-body control  
topology dynamics

This is a research sandbox.

---

# hfs

Human feedback experiments.

Collects human evaluation signals for architectural decisions.

---

# Summary

GitCube Lab consists of:

Graph evaluation  
Repair agents  
Structural memory  
Human interaction loop

Together these form an architecture reasoning system.
