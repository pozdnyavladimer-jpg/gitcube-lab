# Topological Memory (Memory Atoms)

GitCube-Lab can store *crystallized* events as compact **Memory Atoms**.

Why this exists:
- LLMs store text; we store **structural invariants**.
- A Memory Atom is a small JSON record: **DNA + verdict + baseline**.
- This is designed to be searchable and safe for CI.

## Atom format

Each atom contains:
- `verdict`: `ALLOW | WARN | BLOCK`
- `dna`: a compact signature (Structural DNA or HFS DNA)
- `band`: 1..7 energy band (high risk -> 1)
- `risk`: continuous value in `[0,1]`
- baseline: `mu`, `sigma`, `warn_threshold`, `block_threshold`
- optional anchors: `repo`, `ref`

## Store

Atoms are stored in a JSONL file (append-only):

`memory/memory.jsonl`

## CLI

Record a report as an atom:

```bash
python -m memory.cli record --report report.json --store memory/memory.jsonl --repo my/repo --ref PR#12
```

Query stored atoms:

```bash
python -m memory.cli query --store memory/memory.jsonl --verdict BLOCK --limit 10
```

This gives you a searchable stream of *structural states*.
