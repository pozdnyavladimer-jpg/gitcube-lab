# GraphEval — School of AI Architecture

GraphEval — це benchmark framework для оцінки архітектурних графів з типізованими ребрами та фізикою структурного ризику.

LLM можуть писати код. Але вони не відчувають архітектурний біль. GraphEval вводить цей біль чисельно.

---

## 🧠 Problem
Сучасні LLM:
- будують графи залежностей
- оптимізують код
- але **не відчувають макро-архітектурних порушень**

Вони можуть:
- створювати цикли
- пробивати шари
- перевантажувати систему щільністю зв’язків
- маскувати жорсткі виклики під "легальні" типи

**GraphEval — це середовище, де ці дії мають числові наслідки.**

---

## 🧬 Core Model

### Nodes
- Ідентифікатор (`id`)
- Шар (`layer`)
- Capability flags (`can_feedback`, `is_core`)

### Edge Types (6-Edge Grammar)
**Strict (Формують структуру та масу):**
- `DEP` — Залежність (import/compile-time)
- `SYNC_CALL` — Блокуючий виклик (runtime)
- `DATA` — Передача стану
- `OWN` — Композиція / Життєвий цикл

**Soft (Ефір / Інформація):**
- `EVENT` — Асинхронна подія (не створює структурного блокування)

**Exception (Кібернетика):**
- `FEEDBACK` — Контрольований канал вгору по шарах

---

## ⚙ Risk Model
Risk ∈ [0.0 – 1.0]

### 1. Layer breach
Якщо є порушення шарів (`layer_viol > 0`):
`risk >= 0.45 + 0.10 * min(4, layer_viol)`

### 2. Strict cycles
Якщо є жорсткий цикл (`strict_cycles > 0`):
`risk >= 0.85` та `verdict = BLOCK`

### 3. Dense mesh
Квадратичний штраф за перевищення ліміту щільності:
`d_pen = (density / max_density - 1)^2`

### 4. Adversarial protection (Anti-toxin)
- `FEEDBACK` вимагає capability flag на обох вузлах.
- Квота на `FEEDBACK` (наприклад, <= 5% від strict ребер).
- `SYNC_CALL` + зворотний `FEEDBACK` між тими ж вузлами = `BLOCK` (Deadly pair).
- `EVENT` не може напряму бити в захищені (`is_core`) вузли.

---

## 📂 Structure
```text
apps/
  grapheval/
    __init__.py
    schema.py
    scorer.py
    runner.py
datasets/
  grapheval/
    tasks/
      task_001.json
      task_002.json
      ...
How to Run
PYTHONPATH=. python -m apps.grapheval.runner
Goal & Vision
Навчити AI-агентів не просто генерувати код, а будувати стабільні топології з мінімальним структурним ризиком.
GraphEval — це не лінтер. Це школа, де архітектура стає фізикою.
🔬 Roadmap
[ ] Agent mutation loop (Симуляція навчання)
[ ] Adversarial LLM testing (Перевірка на злом правил)
[ ] Real repo graph extraction
[ ] Curriculum mode (Навчальна програма)
[ ] Visual topology renderer
<!-- end list -->

# GitCube Lab
**Structural Risk Control & Topological Memory Engine**

GitCube Lab is an experimental control system that converts structure (topology) into:
- **continuous risk** (0..1)
- **discrete decisions** (ALLOW / WARN / BLOCK)
- **persistent structural memory** (Memory Atoms → Crystal Keys)

This is not NLP.  
This is not sentiment analysis.  
This is structural instability modeling.

---

## TL;DR

GitCube:
1) Extracts structural invariants (DNA)  
2) Aggregates them into continuous risk (0..1)  
3) Computes adaptive thresholds (μ + kσ)  
4) Produces ALLOW / WARN / BLOCK  
5) Persists compact records (Memory Atoms)  
6) Merges recurring states (Crystal Keys)  
7) Enables meta-control (feedback tightening)

Continuous inside.  
Discrete outside.  
Memory across time.

---

## Repository Map

### Core (Topological Memory)
- `memory/atom.py` — MemoryAtom (phase_state 1..42, flower invariant, crystal_key)
- `memory/store.py` — JSONL store with `upsert()` merge by `crystal_key`
- `memory/cli.py` — CLI: record / query / stats
- `memory/meta_controller.py` — optional feedback tightening layer

### Kernel Sandbox (signals → discrete “keyboard”)
- `kuramoto13.py` — 13-node Kuramoto engine, CRYSTAL detection
- `teleport.py` — continuous state → `O1..O7` + stable letter (a “keyboard”)

### Applications (examples)
- `apps/vr_comfort/vestibular_kernel.py` — adaptive comfort controller (VR mismatch)
- `apps/vr_comfort/demo_vr_comfort.py` — demo runner
- `apps/graph_school/*` — (optional) graph learning/training environment

Docs:
- `docs/kernel_overview.md`
- `docs/memory.md`

---

## Quickstart (Local)

Clone:
```bash
git clone https://github.com/pozdnyavladimer-jpg/gitcube-lab.git
cd gitcube-lab
Verify Python can import packages:
PYTHONPATH=. python -c "import memory; print('OK')"
Run HFS simulator (example)
python hfs/hfs_demo.py --seed 99 --n 220 --window 20 > report.json
Record a Memory Atom (JSON report → JSONL)
PYTHONPATH=. python -m memory.cli record \
  --report report.json \
  --store memory/memory.jsonl \
  --repo demo \
  --ref test
Store stats
PYTHONPATH=. python -m memory.cli stats --store memory/memory.jsonl
Query stored atoms
PYTHONPATH=. python -m memory.cli query --store memory/memory.jsonl --limit 10
Kernel Runs (Sandbox)
python kuramoto13.py
python teleport.py
python apps/vr_comfort/demo_vr_comfort.py
