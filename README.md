# gitcube-lab (specs + Topological Alphabet)

This repo is the **human-readable + math-readable** layer for GitCube.

- **gitcube-core** = code + CLI + GitHub Action
- **gitcube-lab** = *Topological Alphabet*, math spec, examples, visuals, PR comment templates

## What is GitCube?
GitCube treats a codebase as a **directed dependency graph** and measures **structural stability**.
Instead of long reports, it emits a compact **Structural DNA** string:

```
G0 P1 C0 M0 D0 T0 E0 K1
```

Think of it as **HTTP status codes for architecture**.

## Structural DNA (Topological Alphabet v2.0)

Each symbol is a *channel* (0 OK, 1 WARN, 2 BLOCK):

- **G** — Gate verdict (ALLOW/WARN/BLOCK)
- **P** — Pressure (spectral / entropy proxy)
- **C** — Cycles (cycle-forming edges / SCC cycle risk)
- **M** — Merge (SCC merge pressure: coupling growth)
- **D** — Density (dependency density / fan-in/out)
- **T** — Drift (baseline delta vs normal)
- **E** — Edge risk (top harmful edges attribution)
- **K** — Scale bucket (size normalization)

Detailed definitions: **docs/topological_alphabet.md**  
Math spec: **docs/maths_spec.md**

## How it shows up in GitHub (PR comment)

Example:

> **GitCube**: `G1 P1 C0 M1 D0 T1 E1 K1` → **WARN**  
> Top risky edges:  
> 1) `payments.api → core.db` (cycle-forming)  
> Suggested cut: introduce `payments.port` interface (Dependency Inversion)

Templates: **docs/pr_comment_templates.md**

## Why a separate repo?
Because people read two different “languages”:
- **Product language** (CTO/PM): simple DNA + decision
- **Science language** (engineers/research): definitions + proofs + complexity

Keeping them separated avoids mixing marketing, spec, and core implementation.
