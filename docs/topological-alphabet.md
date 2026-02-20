# Topological Alphabet Specification

Structural DNA is a compressed signature of graph invariants.

Let G = (V, E).

We compute:

1. C — Cycle risk (SCC mass increase)
2. L — Layer violations
3. D — Edge density drift
4. S — Structural delta between revisions
5. H — Spectral entropy proxy
6. E — Entropy acceleration
7. P — Pressure score (combined soft risk)
8. M — Critical gate flag

Each metric is evaluated against adaptive baseline thresholds:

WARN  = μ + 2σ  
BLOCK = μ + 3σ  

Where μ and σ are computed per-repository.

---

## Structural Risk Function

R(G, ΔE) = α ΔC + β ΔH + γ Σ g_cycle(e)

### Verdict

ALLOW  ↔ R ≤ τ1  
WARN   ↔ τ1 < R ≤ τ2  
BLOCK  ↔ R > τ2  

This makes GitCube adaptive, not rigid.
