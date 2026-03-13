# Graph School Benchmark Results

## Current Status

Graph School benchmark is running successfully.

Generated artifacts:

- `traces/train_traces.jsonl`
- `reports/benchmark_report.json`

---

## Current Outcome

Observed result:

- total tasks: 10
- solved / ALLOW: 9
- blocked: 1

Main hard failure:

- `task_010_feedback_ok`

---

## Interpretation

The current system is able to:

1. load typed graph tasks
2. construct an initial candidate topology
3. run local repair attempts
4. evaluate candidates with GraphScorer
5. keep best repairs
6. export benchmark results as structured JSON

This confirms that the repository already contains a working prototype of an architecture-repair benchmark.

---

## What works well

The benchmark currently succeeds on most tasks with:

- low structural risk
- valid layer behavior
- acceptable typed edge usage
- clean goal satisfaction on simple tasks

This means the scorer, gym loop, training loop, and benchmark export are all functioning together correctly.

---

## Current Limitation

The remaining hard failure is:

- `task_010_feedback_ok`

Why it still fails:

- the system can add required edges
- but it still cannot fully repair toxic feedback routing
- it does not yet perform a strong adapter insertion / rerouting strategy

In other words:

the benchmark already proves repair capability,
but not yet robust control-channel repair.

---

## Technical Conclusion

Current version is sufficient to claim:

> Graph School is a working benchmark for evaluating whether agents can improve unsafe software topology under typed graph constraints.

---

## Next Improvement Target

Priority mutation to add next:

- `insert_feedback_adapter`
or
- stronger `reroute_feedback_via_adapter`

Expected impact:

- reduce hard failures from 1 to 0
- improve block escape rate
- improve benchmark completeness

---

## Benchmark Meaning

This project is no longer only a graph scorer.

It is now:

- a structural evaluator
- a repair loop
- a training trace generator
- a benchmark protocol

That is the transition from **tool** to **research environment**.
