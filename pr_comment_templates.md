# PR comment templates

## Compact (1-liner)
**GitCube**: `{DNA}` → **{VERDICT}**. {NOTE}

## Standard
**GitCube**: `{DNA}` → **{VERDICT}**  
- Pressure (ΔH): `{delta_H}` (thresholds: warn `{th_w}`, block `{th_b}`)  
- SCC mass: `{SCC_mass}` (Δ `{delta_SCC}`)  
- Cycle-forming edges: `{cycle_edges}`

**Top risky edges**
1) `{edge_1}` — `{reason_1}`  
   Suggested cut: `{fix_1}`

## Friendly (for OSS)
Thanks! This PR changes the dependency topology.  
GitCube reports: `{DNA}` → **{VERDICT}**.  
If you want, I can suggest a small refactor that removes the cycle risk.
