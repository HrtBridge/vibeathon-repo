# Continuum — Architecture Overview

Continuum is a lifecycle-state declaration system designed to normalize early succession preparation for rural businesses.

This repository contains:
- A Bubble-built UI prototype (exported)
- Bubble data exports (CSV)
- A behavior contract documenting Bubble workflows
- A runnable Python reference engine that mirrors the prototype logic and demonstrates the system without UI

## Repo map

### 1) UI prototype (Bubble)
- `bubble_app/continuum-81071.bubble`
  - Bubble export file representing the application shown in the demo video.

### 2) Prototype data (CSV exports)
- `bubble_exports/*.csv`
  - Exports of Bubble database tables used in the prototype.

### 3) Behavior contract (implemented Bubble logic)
- `spec/bubble_behavior_contract.md`
  - Mechanical description of triggers, writes, and rules used in Bubble.

### 4) Reference engine (runnable logic brain)
- `state_engine/engine.py`
  - Implements the core lifecycle rules, module selection, completion tracking, and admin aggregation.
- `state_engine/demo.py`
  - Runs an end-to-end simulation matching the demo narrative.

### 5) Tooling
- `tools/inspect_bubble_export.py`
  - Confirms the Bubble export is JSON and prints summary counts.

## Core domain concepts

- **Lifecycle_Profile**: a business identity (name, email).
- **Lifecycle_Declaration**: a timestamped declaration containing BigQ + lifecycle stage (+ privacy).
- **Lifecycle_Stage**: one of four stages: Growth, Stable, Exit Curious, Transition Seeking.
- **Lifecycle_Module**: a readiness module linked to a stage (URL, checklist, or form).
- **Completion**: in the Bubble prototype, completion is stored on the module as a list of completed profiles.

## Privacy model
- There is no public log in the current prototype.
- The admin dashboard is gated behind an allowlisted admin email.
- Admin views show aggregated counts and internal listings, and any lifecycle_declarations set to public by the business owner user.