# GitCube Kernel Overview

## What is the “Kernel” here?
A small, explainable core that converts continuous signals into:
- **telemetry** (metrics like R, H, K)
- **discrete modes** (octaves/letters a.k.a. a “keyboard”)
- **actions** (controllers that mitigate instability)

This repo keeps a strict separation:
- **Engine math** (kuramoto13.py, teleport.py)
- **Applications** (apps/vr_comfort/*)

## 1) Kuramoto-13 engine
File: `kuramoto13.py`

- Simulates 13 coupled oscillators.
- Tracks:
  - `R(t)` synchronization (0..1)
  - `H(t)` phase entropy (0..1)
  - `K(t)` coupling strength (controller output)
- Emits **CRYSTAL** event when:
  - `R >= R_gate` and `H <= H_gate` for `hold_steps`.

This gives a measurable “stable attractor” detection.

## 2) Discrete “Keyboard” mapping (Octaves + Letters)
File: `teleport.py`

- Converts a continuous feature vector `x` into:
  - **Octave** O1..O7 (coarse level)
  - **Letter** (stable pattern derived from topology bitmask)

This is useful for:
- dashboards/panels
- stable labels for states
- UI mapping (buttons, modes)

## 3) VR Comfort Kernel (Adaptive Comfort Controller)
Files:
- `apps/vr_comfort/vestibular_kernel.py`
- `apps/vr_comfort/demo_vr_comfort.py`

- Computes discomfort proxy `H_vr` from mismatch of:
  - head angular velocity vs camera angular velocity
  - camera acceleration
- Uses hysteresis to avoid oscillations.
- Outputs mitigation parameters:
  - vignette strength
  - acceleration scaling
  - smoothing
  - reference frame hint

This is a practical example of how a “Kernel” becomes a controller in a real system.

## Next step (optional)
Add a recorder that writes CRYSTAL events into a JSONL store (memory.jsonl).
