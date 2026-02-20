# Math Spec (v2 MVP)

## 1) Code graph
Let the main branch define a directed dependency graph:
\[
G=(V,E),\quad |V|=n,\ |E|=m
\]
An edge \((u\to v)\in E\) means “u imports/depends on v”.

Adjacency matrix:
\[
A\in\{0,1\}^{n\times n},\quad A_{uv}=1\iff (u\to v)\in E.
\]

A PR induces edge changes:
\[
\Delta E=\Delta E^+\ \cup\ \Delta E^-.
\]
After merge:
\[
E'=(E\cup \Delta E^+)\setminus \Delta E^-,\quad G'=(V',E')\ \ (\text{often }V'=V).
\]

## 2) Cyclic structure via SCC
Let \(\mathrm{SCC}(G)=\{C_1,\dots,C_k\}\) be the strongly-connected components.
A simple “cycle mass” proxy:
\[
\mathrm{SCC\_mass}(G)=\frac{\max_i |C_i|}{|V|}.
\]

## 3) Deterministic cycle-forming edge test
For a candidate added edge \(e=(u\to v)\),
\[
e \text{ creates a cycle in } G\ \Longleftrightarrow\ v \leadsto u \text{ in } G.
\]
In terms of reachability matrix \(R\) (transitive closure):
\[
R_{vu}=1 \iff v\leadsto u,\quad g_{\mathrm{cycle}}(e;G)=\mathbf{1}\{R_{vu}=1\}.
\]

## 4) SCC condensation DAG + “merge” risk
Let \(\pi:V\to\{1,\dots,k\}\) map nodes to SCC indices.
Build condensation DAG \(G_{\mathrm{scc}}\).
An added edge can merge SCC regions:
\[
g_{\mathrm{scc}}(e;G)=\mathbf{1}\{\exists \text{ path }\pi(v)\leadsto \pi(u)\text{ in }G_{\mathrm{scc}}\}.
\]

## 5) Spectral proxy (structural entropy)
For stability analysis we symmetrize:
\[
A_s=A+A^\top\quad (\text{or }A_s=\mathbf{1}\{A+A^\top>0\}).
\]
Let \(D=\mathrm{diag}(d_1,\dots,d_n)\), \(d_i=\sum_j (A_s)_{ij}\).
Normalized Laplacian:
\[
L=I-D^{-1/2}A_sD^{-1/2},\quad 0=\lambda_1\le\dots\le \lambda_n\le 2.
\]
A practical entropy over normalized spectrum:
\[
p_i=\frac{\lambda_i}{\sum_{j=1}^n \lambda_j},\quad
H(G)=-\sum_{i=1}^n p_i\log p_i.
\]
Structural drift:
\[
\Delta H=H(G')-H(G).
\]

(Implementation uses **proxies**: top-k eigvals (Lanczos/ARPACK) or heat-kernel traces.)

## 6) PR risk functional + verdict
\[
R(G,\Delta E)=\alpha\cdot \Delta \mathrm{SCC\_mass}\ +\ \beta\cdot \Delta H\ +\ \gamma\cdot \sum_{e\in \Delta E^+} g_{\mathrm{cycle}}(e;G).
\]
Verdict thresholds are adaptive:
\[
\text{ALLOW}\iff R\le \tau_1,\quad
\text{WARN}\iff \tau_1<R\le \tau_2,\quad
\text{BLOCK}\iff R>\tau_2.
\]
