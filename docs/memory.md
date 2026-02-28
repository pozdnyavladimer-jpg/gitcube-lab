# Topological Memory (Memory Atoms)

GitCube-Lab can persist structural reports as compact Memory Atoms.
Instead of storing raw logs or full text streams, the system stores structural invariants.

## Each Memory Atom contains
- verdict: ALLOW | WARN | BLOCK
- DNA signature
- baseline parameters (μ, σ)
- adaptive thresholds (warn_threshold, block_threshold)
- risk score
- phase_state (1..42)
- flower invariant (petal_area)
- crystal_key

Atoms are stored as JSONL records.

## Crystal Keys
Each atom generates:
crystal_key = kind + ":" + dna_key

The store aggregates:
- strength (occurrence count)
- flower_area_sum
- flower_area_max
- last_seen

## Record an Atom
```bash
PYTHONPATH=. python -m memory.cli record \
  --report report.json \
  --store memory/memory.jsonl \
  --repo your/repo \
  --ref PR#12
Query Atoms
PYTHONPATH=. python -m memory.cli query \
  --store memory/memory.jsonl \
  --verdict BLOCK \
  --limit 10
Show last entry ("джонс")
tail -n 1 memory/memory.jsonl
