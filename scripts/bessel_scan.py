# -*- coding: utf-8 -*-
"""
bessel_scan.py
Compute Bessel J_m zeros z_{m,n} (for circular membrane modes),
convert them to frequencies up to a max octave range, then map into teleport keys.

Outputs:
- data/bessel_scan.csv
- docs/bessel_scan.md (table summary)

Requires:
  pip install scipy pandas

Run:
  python scripts/bessel_scan.py --f0 110 --m-max 12 --n-max 12 --octaves 6
"""

from __future__ import annotations
import argparse
import math
import os
from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd
from scipy.special import jn_zeros

# We will reuse your teleport mapping if available
def try_import_teleport():
    try:
        import teleport  # repo root teleport.py
        return teleport
    except Exception:
        return None

def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def freq_to_octave_letter(f: float, f0: float = 110.0) -> Dict[str, Any]:
    """
    Map frequency f to:
    - octave index relative to f0 by log2
    - 24-step letter inside octave by fractional log2 * 24
    This is a pure wave->keyboard mapping (no social features).
    """
    if f <= 0 or f0 <= 0:
        return {"oct": None, "letter": None, "step24": None}

    x = math.log(f / f0, 2.0)  # octaves above f0
    oct_i = int(math.floor(x))
    frac = x - oct_i
    step24 = int(round(frac * 24)) % 24

    alphabet = "0123456789ABCDEFGHIJKLMN"
    letter = alphabet[step24]
    return {"oct": oct_i, "letter": letter, "step24": step24}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--f0", type=float, default=110.0, help="base frequency (e.g., A2=110Hz)")
    ap.add_argument("--m-max", type=int, default=12, help="max m for J_m")
    ap.add_argument("--n-max", type=int, default=12, help="max n (number of zeros per m)")
    ap.add_argument("--octaves", type=int, default=6, help="how many octaves above f0 to include")
    ap.add_argument("--out-csv", default="data/bessel_scan.csv")
    ap.add_argument("--out-md", default="docs/bessel_scan.md")
    args = ap.parse_args()

    f0 = float(args.f0)
    f_max = f0 * (2 ** int(args.octaves))

    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.out_md) or ".", exist_ok=True)

    tp = try_import_teleport()

    rows: List[Dict[str, Any]] = []

    # For a circular membrane: f_{m,n} ∝ z_{m,n}
    # We'll scale so that the smallest zero maps to f0
    z00 = jn_zeros(0, 1)[0]  # first zero of J0
    scale = f0 / float(z00)

    for m in range(0, int(args.m_max) + 1):
        zeros = jn_zeros(m, int(args.n_max))
        for n, z in enumerate(zeros, start=1):
            f = float(z) * scale
            if f > f_max:
                continue

            key_wave = freq_to_octave_letter(f, f0=f0)
            # Optional: feed into teleport if you want unify naming
            # We'll build a simple x vector from wave-only features:
            # resonance=1, entropy=0, intention=+1, structure=1, pressure=0.5, stability=1, novelty=0.5
            key_tp = None
            if tp is not None and hasattr(tp, "get_key"):
                x = [1.0, 0.0, 1.0, 1.0, 0.5, 1.0, 0.5]
                key_tp, mask, e = tp.get_key(x)
            rows.append({
                "m": m,
                "n": n,
                "z_mn": float(z),
                "freq_hz": f,
                "oct_rel": key_wave["oct"],
                "letter24": key_wave["letter"],
                "step24": key_wave["step24"],
                "teleport_example_key": key_tp,
            })

    df = pd.DataFrame(rows).sort_values(["freq_hz", "m", "n"]).reset_index(drop=True)
    df.to_csv(args.out_csv, index=False)

    # markdown summary (first 80 rows)
    head = df.head(80)
    md = []
    md.append("# Bessel scan (circular membrane modes)\n")
    md.append(f"- f0 = {f0} Hz\n")
    md.append(f"- included up to {f_max:.2f} Hz (octaves={args.octaves})\n")
    md.append("\n## First modes\n")
    md.append(head.to_markdown(index=False))
    md.append("\n")
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print("Wrote:", args.out_csv)
    print("Wrote:", args.out_md)
    print("Rows:", len(df))

if __name__ == "__main__":
    main()
