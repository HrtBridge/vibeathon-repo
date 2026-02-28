from datetime import datetime
from typing import Dict, Any, Optional, List

# -----------------------------
# Lifecycle Declaration Engine
# -----------------------------
#
# Core idea:
# - Owners "declare" a lifecycle state (confidential by default)
# - The declaration unlocks modules (state-specific paths)
# - Progress is tracked as lightweight percentages
# - Visibility can be toggled per declaration log entry (optional)

LIFECYCLE_STATES = [
    "GROWTH",
    "STABLE",
    "SUCCESSION_DEVELOPING",
    "EXIT_CURIOUS",
    "EMERGENCY_CONTINUITY_ONLY",
]

EVENTS = [
    "DECLARE_STATE",
    "TOGGLE_PUBLIC_VISIBILITY",
    "COMPLETE_MODULE_STEP",
]

# Which modules unlock for each lifecycle state (minimal, demo-focused)
STATE_MODULES = {
    "GROWTH": [
        "succession_reflection_10yr",
        "emergency_continuity_plan",
    ],
    "STABLE": [
        "emergency_continuity_plan",
        "succession_reflection_10yr",
        "governance_docs_checklist",
    ],
    "SUCCESSION_DEVELOPING": [
        "succession_readiness_checklist",
        "timeline_builder",
        "overlap_planning_explainer",
    ],
    "EXIT_CURIOUS": [
        "readiness_checklist",
        "timeline_builder",
        "valuation_conversation_starter",
        "financing_pathways_resources",
    ],
    "EMERGENCY_CONTINUITY_ONLY": [
        "emergency_continuity_plan",
    ],
}

def utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"

def clamp_pct(x: int) -> int:
    return max(0, min(100, x))

def new_profile(business_id: str, owner_id: str) -> Dict[str, Any]:
    return {
        "business_id": business_id,
        "owner_id": owner_id,
        "state": "STABLE",  # default; can be changed via DECLARE_STATE
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "modules_progress": {},  # module_key -> pct
        "visibility": "PRIVATE",  # default for latest declaration entry
        "log": [],  # audit log of declarations and progress
    }

def unlocked_modules(state: str) -> List[str]:
    return STATE_MODULES.get(state, [])

def apply_event(
    profile: Dict[str, Any],
    event_type: str,
    by: str = "OWNER",
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    meta = meta or {}
    current_state = profile.get("state")

    if event_type not in EVENTS:
        raise ValueError(f"Unknown event_type: {event_type}")

    if event_type == "DECLARE_STATE":
        new_state = meta.get("state")
        if new_state not in LIFECYCLE_STATES:
            raise ValueError(f"Invalid lifecycle state: {new_state}")

        # Default behavior: declarations are private unless explicitly public.
        visibility = meta.get("visibility", "PRIVATE")
        if visibility not in ["PRIVATE", "PUBLIC"]:
            raise ValueError("visibility must be PRIVATE or PUBLIC")

        profile["state"] = new_state
        profile["visibility"] = visibility

        # Initialize progress for newly unlocked modules (if absent)
        for module in unlocked_modules(new_state):
            profile["modules_progress"].setdefault(module, 0)

    elif event_type == "TOGGLE_PUBLIC_VISIBILITY":
        # toggles latest declaration visibility (or sets explicitly)
        visibility = meta.get("visibility")
        if visibility is None:
            profile["visibility"] = "PUBLIC" if profile.get("visibility") == "PRIVATE" else "PRIVATE"
        else:
            if visibility not in ["PRIVATE", "PUBLIC"]:
                raise ValueError("visibility must be PRIVATE or PUBLIC")
            profile["visibility"] = visibility

    elif event_type == "COMPLETE_MODULE_STEP":
        module = meta.get("module")
        delta = meta.get("delta_pct", 10)
        if not module or not isinstance(module, str):
            raise ValueError("meta.module is required")

        # Only allow progress on currently unlocked modules
        if module not in unlocked_modules(profile["state"]):
            raise ValueError(f"Module '{module}' is not unlocked for state '{profile['state']}'")

        current = int(profile["modules_progress"].get(module, 0))
        profile["modules_progress"][module] = clamp_pct(current + int(delta))

    profile["updated_at"] = utc_now()
    profile.setdefault("log", []).append({
        "event": event_type,
        "by": by,
        "at": profile["updated_at"],
        "meta": meta
    })
    return profile
