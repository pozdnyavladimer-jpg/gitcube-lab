# -*- coding: utf-8 -*-
"""CLI for Topological Memory.

Two commands:
- record: convert a GitCube/HFS JSON report into a MemoryAtom and append it to JSONL
- query : search the JSONL store

Examples:
  python -m memory.cli record --report report.json --store memory/memory.jsonl --repo my/repo --ref PR#12
  python -m memory.cli query --store memory/memory.jsonl --verdict BLOCK --limit 10
"""

from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any, Dict, Optional

from .atom import MemoryAtom
from .bands import risk_to_band
from .store import MemoryStore, Query


def _get(d: Dict[str, Any], *path: str, default=None):
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur


def _stable_dna_key(dna: str) -> str:
    """Stable identifier derived from DNA when producer doesn't provide dna_key."""
    dna = (dna or "").encode("utf-8")
    return hashlib.sha256(dna).hexdigest()[:16]


def atom_from_report(
    report: Dict[str, Any], *, repo: Optional[str], ref: Optional[str], note: Optional[str]
) -> MemoryAtom:
    # kind / version
    kind = str(report.get("kind") or report.get("type") or "REPORT")
    version = str(report.get("version") or report.get("schema_version") or "0")

    # verdict normalization
    verdict = str(report.get("verdict") or _get(report, "action", "recommendation") or "ALLOW").upper()
    if verdict not in {"ALLOW", "WARN", "BLOCK"}:
        verdict = "ALLOW"

    # dna / dna_key
    dna = str(report.get("dna") or _get(report, "topology", "dna") or _get(report, "metrics", "dna") or "")
    dna_key = str(
        report.get("dna_key")
        or _get(report, "topology", "dna_key")
        or _get(report, "metrics", "dna_key")
        or _stable_dna_key(dna)
    )

    # risk location differs by producer
    risk = _get(report, "baseline", "last_risk", default=None)
    if risk is None:
        risk = report.get("risk")
    if risk is None:
        # fallback: use entropy_score if present
        risk = _get(report, "metrics", "entropy_score", default=0.0)
    risk = float(risk or 0.0)

    # baseline stats (may be missing)
    mu = float(_get(report, "baseline", "mu", default=0.0) or 0.0)
    sigma = float(_get(report, "baseline", "sigma", default=0.0) or 0.0)
    warn_th = float(_get(report, "baseline", "warn_threshold", default=0.0) or 0.0)
    block_th = float(_get(report, "baseline", "block_threshold", default=0.0) or 0.0)

    # If thresholds are missing, derive simple ones for storage purposes
    if warn_th == 0.0 and block_th == 0.0 and sigma > 0.0:
        warn_th = mu + 2.0 * sigma
        block_th = mu + 3.0 * sigma

    band = int(risk_to_band(risk))

    # metrics payload (optional)
    metrics = report.get("metrics") or report.get("metrics_last_window") or None

    # IMPORTANT: MemoryAtom in your repo does NOT accept `t=...`
    # and (from your signature) requires at least: kind, version, verdict, dna, dna_key, band
    atom = MemoryAtom(
        kind=kind,
        version=version,
        verdict=verdict,
        dna=dna,
        dna_key=dna_key,
        band=band,
    )

    # Optional enrichment (only if MemoryAtom supports these attrs)
    # If MemoryAtom is a dataclass with frozen=False or defines these fields, set them.
    for k, v in {
        "risk": risk,
        "mu": mu,
        "sigma": sigma,
        "warn_threshold": warn_th,
        "block_threshold": block_th,
        "repo": repo,
        "ref": ref,
        "note": note,
        "metrics": metrics,
    }.items():
        if hasattr(atom, k):
            try:
                setattr(atom, k, v)
            except Exception:
                # If frozen / read-only, just ignore.
                pass

    return atom


def cmd_record(args: argparse.Namespace) -> int:
    with open(args.report, "r", encoding="utf-8") as f:
        report = json.load(f)

    atom = atom_from_report(report, repo=args.repo, ref=args.ref, note=args.note)
    MemoryStore(args.store).append(atom)

    if not args.quiet:
        print(json.dumps(atom.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    q = Query(
        verdict=args.verdict,
        band_min=args.band_min,
        band_max=args.band_max,
        dna_contains=args.contains,
        kind=args.kind,
        limit=args.limit,
    )
    rows = MemoryStore(args.store).query(q)
    print(json.dumps({"count": len(rows), "items": rows}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="gitcube-memory")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="Record a JSON report as a Memory Atom")
    r.add_argument("--report", required=True, help="Path to GitCube/HFS JSON report")
    r.add_argument("--store", default="memory/memory.jsonl", help="JSONL store path")
    r.add_argument("--repo", default=None, help="Repo identifier (optional)")
    r.add_argument("--ref", default=None, help="Commit/PR/session reference (optional)")
    r.add_argument("--note", default=None, help="Short note (optional)")
    r.add_argument("--quiet", action="store_true")
    r.set_defaults(func=cmd_record)

    q = sub.add_parser("query", help="Query the Memory Store")
    q.add_argument("--store", default="memory/memory.jsonl")
    q.add_argument("--verdict", default=None, choices=["ALLOW", "WARN", "BLOCK"], help="Filter by verdict")
    q.add_argument("--band-min", type=int, default=None)
    q.add_argument("--band-max", type=int, default=None)
    q.add_argument("--contains", default=None, help="Substring match inside DNA")
    q.add_argument("--kind", default=None, help="Filter by report kind")
    q.add_argument("--limit", type=int, default=50)
    q.set_defaults(func=cmd_query)

    return ap


def main(argv=None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
