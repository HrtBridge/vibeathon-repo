from datetime import datetime

ALLOWED_TRANSITIONS = {
    "PROPOSED": ["CAPTURE_COMMITMENT", "CANCEL"],
    "COMMITTED": ["FLAG_AT_RISK", "CHECK_IN", "RESCHEDULE", "CANCEL"],
    "AT_RISK": ["CAPTURE_COMMITMENT", "MARK_NO_SHOW", "RESCHEDULE", "CANCEL"],
    "COMPLETED": [],
    "NO_SHOW": [],
    "CANCELLED": []
}

NEXT_STATE = {
    "CAPTURE_COMMITMENT": "COMMITTED",
    "FLAG_AT_RISK": "AT_RISK",
    "CHECK_IN": "COMPLETED",
    "MARK_NO_SHOW": "NO_SHOW",
    "RESCHEDULE": "PROPOSED",
    "CANCEL": "CANCELLED"
}

def apply_event(entity: dict, event_type: str, by: str = "SYSTEM", meta: dict | None = None) -> dict:
    current_state = entity["state"]
    allowed = ALLOWED_TRANSITIONS.get(current_state, [])
    if event_type not in allowed:
        raise ValueError(f"Event '{event_type}' not allowed from state '{current_state}'")

    entity["state"] = NEXT_STATE.get(event_type, current_state)
    entity["updated_at"] = datetime.utcnow().isoformat() + "Z"
    entity.setdefault("log", []).append({
        "event": event_type,
        "by": by,
        "at": entity["updated_at"],
        "meta": meta or {}
    })
    return entity
