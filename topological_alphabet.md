# Topological Alphabet v2.0 (Structural DNA)

## Encoding
Structural DNA is an ordered list of 8 symbols:

`G P C M D T E K`

Each symbol takes a level in {0,1,2}:

- 0 = OK (within baseline)
- 1 = WARN (visible risk / trend)
- 2 = BLOCK (structural hazard)

A report includes:
- `dna.signature` (string)
- `dna.symbols` (per-symbol explanation, thresholds, measured value)

## Symbol meanings (practical)
### G — Gate
Maps the aggregated risk `R` to ALLOW/WARN/BLOCK.

### P — Pressure (entropy / spectral proxy)
Measures global structural “tightness” (coupling + loss of modular separability).
For v2 MVP, use a spectral proxy `H(G)` and report `ΔH`.

### C — Cycles (cycle-forming edges)
Detects whether PR introduces edges that close a path `v →* u` (cycle creation).
Also report SCC mass trend.

### M — Merge (SCC merge pressure)
Measures *how much* SCCs are merged/expanded by the PR:
- merging two SCCs into a bigger SCC increases rework risk.

### D — Density
Dependency density / fan-in/out inflation (size-normalized).

### T — Drift (adaptive baseline)
How far metrics drift from repo’s historical normal:
- uses rolling baseline (median + MAD or mean + std).
This is what makes thresholds adaptive per-repo.

### E — Edge risk attribution
Top-N edges with the largest local risk contribution:
- cycle-forming
- SCC-merging
- largest estimated ΔH contribution

### K — Scale bucket
Size normalization: small repos need different thresholds than huge monoliths.

## Output (JSON sketch)
See `docs/json_schema.md`.
