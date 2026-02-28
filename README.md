# GitCube Lab
**Structural Risk Control & Topological Memory Engine**

GitCube Lab is an experimental control system that converts structure (topology) into:
- **continuous risk** (0..1)
- **discrete decisions** (ALLOW / WARN / BLOCK)
- **persistent structural memory** (Memory Atoms → Crystal Keys)

This is not NLP.  
This is not sentiment analysis.  
This is structural instability modeling.

---

## TL;DR

GitCube:
1) Extracts structural invariants (DNA)  
2) Aggregates them into continuous risk (0..1)  
3) Computes adaptive thresholds (μ + kσ)  
4) Produces ALLOW / WARN / BLOCK  
5) Persists compact records (Memory Atoms)  
6) Merges recurring states (Crystal Keys)  
7) Enables meta-control (feedback tightening)

Continuous inside.  
Discrete outside.  
Memory across time.

---

## Repository Map

### Core (Topological Memory)
- `memory/atom.py` — MemoryAtom (phase_state 1..42, flower invariant, crystal_key)
- `memory/store.py` — JSONL store with `upsert()` merge by `crystal_key`
- `memory/cli.py` — CLI: record / query / stats
- `memory/meta_controller.py` — optional feedback tightening layer

### Kernel Sandbox (signals → discrete “keyboard”)
- `kuramoto13.py` — 13-node Kuramoto engine, CRYSTAL detection
- `teleport.py` — continuous state → `O1..O7` + stable letter (a “keyboard”)

### Applications (examples)
- `apps/vr_comfort/vestibular_kernel.py` — adaptive comfort controller (VR mismatch)
- `apps/vr_comfort/demo_vr_comfort.py` — demo runner
- `apps/graph_school/*` — (optional) graph learning/training environment

Docs:
- `docs/kernel_overview.md`
- `docs/memory.md`

---

## Quickstart (Local)

Clone:
```bash
git clone https://github.com/pozdnyavladimer-jpg/gitcube-lab.git
cd gitcube-lab
Verify Python can import packages:
PYTHONPATH=. python -c "import memory; print('OK')"
Run HFS simulator (example)
python hfs/hfs_demo.py --seed 99 --n 220 --window 20 > report.json
Record a Memory Atom (JSON report → JSONL)
PYTHONPATH=. python -m memory.cli record \
  --report report.json \
  --store memory/memory.jsonl \
  --repo demo \
  --ref test
Store stats
PYTHONPATH=. python -m memory.cli stats --store memory/memory.jsonl
Query stored atoms
PYTHONPATH=. python -m memory.cli query --store memory/memory.jsonl --limit 10
Kernel Runs (Sandbox)
python kuramoto13.py
python teleport.py
python apps/vr_comfort/demo_vr_comfort.py
