# GitCube Lab
### Structural DNA for Software Architecture

Most pull requests look harmless.

But some of them silently break the topology of your system.

GitCube compresses a repository’s dependency graph into an 8-symbol Structural DNA string.

Instead of reading code,
we read structure.

---

## What is Structural DNA?

Every repository becomes a graph:

G = (V, E)

We measure its structural invariants and encode them as:

C L D S H E P M

Example:

C1 H1 S0 D1 L0 E0 P1 M0

This is a WARN state.
Not a block. Not a panic.
But structural pressure is rising.

---

## The 8 Symbols

| Symbol | Meaning |
|--------|----------|
| C | Cycles / SCC risk |
| L | Layer violations |
| D | Dependency density |
| S | Structural drift |
| H | Structural entropy |
| E | Entropy lead (early signal) |
| P | Architectural pressure |
| M | Critical state (Meru Gate → BLOCK) |

---

## Verdict Logic

ALLOW  → all metrics stable  
WARN   → structural pressure detected  
BLOCK  → critical topology violation  

BLOCK is rare.
WARN is normal evolution.
Chaos is fuel — not an enemy.

---

## Example

PR diff:
```diff
+ payments.api -> core.db
