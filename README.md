# GitCube Lab
**Structural Risk Control & Topological Memory Engine**

GitCube Lab is an experimental structural control system that converts topology into measurable risk and discrete machine decisions.

It operates on:

- Software architecture graphs (Structural DNA)
- Human interaction streams (HFS — Human Function Stream)

This is not NLP.  
This is not sentiment analysis.  
This is structural instability modeling.

---

# TL;DR

GitCube:

1. Extracts structural invariants  
2. Aggregates them into continuous risk (0..1)  
3. Computes adaptive thresholds (μ + kσ)  
4. Produces ALLOW / WARN / BLOCK  
5. Persists compact structural records (Memory Atoms)  
6. Detects recurring structural states (Crystal Keys)  
7. Applies Meta-Control (threshold tightening)  

Continuous inside.  
Discrete outside.  
Memory across time.

---

# Core Architecture

## 1. Structural DNA (Graph Layer)

Any repository can be represented as:

G = (V, E)

Where:
- V — modules/files  
- E — dependencies  

GitCube compresses structural invariants into an 8-symbol signature:

C L D S H E P M  

Example:

DNA: C1 L0 D2 S1 H0 E1 P1 M0  

| Symbol | Meaning |
|--------|----------|
| C | Cycles / SCC risk |
| L | Layer violations |
| D | Dependency density |
| S | Structural drift |
| H | Structural entropy |
| E | Entropy lead |
| P | Architectural pressure |
| M | Critical gate |

Structural DNA encodes topology — not semantics.

---

## 2. HFS — Human Function Stream (Cognitive Layer)

HFS models structural volatility in interaction streams.

Signature:

T R P S C F W M  

| Symbol | Meaning |
|--------|----------|
| T | Topic drift |
| R | Rewrite rate |
| P | Pressure spike |
| S | Stability gain |
| C | Contradiction rate |
| F | Focus lock |
| W | Warn activation |
| M | Meltdown gate |

Output:
- DNA signature  
- Continuous risk  
- Discrete verdict  

No semantic interpretation. Only structure.

---

# Risk Model

Risk ∈ [0,1]

Adaptive baseline per system:

warn_threshold = μ + 2σ  
block_threshold = μ + 3σ  

Decision logic:

risk ≤ warn_threshold → ALLOW  
warn_threshold < risk ≤ block_threshold → WARN  
risk > block_threshold → BLOCK  

BLOCK is rare.  
WARN is normal evolution.  
Noise is measured — not punished.

---

# Memory Atoms (Topological Memory)

Instead of storing raw logs, GitCube stores structural invariants:

- verdict  
- DNA  
- baseline (μ, σ)  
- thresholds  
- risk  
- phase band  
- flower geometry (petal_area)  
- crystal_key  

Atoms are stored as JSONL records.

---

# Crystal Keys (Recurring Structural States)

Each Memory Atom generates a crystal_key:

kind + DNA  

Example:

HFS_NAVIGATOR_REPORT:T1 R3 S1  

The system aggregates:

- strength (occurrence count)  
- flower_area_sum  
- last_seen  

This enables structural recurrence detection.

---

# Meta-Controller (Feedback Layer)

When a structural state repeats frequently:

strength ↑  

The Meta-Controller tightens thresholds for that crystal:

warn_threshold_meta  
block_threshold_meta  

Formula (simplified):

new_threshold = threshold × (1 − α log(1 + strength))

Constraints:
- Hard minimum clamp  
- Max shrink limit  
- Order preserved (block > warn)  

This creates structural learning without semantic memory.

---

# Quickstart (Local)

Clone:

```bash
git clone https://github.com/pozdnyavladimer-jpg/gitcube-lab.git
cd gitcube-lab
```

Verify environment:

```bash
PYTHONPATH=. python -c "import memory; print('OK')"
```

Run HFS simulator:

```bash
python hfs/hfs_demo.py --seed 99 --n 220 --window 20 > report.json
```

Record Memory Atom:

```bash
PYTHONPATH=. python -m memory.cli record \
  --report report.json \
  --store memory/memory.jsonl \
  --repo demo \
  --ref test
```

View stats:

```bash
PYTHONPATH=. python -m memory.cli stats \
  --store memory/memory.jsonl
```

Query stored atoms:

```bash
PYTHONPATH=. python -m memory.cli query \
  --store memory/memory.jsonl \
  --limit 10
```

---

# Full System Flow

Graph / Interaction Stream  
↓  
Structural Metrics  
↓  
Continuous Risk  
↓  
Adaptive Baseline (μ, σ)  
↓  
Discrete Gate (ALLOW / WARN / BLOCK)  
↓  
Memory Atom  
↓  
Crystal Aggregation  
↓  
Meta-Controller Feedback  

Closed structural loop.

---

# Repository Structure

```
hfs/
  hfs_demo.py
  ai_validator_hfs.py
  hfs_schema.md

memory/
  atom.py
  store.py
  cli.py
  meta_controller.py

docs/
  topological-alphabet.md
```

---

# Use Cases

- CI/CD structural gating  
- Architecture drift detection  
- Recurrent instability mapping  
- AI meta-control layer  
- Cognitive volatility monitoring  

---

# Project Status

Research prototype — hybrid control + structural memory.

Focus:
- Graph invariants  
- Adaptive baselining  
- Structural entropy  
- Recurrent state learning  
- Feedback control  

---

# License

AGPL-3.0
