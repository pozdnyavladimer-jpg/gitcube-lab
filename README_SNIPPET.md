## Topological Memory (Memory Atoms)

GitCube-Lab can persist structural reports as compact Memory Atoms. Instead of storing raw logs or full text streams, the system stores structural invariants extracted from validated reports. 

**Each Memory Atom contains:**
- **verdict:** `ALLOW | WARN | BLOCK`
- **DNA:** compressed structural signature
- **baseline parameters:** `μ, σ`
- **adaptive thresholds:** `warn_threshold, block_threshold`
- **energy band:** `1..7`
- **risk score**

Memory Atoms are append-only records and enable:
- structural feedback loops
- historical instability analysis
- adaptive threshold tuning
- meta-control for AI agents

---

### Record an Atom
```bash
python -m memory.cli record \
  --report report.json \
  --store memory/memory.jsonl \
  --repo your/repo \
  --ref PR#12
```

### Query Atoms
```bash
python -m memory.cli query \
  --store memory/memory.jsonl \
  --verdict BLOCK \
  --limit 10
```

*Memory operates as a structural state history — not a chat log.*
