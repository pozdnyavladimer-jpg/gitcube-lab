# HFS (Human Function Stream) — Schema v0.1

HFS is a minimal, append-only event stream that describes *human-machine interaction*
as machine-readable JSON lines (one event per line).

Goal: make "human noise" measurable, so an AI can act as a Navigator:
ALLOW / WARN / BLOCK + a compact Structural DNA signature.

---

## Event (one JSON per line)

Required fields:

- `t` (float) — unix timestamp seconds (or monotonic seconds)
- `channel` (string) — `chat | git | ide | web | vr`
- `event` (string) — `message | edit | commit | click | pause | error`
- `payload` (object) — event-specific data
- `features` (object) — lightweight numeric signals (optional)

Example:

```json
{"t": 1710000000.12, "channel":"chat", "event":"message",
 "payload":{"text":"I want to build a navigator"}, 
 "features":{"len":27, "edits":0, "pause_s":0.4}}
