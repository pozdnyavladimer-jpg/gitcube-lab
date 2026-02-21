# -*- coding: utf-8 -*-
"""
AI Validator for HFS Navigator
License: AGPL-3.0
Author: Володимир Поздняк

Reads HFS Navigator JSON report and enforces:
- ALLOW → exit 0
- WARN  → exit 2
- BLOCK → exit 3

Usage:
  python hfs/ai_validator_hfs.py report.json
"""

import sys
import json
from pathlib import Path


EXIT_ALLOW = 0
EXIT_WARN = 2
EXIT_BLOCK = 3


def load_report(path: Path):
    if not path.exists():
        print(f"[HFS VALIDATOR] Report not found: {path}")
        sys.exit(EXIT_BLOCK)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[HFS VALIDATOR] Failed to read report: {e}")
        sys.exit(EXIT_BLOCK)


def main():
    if len(sys.argv) < 2:
        print("Usage: python hfs/ai_validator_hfs.py report.json")
        sys.exit(EXIT_BLOCK)

    report_path = Path(sys.argv[1])
    report = load_report(report_path)

    verdict = report.get("verdict", "UNKNOWN")
    dna = report.get("dna", "N/A")
    baseline = report.get("baseline", {})
    recommendation = report.get("recommendation", "")

    print("======================================")
    print(" HFS Cognitive Navigator Validation")
    print("======================================")
    print(f"Verdict       : {verdict}")
    print(f"Structural DNA: {dna}")
    print(f"Last Risk     : {baseline.get('last_risk')}")
    print(f"Warn Threshold: {baseline.get('warn_threshold')}")
    print(f"Block Threshold: {baseline.get('block_threshold')}")
    print("--------------------------------------")
    print(f"Recommendation: {recommendation}")
    print("======================================")

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
