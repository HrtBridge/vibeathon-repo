# Scenario Walkthrough

## Scenario: Appointment Commitment Flow

Initial state:
PROPOSED

1. Patient captures commitment (deposit hold OR reconfirm)
→ COMMITTED

2. No reconfirmation window elapses
→ AT_RISK

3. Patient reconfirms
→ COMMITTED

4. Patient checks in
→ COMPLETED

## Why This Matters

Traditional scheduling systems track time.
This engine tracks commitment.

The difference:
- Less no-shows
- Automatic risk detection
- Enforceable state transitions
