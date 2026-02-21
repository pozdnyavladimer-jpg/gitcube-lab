## Topological Memory (Memory Atoms)

GitCube-Lab can **crystallize** reports into compact **Memory Atoms**.
Instead of storing raw text, we store **structural invariants**:

- verdict: `ALLOW | WARN | BLOCK`
- DNA: compressed signature
- baseline: `μ, σ, warn_threshold, block_threshold`
- energy band: `1..7` (high risk → 1)

### Record an atom

```bash
# after you produced report.json (from GitCube or HFS)
python -m memory.cli record --report report.json --store memory/memory.jsonl --repo your/repo --ref PR#12
```

### Query atoms

```bash
python -m memory.cli query --store memory/memory.jsonl --verdict BLOCK --limit 10
```
