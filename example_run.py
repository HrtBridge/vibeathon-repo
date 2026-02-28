from state_engine import new_profile, apply_event, unlocked_modules

profile = new_profile(business_id="biz_001", owner_id="owner_001")

print("Initial state:", profile["state"])
print("Unlocked modules:", unlocked_modules(profile["state"]))

# 1) Owner declares a lifecycle state (confidential by default)
profile = apply_event(profile, "DECLARE_STATE", by="OWNER", meta={"state": "EXIT_CURIOUS", "visibility": "PRIVATE"})
print("\nAfter DECLARE_STATE:", profile["state"], "| visibility:", profile["visibility"])
print("Unlocked modules:", unlocked_modules(profile["state"]))

# 2) Owner completes a step (progress indicator)
profile = apply_event(profile, "COMPLETE_MODULE_STEP", by="OWNER", meta={"module": "timeline_builder", "delta_pct": 20})
profile = apply_event(profile, "COMPLETE_MODULE_STEP", by="OWNER", meta={"module": "readiness_checklist", "delta_pct": 10})

print("\nProgress:")
for k, v in profile["modules_progress"].items():
    print(f" - {k}: {v}%")

# 3) Optional: owner chooses to make the declaration public later
profile = apply_event(profile, "TOGGLE_PUBLIC_VISIBILITY", by="OWNER", meta={"visibility": "PUBLIC"})
print("\nAfter TOGGLE_PUBLIC_VISIBILITY:", profile["visibility"])

print("\nEvent log:")
for e in profile["log"]:
    print(e)
