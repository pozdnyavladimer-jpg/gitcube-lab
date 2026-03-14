# NOW

Current state of GitCube Lab.

This file is the quick orientation point if the developer returns after a long break
or after switching devices.

---

# Core system (main focus)

These modules form the core architecture reasoning engine.

apps/grapheval  
agent/  
memory/

Core idea:

task
→ graph
→ structural risk evaluation
→ repair loop
→ memory atom
→ meta policy
→ orchestrated result

The goal is a system that can evaluate, repair and remember architectural structures.

---

# Secondary layers

These modules support experimentation or earlier stages of the system.

apps/graph_school  
apps/graph_ai  
simulator  
hfs

graph_school = architecture grammar learning  
graph_ai = prompt → graph → evaluate → repair loop  
simulator = experimental dynamics  
hfs = human feedback experiments

---

# Current priority

Do NOT expand new modules.

Focus on closing the main loop:

graph
→ evaluate
→ repair
→ memory
→ policy

---

# Long-term direction

Architecture reasoning engine that works with humans:

Human intent  
↓  
Graph generation  
↓  
Structural evaluation  
↓  
Agent repair loop  
↓  
Memory accumulation  
↓  
Policy learning

This is the path toward human-AI architectural symbiosis.
