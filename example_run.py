from state_engine import apply_event

entity = {
    "id": "apt_001",
    "state": "PROPOSED",
    "created_at": "2026-02-28T11:30:00-06:00",
    "updated_at": "2026-02-28T11:30:00-06:00",
    "log": []
}

print("Initial:", entity["state"])

entity = apply_event(entity, "CAPTURE_COMMITMENT", by="PATIENT", meta={"method": "deposit_hold_optional"})
print("After commitment:", entity["state"])

entity = apply_event(entity, "FLAG_AT_RISK", by="SYSTEM", meta={"reason": "no_reconfirm_window_elapsed"})
print("After at-risk:", entity["state"])

entity = apply_event(entity, "CAPTURE_COMMITMENT", by="PATIENT", meta={"method": "reconfirm"})
print("After reconfirm:", entity["state"])

entity = apply_event(entity, "CHECK_IN", by="CLINIC")
print("After check-in:", entity["state"])

print("\nEvent log:")
for e in entity["log"]:
    print(e)
