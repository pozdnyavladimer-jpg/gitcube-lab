# JSON Schema sketch (v2)

```json
{
  "tool": "gitcube-core",
  "engine": "V-CORE SriYantra Engine",
  "graph": { "nodes": 123, "edges": 456 },
  "baseline": {
    "enabled": true,
    "path": ".gitcube/baseline.json",
    "version": 1,
    "stats": {
      "H_mean": 0.018,
      "H_std": 0.004,
      "SCC_mass_mean": 0.010,
      "SCC_mass_std": 0.006
    }
  },
  "metrics": {
    "H": 0.0195,
    "delta_H": 0.0012,
    "SCC_mass": 0.031,
    "delta_SCC_mass": 0.021,
    "cycle_forming_edges": 1
  },
  "thresholds": {
    "delta_H_warn": 2.0,
    "delta_H_block": 3.5,
    "delta_SCC_mass_warn": 2.0,
    "delta_SCC_mass_block": 3.5,
    "cycle_forming_edges_block": 1
  },
  "dna": {
    "signature": "G1 P1 C1 M1 D0 T1 E1 K1",
    "symbols": {
      "G": {"level": 1, "meaning": "WARN"},
      "P": {"level": 1, "value": 0.0012, "explain": "ΔH above baseline"},
      "C": {"level": 1, "value": 1, "explain": "cycle-forming edge detected"},
      "M": {"level": 1, "value": 0.021, "explain": "SCC mass jump"},
      "D": {"level": 0, "value": 0.04},
      "T": {"level": 1, "z": 2.1},
      "E": {"level": 1, "top_edges": ["payments.api->core.db"]},
      "K": {"level": 1, "bucket": "S"}
    }
  },
  "action": {
    "recommendation": "WARN",
    "note": "trend: structural pressure rising",
    "required": ""
  },
  "warnings": []
}
```

Notes:
- `*_warn` and `*_block` can be Z-score thresholds (e.g. 2σ / 3.5σ) or quantiles.
- `K.bucket` example: XS/S/M/L/XL by node count.
