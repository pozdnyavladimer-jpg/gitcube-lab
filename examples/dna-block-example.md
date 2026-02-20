# DNA Example — BLOCK Case

## PR change
+ payments.api -> core.db

## GitCube Result

DNA: C2 H1 S0 D1 L1 E1 P1 M1  
Verdict: BLOCK  

Reason:
Edge creates a cycle.
Path core.db → payments.api already exists.

Suggested structural fix:
Introduce payments.port interface and invert dependency.
