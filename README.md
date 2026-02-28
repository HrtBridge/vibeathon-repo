# Vibeathon State Engine (Prototype Brain)

This repository contains a tiny, runnable "state declaration engine" used to model a commitment-based flow.

## Core Reframe
The problem isn't scheduling. It's **commitment**.

## What this does
A small finite-state machine that:
- defines allowed transitions (guardrails)
- applies events to an entity
- produces a new state + audit log

States (example): PROPOSED → COMMITTED → AT_RISK → COMPLETED / NO_SHOW

## Run locally (Mac)
Requires Python 3.

```bash
python3 example_run.py
code .
