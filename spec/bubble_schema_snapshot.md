# Bubble Schema Snapshot

This file is generated from the CSV headers in `bubble_exports/`.

## lifecycle_declarations

- File: `bubble_exports/lifecycle_declarations.csv`

### Columns

- `(Linked) Lifecycle_Profile`
- `(Linked) Lifecycle_Stage`
- `ai_recommendations`
- `bigq_score`
- `bigq_why`
- `created_at`
- `privacy`

## lifecycle_modules

- File: `bubble_exports/lifecycle_modules.csv`

### Columns

- `(Linked) Lifecycle_Profile_did_complete`
- `(Linked) Lifecycle_Stage`
- `create_on`
- `description`
- `module_type`
- `ModuleTypeChecklist_list`
- `ModuleTypeForm_Question`

## lifecycle_stages

- File: `bubble_exports/lifecycle_stages.csv`

### Columns

- `short_description`
- `long_description`
- `name`
- `Creation Date`
- `Modified Date`
- `Slug`
- `Creator`

## lifecycle_profiles

- File: `bubble_exports/lifecycle_profiles.csv`

### Columns

- `(Linked) Lifecycle_Declaration`
- `(Linked) Lifecycle_Stage`
- `(Linked) Module_Responses`
- `business_name`
- `created_on`
- `email`
- `progress_emergency_continuity_plan`

## module_responses

- File: `bubble_exports/module_responses.csv`

### Columns

- `(Linked) Lifecycle_Module`
- `(Linked) Lifecycle_Profile`
- `response_text`
- `status`
- `updated_at`
- `Creation Date`
- `Modified Date`

## users

- File: `bubble_exports/users.csv`

### Columns

- `(Linked) Lifecycle_Profile`
- `Creation Date`
- `Modified Date`
- `Slug`
- `email`
