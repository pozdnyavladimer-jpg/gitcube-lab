
---

GitCube Lab — System Map

GitCube Lab — це система для аналізу і ремонту архітектури програм як графів.

Замість аналізу окремих файлів система дивиться на топологію залежностей і перевіряє її стабільність.

Основний цикл системи:

perception → evaluation → repair → memory → control

Тобто:

код → граф → оцінка ризику → ремонт → пам'ять → рішення


---

Загальний потік системи

INPUT
архітектура / pull request

↓

GRAPH BUILDER
будується dependency graph

↓

STRUCTURAL PHYSICS
GraphEval оцінює ризик структури

↓

risk ∈ [0..1]

↓

SAFE → ALLOW
UNSAFE → WARN / BLOCK

↓

GRAPH SCHOOL
агенти пробують ремонтувати граф

↓

CRYSTAL MEMORY
результат записується як memory atom

↓

SWARM CONTROL
orchestrator приймає фінальне рішення

↓

FINAL DECISION


---

Основні підсистеми

1. Perception Layer

Файли:

apps/grapheval/schema.py

Завдання:

перетворити код у dependency graph

G = (V,E)


---

2. Structural Physics

Файли:

apps/grapheval/scorer.py

Це двигун оцінки ризику.

Він знаходить:

cycles

SCC mass

layer violations

dependency density

structural entropy


Результат:

risk score
ALLOW / WARN / BLOCK


---

3. Graph School

Файли:

agent/gym.py
agent/mutations.py
agent/train.py
agent/benchmark.py

Це середовище навчання агентів.

Цикл ремонту:

graph
→ mutate
→ rescore
→ keep improvement

Агенти вчаться:

розривати цикли

зменшувати SCC

відновлювати шари

стабілізувати архітектуру



---

4. Crystal Memory

Файли:

memory/atom.py
memory/store.py
memory/meta.py

Тут зберігаються Memory Atoms.

Приклад:

{ "dna": "G1 P1 C1", "risk": 0.58, "verdict": "WARN", "band": 3 }

Це стиснена пам'ять архітектурних станів.


---

5. Swarm Control

Файл:

agent/orchestrator.py

Це мозок системи.

Він:

читає structural DNA

активує органи агентів

обирає режим

формує фінальне рішення



---

Structural DNA

GitCube переводить архітектуру у символи:

G P C M D T E K

де:

G — Gate (ALLOW/WARN/BLOCK)
P — Pressure (entropy)
C — Cycles
M — SCC merge
D — Density
T — Drift
E — Edge risk
K — Scale

Приклад:

G1 P1 C1 M0 D0 T1

Це компактний опис стану архітектури.


---

Навчальний цикл системи

task
↓
graph
↓
risk evaluation
↓
repair attempts
↓
best topology
↓
memory atom
↓
policy update

З часом система накопичує архітектурний досвід.


---

Структура репозиторію

gitcube-lab

README.md
ARCHITECTURE.md
SYSTEM_MAP.md

apps/
grapheval/
scorer.py
schema.py

agent/
gym.py
mutations.py
train.py
benchmark.py
orchestrator.py

memory/
atom.py
store.py
meta.py

datasets/
grapheval/tasks

docs/
graph_school_benchmark.md


---

Мета проекту

GitCube створює AI систему, яка розуміє архітектуру програм.

Система повинна:

читати топологію систем

знаходити структурні ризики

ремонтувати небезпечні архітектури

пам'ятати патерни

допомагати AI проектувати стабільні системи


Коротко:

GitCube вчить AI думати як архітектор програмного забезпечення.


---
