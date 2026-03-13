# Graph School Benchmark

Graph School is a benchmark for measuring whether an agent can repair unsafe software topology under typed graph constraints.

This benchmark is built on top of:

- `apps/grapheval/*` — typed graph scoring engine
- `agent/gym.py` — mutation-based repair loop
- `agent/train.py` — curriculum / trace generation
- `agent/benchmark.py` — aggregate benchmark runner

---

## Goal

The benchmark does **not** measure whether an agent can produce nice text.

It measures whether an agent can:

1. read a graph task
2. propose an initial topology
3. improve that topology through repair attempts
4. reduce structural risk
5. satisfy architectural goals
6. escape unsafe states such as `BLOCK`

---

## Core Question

**Can an agent repair unsafe software architecture under formal typed-graph rules?**

---

## Task Format

Tasks live in:

```text
datasets/grapheval/tasks/
