# -*- coding: utf-8 -*-
"""
CLI for Topological Memory.

Commands:
- record: convert a JSON report into a MemoryAtom and upsert into JSONL
- query : search the JSONL store
- stats : quick store stats
"""

from __future__ import annotations

import argparse
import json

from .atom import MemoryAtom
from .store import MemoryStore, Query


def cmd_record(args: argparse.Namespace) -> int:
    with open(args.report, "r", encoding="utf-8") as f:
        report = json.load(f)

    atom = MemoryAtom.from_report(
        report,
        key_len=args.key_len,
        repo=args.repo,
        ref=args.ref,
        note=args.note,
        cusum_gate=args.cusum_gate,
    )

    stored = MemoryStore(args.store).upsert(
        atom,
        flower_gate=args.flower_gate,
        flower_bonus=args.flower_bonus,
    )

    if not args.quiet:
        print(json.dumps(stored.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    q = Query(
        verdict=args.verdict,
        band_min=args.band_min,
        band_max=args.band_max,
        phase_state=args.phase_state,
        dna_contains=args.contains,
        dna_key=args.dna_key,
        kind=args.kind,
        min_strength=args.min_strength,
        limit=args.limit,
    )
    rows = MemoryStore(args.store).query(q)
    print(json.dumps({"count": len(rows), "items": rows}, ensure_ascii=False, indent=2))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    s = MemoryStore(args.store).stats()
    print(json.dumps(s, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="gitcube-memory")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="Record a JSON report as a Memory Atom (merge/upsert)")
    r.add_argument("--report", required=True, help="Path to JSON report")
    r.add_argument("--store", default="memory/memory.jsonl", help="JSONL store path")
    r.add_argument("--repo", default=None, help="Repo identifier (optional)")
    r.add_argument("--ref", default=None, help="Commit/PR/session reference (optional)")
    r.add_argument("--note", default=None, help="Short note (optional)")
    r.add_argument("--key-len", type=int, default=3, help="How many DNA tokens to use for dna_key")
    r.add_argument("--cusum-gate", type=float, default=0.05, help="Shadow dominance gate for Δcusum")

    # flower knobs (optional)
    r.add_argument("--flower-gate", type=float, default=0.01, help="Petal area gate for bonus strength")
    r.add_argument("--flower-bonus", type=int, default=1, help="Bonus strength if petal_area>=gate")

    r.add_argument("--quiet", action="store_true")
    r.set_defaults(func=cmd_record)

    q = sub.add_parser("query", help="Query the Memory Store")
    q.add_argument("--store", default="memory/memory.jsonl")
    q.add_argument("--verdict", default=None, choices=["ALLOW", "WARN", "BLOCK"], help="Filter by verdict")
    q.add_argument("--band-min", type=int, default=None)
    q.add_argument("--band-max", type=int, default=None)
    q.add_argument("--phase-state", type=int, default=None, help="1..42 exact phase_state filter")
    q.add_argument("--dna-key", default=None, help="Exact dna_key match")
    q.add_argument("--contains", default=None, help="Substring match inside DNA")
    q.add_argument("--kind", default=None, help="Filter by report kind")
    q.add_argument("--min-strength", type=int, default=None, help="Only atoms with strength >= N")
    q.add_argument("--limit", type=int, default=50)
    q.set_defaults(func=cmd_query)

    s = sub.add_parser("stats", help="Store statistics")
    s.add_argument("--store", default="memory/memory.jsonl")
    s.set_defaults(func=cmd_stats)

    return ap


def main(argv=None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
