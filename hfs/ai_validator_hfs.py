# -*- coding: utf-8 -*-
"""
AI Validator for HFS Navigator (with optional Meta-Control feedback)
License: AGPL-3.0
Author: Володимир Поздняк

Reads HFS Navigator JSON report and enforces:
- ALLOW → exit 0
- WARN  → exit 2
- BLOCK → exit 3

Optional:
- Meta-control loop via --meta + --store memory.jsonl
  This uses historical Memory Atoms to adjust current risk (trust discount).

Usage:
  python hfs/ai_validator_hfs.py report.json
  python hfs/ai_validator_hfs.py report.json --meta --store memory.jsonl
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXIT_ALLOW = 0
EXIT_WARN = 2
EXIT_BLOCK = 3


# -------------------------
# Helpers: IO
# -------------------------
def load_report(path: Path) -> Dict[str, Any]:
    if not path.exists():
        print(f"[HFS VALIDATOR] Report not found: {path}")
        sys.exit(EXIT_BLOCK)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[HFS VALIDATOR] Failed to read report: {e}")
        sys.exit(EXIT_BLOCK)


def load_memory_jsonl(path: Path, limit: int = 5000) -> List[Dict[str, Any]]:
    """
    Reads JSONL store. Each line = one atom (dict).
    limit: safety guard to avoid loading huge files in CI.
    """
    if not path.exists():
        return []

    items: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except Exception:
                    # skip bad line
                    continue
    except Exception:
        return []
    return items


# -------------------------
# Meta-control (minimal)
# -------------------------
def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _dna_tokens(dna: str) -> List[str]:
    """
    DNA format examples:
      "DNA: T2 R1 P1 S1 C0 F0 W0 M1"
      "C1 L0 D2 S1 H0 E1 P1 M0"
    Tokenize into ["T2","R1",...]
    """
    dna = (dna or "").strip()
    dna = dna.replace("DNA:", "").strip()
    parts = [p.strip() for p in dna.split() if p.strip()]
    toks = [p for p in parts if len(p) >= 2 and p[0].isalpha() and p[1:].isdigit()]
    return toks


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


def meta_adjust(
    report: Dict[str, Any],
    memory_items: List[Dict[str, Any]],
    *,
    k: int = 25,
    min_matches: int = 3,
    alpha_block: float = 0.18,
    alpha_band: float = 0.06,
    max_penalty: float = 0.25,
) -> Tuple[str, float, Dict[str, Any]]:
    """
    Returns: (verdict_meta, risk_meta, meta_debug_dict)
    """
    dna_now = str(report.get("dna", ""))
    toks_now = _dna_tokens(dna_now)
    kind_now = report.get("kind")

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for it in memory_items:
        if kind_now and it.get("kind") != kind_now:
            continue

        dna_it = str(it.get("dna", ""))
        toks_it = _dna_tokens(dna_it)

        sim = _jaccard(toks_now, toks_it)

        # tiny boost if same verdict
        if it.get("verdict") == report.get("verdict"):
            sim += 0.05

        if sim > 0.0:
            scored.append((sim, it))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [it for _, it in scored[:k]]
    matched = len(top)

    # baseline thresholds can be at root or inside baseline dict
    baseline = report.get("baseline", {}) or {}
    warn_th = float(report.get("warn_threshold", baseline.get("warn_threshold", 0.0)) or 0.0)
    block_th = float(report.get("block_threshold", baseline.get("block_threshold", 1.0)) or 1.0)

    base_verdict = str(report.get("verdict", "ALLOW"))
    risk = float(report.get("risk", baseline.get("last_risk", 0.0)) or 0.0)

    if matched == 0:
        return base_verdict, risk, {
            "matched": 0,
            "penalty": 0.0,
            "risk_meta": risk,
            "verdict_meta": base_verdict,
        }

    n_block = sum(1 for it in top if it.get("verdict") == "BLOCK")
    block_rate = n_block / float(matched)

    bands = [float(it.get("band", 0.0)) for it in top if it.get("band") is not None]
    avg_band = sum(bands) / float(len(bands)) if bands else 0.0

    penalty = alpha_block * block_rate + alpha_band * (avg_band / 7.0)
    penalty = _clamp(penalty, 0.0, max_penalty)

    risk_meta = _clamp(risk + penalty, 0.0, 1.0)

    # avoid overfitting: too few matches => keep base verdict
    if matched < min_matches:
        verdict_meta = base_verdict
    else:
        if risk_meta > block_th:
            verdict_meta = "BLOCK"
        elif risk_meta > warn_th:
            verdict_meta = "WARN"
        else:
            verdict_meta = "ALLOW"

    return verdict_meta, risk_meta, {
        "matched": matched,
        "block_rate": block_rate,
        "avg_band": avg_band,
        "penalty": penalty,
        "risk_base": risk,
        "risk_meta": risk_meta,
        "verdict_base": base_verdict,
        "verdict_meta": verdict_meta,
        "warn_threshold": warn_th,
        "block_threshold": block_th,
    }


# -------------------------
# Main
# -------------------------
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("report", help="Path to report.json produced by HFS/GitCube")
    ap.add_argument("--store", default=None, help="Path to memory JSONL (e.g. memory.jsonl)")
    ap.add_argument("--meta", action="store_true", help="Enable meta-control feedback loop")

    # optional metadata (not required)
    ap.add_argument("--repo", default=None, help="Repo identifier (optional)")
    ap.add_argument("--ref", default=None, help="Commit/PR/session reference (optional)")
    return ap.parse_args()


def main():
    args = parse_args()

    report_path = Path(args.report)
    report = load_report(report_path)

    verdict = report.get("verdict", "UNKNOWN")
    dna = report.get("dna", "N/A")
    baseline = report.get("baseline", {}) or {}
    recommendation = report.get("recommendation", "")

    # --- META LOOP (optional) ---
    meta_info = None
    if args.meta and args.store:
        store_path = Path(args.store)
        items = load_memory_jsonl(store_path)

        verdict_meta, risk_meta, meta_info = meta_adjust(report, items)
        # override verdict (this is the "feedback loop")
        verdict = verdict_meta
        # reflect meta risk in printout
        report["_risk_meta"] = risk_meta

    # --- Print ---
    print("======================================")
    print(" HFS Cognitive Navigator Validation")
    print("======================================")
    print(f"Verdict        : {verdict}")
    print(f"Structural DNA : {dna}")

    # base risk + thresholds
    last_risk = baseline.get("last_risk", report.get("risk"))
    print(f"Last Risk      : {last_risk}")
    print(f"Warn Threshold : {baseline.get('warn_threshold')}")
    print(f"Block Threshold: {baseline.get('block_threshold')}")

    # meta debug (if enabled)
    if meta_info:
        print("--------------------------------------")
        print("[META] Feedback loop enabled")
        print(f"[META] matched      : {meta_info.get('matched')}")
        if "block_rate" in meta_info:
            print(f"[META] block_rate   : {round(float(meta_info.get('block_rate', 0.0)), 3)}")
        if "avg_band" in meta_info:
            print(f"[META] avg_band     : {round(float(meta_info.get('avg_band', 0.0)), 3)}")
        if "penalty" in meta_info:
            print(f"[META] penalty      : {round(float(meta_info.get('penalty', 0.0)), 3)}")
        if "risk_meta" in meta_info:
            print(f"[META] risk_meta    : {round(float(meta_info.get('risk_meta', 0.0)), 4)}")
        if "verdict_base" in meta_info:
            print(f"[META] verdict_base : {meta_info.get('verdict_base')}")
        print(f"[META] verdict_meta : {meta_info.get('verdict_meta')}")
    print("--------------------------------------")
    print(f"Recommendation : {recommendation}")
    print("======================================")

    # --- Exit codes ---
    if verdict == "ALLOW":
        print("[HFS VALIDATOR] Proceed.")
        sys.exit(EXIT_ALLOW)

    elif verdict == "WARN":
        print("[HFS VALIDATOR] Warning band activated.")
        sys.exit(EXIT_WARN)

    elif verdict == "BLOCK":
        print("[HFS VALIDATOR] BLOCK activated. Stability at risk.")
        sys.exit(EXIT_BLOCK)

    else:
        print("[HFS VALIDATOR] Unknown verdict. Failing safe.")
        sys.exit(EXIT_BLOCK)


if __name__ == "__main__":
    main()
