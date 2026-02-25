import argparse, json, os, sys

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--noise_sigma", type=float, default=0.0)
    p.add_argument("--beta", type=float, default=0.3)

    # ⬇️ ДОДАТИ:
    p.add_argument("--report_path", type=str, default="")
    p.add_argument("--trace_path", type=str, default="")

    return p.parse_args()
