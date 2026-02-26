# Topological Memory (Memory Atoms)

GitCube persists structural reports as compact Memory Atoms.

Instead of storing raw logs or full text streams, the system stores structural invariants extracted from validated reports.

---

## Each Memory Atom Contains

- verdict: ALLOW | WARN | BLOCK  
- DNA signature  
- baseline parameters (μ, σ)  
- adaptive thresholds  
- risk score  
- phase_state (1..42)  
- flower invariant (petal_area)  
- crystal_key  

Atoms are stored as JSONL records.

---

## Crystal Keys

Each Memory Atom generates:

crystal_key = kind + ":" + dna_key

Example:

HFS_NAVIGATOR_REPORT:T1 R3 S1

The system aggregates:

- strength (occurrence count)  
- flower_area_sum  
- flower_area_max  
- last_seen  

This enables structural recurrence detection.

---

## Merge Strategy

MemoryStore uses upsert():

- Merge by crystal_key  
- Increase strength  
- Update last_seen  
- Accumulate flower area  

This creates structural memory across time.

---

## Record an Atom

```bash
python -m memory.cli record \
  --report report.json \
  --store memory/memory.jsonl \
  --repo your/repo \
  --ref PR#12
```

---

## Query Atoms

```bash
python -m memory.cli query \
  --store memory/memory.jsonl \
  --verdict BLOCK \
  --limit 10
```

---

## View Last Entry

```bash
tail -n 1 memory/memory.jsonl
```
