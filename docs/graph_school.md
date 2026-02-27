# Graph School

Graph School is a structural grammar simulator.

It evaluates directed graphs representing software architectures.

Each lesson is a JSON file containing:
- nodes (with layer levels)
- edges (directed dependencies)

The engine evaluates:
- Cycles
- Layer violations
- Skip violations
- Graph density
- Structural entropy

Output:
- Verdict: ALLOW / WARN / BLOCK
- Risk score
- DNA signature

This is a topology-first learning model.

No semantic analysis.
Only structure.
