# Resonance Memory Layer

## Overview

The Resonance Memory Layer is a higher-order adaptive control system built on top of the base graph scoring engine.

Unlike a static rule-based evaluator, this layer stores experience, weighs it by structural depth, and dynamically adjusts exploration and action routing.

It is designed to answer one core question:

> How can a system remember not only what worked, but how deeply aligned that solution was?

---

## Core Idea

The system does not treat all successful actions equally.

Each experience is evaluated through:

- **Hexagram state** — a 6-dimensional signal:
  - red_mass
  - orange_flow
  - yellow_struct
  - green_balance
  - blue_law
  - violet_future

- **Ring depth** — structural depth of the state:
  - ring 14 → raw/noisy state
  - ring 10a → structural stabilization
  - ring 10b → behavioral stabilization
  - ring 8 → core-aligned state

- **Self-rewrite dynamics** — adaptive adjustment of:
  - exploration bias
  - repeat penalty strength
  - ring pressure

---

## Main Components

### 1. Experience Memory

Stored in:

```text
memory/experience_store.jsonl
```
Each record includes:
action
before_hex
after_hex
before_dna
after_dna
ring layer
score gain
risk drop
This allows the controller to compare current state with prior successful transitions.
2. Hexagram Representation
The state is represented as a six-axis vector:
W = [R, O, Y, G, B, V]
Where:
R = mass / overload
O = flow / movement
Y = structural rigidity
G = balance / healing
B = law / order
V = future / extensibility
This vector acts as a resonance signature.
3. Ring Gravity
Not all experience has equal authority.
The inner the ring, the stronger the signal.
Base weights:
ring 14 → 1.0
ring 10a → 1.4
ring 10b → 1.8
ring 8 → 4.5
This creates a gravity field that pulls decision-making toward structurally deeper states.
4. Diversity Discipline
The system avoids collapsing into one dominant action forever.
It uses:
repeat penalty
dominant vote softening
forced exploration
stochastic top-k choice
This prevents local minima and premature convergence.
5. Self-Rewrite
The system rewrites its own behavioral parameters based on recent history.
Tracked parameters:
explore_bias
repeat_penalty_strength
ring_pressure
This makes exploration adaptive rather than fixed.
Control Flow
score → hexagram → memory lookup → weighted voting
→ exploration discipline → action selection → experience update
→ self-rewrite adaptation
Exploration Modes
The controller exposes explicit exploration reasons:
none
forced_early
forced_repeat
random
Meaning:
forced_early — low-history phase, system intentionally avoids deterministic lock-in
forced_repeat — same action repeated too often, system breaks pattern
random — probabilistic exploration under confidence/temperature control
Why This Layer Exists
A normal controller answers:
What is the best action right now?
The Resonance Memory Layer answers:
What action is most aligned with long-term structural truth, while still allowing adaptation?
This is the difference between:
static optimization
and self-balancing adaptive behavior
Practical Effect
This layer makes the system capable of:
remembering successful transitions
preferring deeper, more stable states
avoiding repetitive action loops
adjusting its own exploration strategy
evolving behavior under changing context
Suggested Entry Points
Main files:
agent/integrated_controller.py
agent/monk_discipline.py
agent/self_rewrite.py
memory/experience_matrix.py
memory/atom.py
Short Summary
The Resonance Memory Layer turns the project from:
rule-based scorer
into:
adaptive resonance-driven control system
