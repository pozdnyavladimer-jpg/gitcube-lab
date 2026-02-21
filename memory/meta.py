# memory/meta.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def _dna_tokens(dna: str) -> List[str]:
    """
    DNA format examples:
      "DNA: T2 R1 P1 S1 C0 F0 W0 M1"
      "C1 L0 D2 S1 H0 E1 P1 M0"
    We tokenize into ["T2","R1",...].
    """
    dna = dna.strip()
    dna = dna.replace("DNA:", "").strip()
    parts = [p.strip() for p in dna.split() if p.strip()]
    # keep only things like "T2" or "C1"
    toks = [p for p in parts if len(p) >= 2 and p[0].isalpha() and p[1:].isdigit()]
    return toks

def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))

@dataclass
class MetaStats:
    matched: int
    block_rate: float
    avg_band: float
    avg_risk: float
    penalty: float
    verdict_meta: str

def meta_adjust_report(
    report: Dict[str, Any],
    memory_items: List[Dict[str, Any]],
    *,
    k: int = 20,
    min_matches: int = 3,
    alpha_block: float = 0.18,   # how strong BLOCK history affects penalty
    alpha_band: float = 0.06,    # band contribution
    alpha_recency: float = 0.0,  # (optional) if you later add recency weighting
    max_penalty: float = 0.25,
) -> Tuple[Dict[str, Any], MetaStats]:
    """
    Returns: (new_report_with_meta_fields, stats)

    Strategy:
      - find similar items by DNA token overlap (Jaccard)
      - compute block_rate, avg_band, avg_risk
      - penalty = alpha_block*block_rate + alpha_band*(avg_band/7)
      - risk' = clamp(risk + penalty, 0, 1)
      - verdict_meta computed using original thresholds from report (warn/block)
    """
    dna_now = str(report.get("dna", ""))
    toks_now = _dna_tokens(dna_now)

    kind_now = report.get("kind")
    # score each memory atom
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for it in memory_items:
        if kind_now and it.get("kind") != kind_now:
            continue
        dna_it = str(it.get("dna", ""))
        toks_it = _dna_tokens(dna_it)
        sim = _jaccard(toks_now, toks_it)

        # small boost if same verdict
        if it.get("verdict") == report.get("verdict"):
            sim += 0.05

        if sim > 0.0:
            scored.append((sim, it))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [it for _, it in scored[:k]]

    matched = len(top)
    if matched == 0:
        # nothing to learn from
        penalty = 0.0
        risk_meta = float(report.get("risk", 0.0))
        verdict_meta = str(report.get("verdict", "ALLOW"))
        stats = MetaStats(0, 0.0, 0.0, 0.0, 0.0, verdict_meta)
        out = dict(report)
        out["meta_control"] = {"matched": 0, "penalty": 0.0, "risk_meta": risk_meta, "verdict_meta": verdict_meta}
        return out, stats

    n_block = sum(1 for it in top if it.get("verdict") == "BLOCK")
    block_rate = n_block / float(matched)

    bands = [float(it.get("band", 0.0)) for it in top if it.get("band") is not None]
    avg_band = sum(bands) / float(len(bands)) if bands else 0.0

    risks = [float(it.get("risk", 0.0)) for it in top if it.get("risk") is not None]
    avg_risk = sum(risks) / float(len(risks)) if risks else 0.0

    penalty = alpha_block * block_rate + alpha_band * (avg_band / 7.0)
    penalty = _clamp(penalty, 0.0, max_penalty)

    risk = float(report.get("risk", 0.0))
    risk_meta = _clamp(risk + penalty, 0.0, 1.0)

    warn_th = float(report.get("warn_threshold", report.get("baseline", {}).get("warn_threshold", 0.0)))
    block_th = float(report.get("block_threshold", report.get("baseline", {}).get("block_threshold", 1.0)))

    # If too few matches, don't change verdict (avoid overfitting)
    if matched < min_matches:
        verdict_meta = str(report.get("verdict", "ALLOW"))
    else:
        if risk_meta > block_th:
            verdict_meta = "BLOCK"
        elif risk_meta > warn_th:
            verdict_meta = "WARN"
        else:
            verdict_meta = "ALLOW"

    out = dict(report)
    out["meta_control"] = {
        "matched": matched,
        "block_rate": block_rate,
        "avg_band": avg_band,
        "avg_risk": avg_risk,
        "penalty": penalty,
        "risk_meta": risk_meta,
        "verdict_meta": verdict_meta,
    }

    stats = MetaStats(matched, block_rate, avg_band, avg_risk, penalty, verdict_meta)
    return out, stats
