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

## TL;DR

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

## Core Components

### Structural DNA (Graph Layer)

Any repository can be represented as:

G = (V, E)

Where:
- V — modules/files  
- E — dependencies  

GitCube compresses structural invariants into an 8-symbol signature:

C L D S H E P M

Example:

DNA: C1 L0 D2 S1 H0 E1 P1 M0

Structural DNA encodes topology — not semantics.

---

### HFS — Human Function Stream

HFS models structural volatility in interaction streams.

Output:
- DNA signature  
- Continuous risk  
- Discrete verdict  

No semantic interpretation. Only structure.

---

## Risk Model

Risk ∈ [0,1]

Adaptive baseline:

warn_threshold = μ + 2σ  
block_threshold = μ + 3σ  

Decision logic:

risk ≤ warn_threshold → ALLOW  
warn_threshold < risk ≤ block_threshold → WARN  
risk > block_threshold → BLOCK  

Noise is measured — not punished.

---

## Topological Memory

Instead of storing raw logs, GitCube stores structural invariants:

- verdict  
- DNA  
- baseline (μ, σ)  
- thresholds  
- risk  
- phase band  
- flower geometry  
- crystal_key  

Atoms are stored as JSONL records.

---

## Meta-Control

Recurring structural states strengthen over time:

new_threshold = threshold × (1 − α log(1 + strength))

Constraints:
- Minimum clamp  
- Max shrink limit  
- Order preserved (block > warn)

This creates structural learning without semantic memory.

---

## Quickstart

Clone:

```bash
git clone https://github.com/pozdnyavladimer-jpg/gitcube-lab.git
cd gitcube-lab
```

Verify environment:

```bash
PYTHONPATH=. python -c "import memory; print('OK')"
```

Run HFS demo:

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

Query:

```bash
PYTHONPATH=. python -m memory.cli query \
  --store memory/memory.jsonl \
  --limit 10
```

---

## Kernel Sandbox

This repository also contains:

- `kuramoto13.py` — 13-node Kuramoto engine with CRYSTAL detection
- `teleport.py` — discrete mapping from continuous state → O1..O7 + letter
- `apps/vr_comfort/vestibular_kernel.py` — adaptive VR comfort controller
- `docs/kernel_overview.md` — kernel architecture details
- `docs/memory.md` — memory system details

---

## Use Cases

- CI/CD structural gating  
- Architecture drift detection  
- Recurrent instability mapping  
- AI meta-control layer  
- VR adaptive comfort systems  
- Cognitive volatility monitoring  

---

## Status

Research prototype — hybrid control + structural memory.

License: AGPL-3.0
