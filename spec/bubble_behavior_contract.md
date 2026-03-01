# Bubble Behavior Contract (Continuum Prototype)

This document describes the implemented Bubble logic that the demo video showcases.

## Enums / field conventions
- Lifecycle stages: Growth, Stable, Exit Curious, Transition Seeking (stored as linked `Lifecycle_Stage` in Bubble)
- Module types:
  - URL → field: `ModuleTypeURL_link`
  - CHECKLIST → field: `ModuleTypeChecklist_list` (list of text)
  - FORM → field: `ModuleTypeForm_Question` (text)
- Admin gating (current): only `brentrosenauer@gmail.com`

## Core flows

### F1 — BigQ entry (logged out)
Trigger:
- Logged-out user submits BigQ on the form module.

Behavior:
- Create a new `Lifecycle_Declaration` when BigQ is submitted.
- Save: `bigq_score`, `bigq_why`, `created_at`
- Continue the multi-step form and update the SAME `Lifecycle_Declaration` with selected `Lifecycle_Stage`.
- During the flow, a `Lifecycle_Profile` may be created/linked using business name + email.

### F2 — Lifecycle Stage declaration (logged in)
Trigger:
- Logged-in user submits stage selection from dashboard.

Behavior:
- Create a new `Lifecycle_Declaration` on submit (stage-only flow).
- Save: `lifecycle_stage`, `created_at`

### F3 — Current stage derivation
Behavior:
- After each declaration, the user's `Lifecycle_Profile` is updated with the latest declared `Lifecycle_Stage`.
- Dashboard uses `Lifecycle_Profile.current_stage` (or equivalent field) as the source of truth.

### F4 — Module selection
Behavior:
- Dashboard filters `Lifecycle_Modules` to those linked to the user's current `Lifecycle_Stage`.
- "View All" shows all modules.
- Completion status is shown by checking whether the current user's `Lifecycle_Profile` is on the module's completed-profiles list.

### F5 — Module open & completion
Behavior:
- Clicking a module opens a module form. UI branches by `module_type`:
  - URL: shows a button that opens `ModuleTypeURL_link`
  - CHECKLIST: shows checklist items from `ModuleTypeChecklist_list`
  - FORM: shows one question from `ModuleTypeForm_Question` with multiline input
- On "Complete", workflow adds current user's `Lifecycle_Profile` to the module's completed-profiles list.

### F6 — Admin dashboard access
Access control:
- Admin dashboard visible only when Current User email = `brentrosenauer@gmail.com`

### F7 — Admin module creation
Behavior:
- Users with admin privileges can create `Lifecycle_Modules` via an admin form, setting:
  - linked `Lifecycle_Stage`
  - `module_type`
  - type-specific fields