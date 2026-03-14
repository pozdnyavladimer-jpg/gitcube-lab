GitCube Lab

Structural Risk Control, Topological Memory & Graph Architecture Benchmark

GitCube Lab — експериментальна система контролю структури програмних архітектур.

Проект поєднує:

- GraphEval — фізику структурного ризику для графів архітектури
- Graph School — benchmark середовище для агентів, які ремонтують архітектуру
- Topological Memory — систему довготривалої пам'яті структурних станів
- Kernel Sandbox — експерименти з нелінійною динамікою та фазовими переходами

Це не NLP.
Це моделювання структурної стабільності.

---

TL;DR

GitCube Lab перетворює архітектуру системи на фізичну модель:

graph topology
→ structural invariants (DNA)
→ continuous risk (0..1)
→ discrete verdict (ALLOW / WARN / BLOCK)
→ repair attempts
→ benchmark metrics
→ persistent structural memory
## Architecture Pipeline

The system treats software architecture as a graph and evaluates its structural stability.

```text
           Software Architecture
                   │
                   ▼
            Typed Graph Model
         (nodes + typed edges)
                   │
                   ▼
            GraphEval Scoring
         structural invariants
         cycles / layers / density
                   │
                   ▼
           Structural Risk
               0.0 – 1.0
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
     ALLOW                 BLOCK
        │                     │
        │                     ▼
        │              Repair Agent
        │            (mutation loop)
        │                     │
        │                     ▼
        │               New Topology
        │                     │
        └───────────▲─────────┘
                    │
               Re-evaluation
                    │
                    ▼
            Benchmark Metrics
Continuous inside.
Discrete outside.
Memory across time.

---

GraphEval — Structural Risk Engine

GraphEval — це benchmark framework для оцінки архітектурних графів з типізованими ребрами та фізикою структурного ризику.

LLM можуть писати код.
Але вони не відчувають архітектурний біль.

GraphEval вводить цей біль чисельно.

---

Problem

Сучасні LLM:

- будують dependency graphs
- оптимізують код
- але не відчувають макроархітектурних порушень

Вони можуть:

- створювати цикли
- пробивати шари
- перевантажувати систему щільністю зв’язків
- маскувати небезпечні виклики

GraphEval — це середовище, де ці дії мають числові наслідки.

---

Core Model

Nodes

Кожен вузол має:

- "id"
- "layer"
- capability flags
  - "can_feedback"
  - "is_core"

---

Edge Types (6-Edge Grammar)

Strict edges

Формують структурну масу:

DEP
SYNC_CALL
DATA
OWN

Soft edges

EVENT

Асинхронна комунікація без блокування.

Exception channel

FEEDBACK

Контрольований зворотний канал.

---

Structural Risk Model

Risk ∈ [0.0 – 1.0]

Layer breach

risk >= 0.45 + 0.10 * min(4, layer_viol)

Strict cycles

strict_cycles > 0
→ risk >= 0.85
→ verdict = BLOCK

Dense mesh

d_pen = (density / max_density - 1)^2

---

Anti-Toxin Rules

GraphEval містить захист від токсичних патернів.

Feedback capability

FEEDBACK дозволений тільки між вузлами
які мають capability flag

Feedback quota

feedback_ratio ≤ limit

Deadly pair

SYNC_CALL(A → B)
+
FEEDBACK(B → A)

→ BLOCK

Core protection

EVENT → is_core
→ BLOCK

---

Graph School

Graph School — це benchmark середовище для агентів, які намагаються ремонтувати небезпечну архітектуру.

Pipeline:

task
→ initial topology
→ mutation operators
→ scoring
→ best candidate
→ benchmark report

---

Agent System

Directory:

agent/
  gym.py
  mutations.py
  train.py
  benchmark.py

gym.py

Mutation loop.

solution
→ mutations
→ scoring
→ keep improvements

mutations.py

Repair operators:

remove_forbidden_edges
add_required_edges
remove_reverse_feedback_deadly_pairs
trim_feedback_without_capability
remove_illegal_sync_to_core

train.py

Training loop.

Creates:

traces/train_traces.jsonl

benchmark.py

Runs the full benchmark and produces:

reports/benchmark_report.json

---

Repository Structure

apps/
  grapheval/
    schema.py
    scorer.py
    runner.py

agent/
  gym.py
  mutations.py
  train.py
  benchmark.py

datasets/
  grapheval/
    tasks/

traces/
  train_traces.jsonl

reports/
  benchmark_report.json

memory/
  atom.py
  store.py
  meta_controller.py

docs/
  benchmark.md
  benchmark_results.md

---

Quickstart

Clone repository:

git clone https://github.com/pozdnyavladimer-jpg/gitcube-lab.git
cd gitcube-lab

Verify Python path:

PYTHONPATH=. python -c "import apps.grapheval; print('OK')"

---

Run GraphEval

PYTHONPATH=. python -m apps.grapheval.runner

---

Train Repair Agent

export PYTHONPATH=.
python -m agent.train --reset

Creates:

traces/train_traces.jsonl

---

Run Benchmark

export PYTHONPATH=.
python -m agent.benchmark

Creates:

reports/benchmark_report.json

---

Topological Memory

GitCube також містить систему структурної пам'яті.

MemoryAtoms:

structural_state
→ invariant extraction
→ crystal_key
→ persistent memory

Components:

memory/atom.py
memory/store.py
memory/meta_controller.py

---

Kernel Sandbox

Експерименти з фазовими переходами та синхронізацією:

kuramoto13.py
teleport.py

---

Current Status

Current version:

Graph School v0.1

Capabilities:

✔ structural risk scoring
✔ graph mutation repair
✔ benchmark reporting
✔ training traces
✔ topological memory

Remaining challenge:

task_010_feedback_ok

This task reveals the limits of the current repair operators.

---

Vision

Навчити AI-агентів:

- не просто генерувати код
- а будувати стабільні топології

GraphEval — це не лінтер.

Це фізика архітектури.
┌─────────────────────────────┐
                    │        INPUT FIELD           │
                    │ Architecture / Code Graphs   │
                    │ datasets/grapheval/tasks     │
                    └───────────────┬──────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │       GRAPH STRUCTURE       │
                    │ typed nodes + typed edges   │
                    │ apps/grapheval/schema.py    │
                    └───────────────┬──────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │    STRUCTURAL PHYSICS       │
                    │ GraphEval Risk Engine       │
                    │ cycles / layers / density   │
                    │ apps/grapheval/scorer.py    │
                    └───────────────┬──────────────┘
                                    │
                          risk ∈ [0..1]
                                    │
                      ┌─────────────┴─────────────┐
                      ▼                           ▼
               ┌──────────────┐           ┌──────────────┐
               │   ALLOW      │           │   BLOCK      │
               │ stable graph │           │ unsafe graph │
               └──────┬───────┘           └──────┬───────┘
                      │                          │
                      │                          ▼
                      │               ┌────────────────────┐
                      │               │     AGENT GYM       │
                      │               │ mutation operators  │
                      │               │ agent/gym.py        │
                      │               │ agent/mutations.py  │
                      │               └─────────┬───────────┘
                      │                         │
                      │                 new topology
                      │                         │
                      └───────────────▲─────────┘
                                      │
                                 re-score
                                      │
                                      ▼
                    ┌─────────────────────────────┐
                    │      BENCHMARK LAYER        │
                    │ training traces             │
                    │ traces/train_traces.jsonl   │
                    │ reports/benchmark_report    │
                    └───────────────┬──────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │       MEMORY FIELD          │
                    │ structural memory atoms     │
                    │ memory/store.py             │
                    │ memory/meta_controller.py   │
                    └───────────────┬──────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │      CRYSTAL TOPOLOGY       │
                    │ final structural state      │
                    │ verdict: ALLOW / WARN /     │
                    │ BLOCK                       │
                    └─────────────────────────────┘
