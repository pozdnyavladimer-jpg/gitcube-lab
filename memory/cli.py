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
import json
from typing import Optional

from .atom import MemoryAtom
from .store import MemoryStore, Query


def cmd_record(args: argparse.Namespace) -> int:
    with open(args.report, "r", encoding="utf-8") as f:
        report = json.load(f)

    # ✅ Single source of truth: build atom exactly as atom.py defines it
    atom = MemoryAtom.from_report(
        report,
        key_len=args.key_len,
        repo=args.repo,
        ref=args.ref,
        note=args.note,
    )

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
    r.add_argument("--key-len", type=int, default=3, help="How many DNA tokens to use for dna_key")
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
