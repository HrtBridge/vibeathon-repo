import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


# Bubble export field names we rely on
MODULE_COMPLETED_LIST_FIELD = "(Linked) Lifecycle_Profile_did_complete"
PROFILE_STAGE_FIELD = "(Linked) Lifecycle_Stage"
MODULE_STAGE_FIELD = "(Linked) Lifecycle_Stage"
DECL_STAGE_FIELD = "(Linked) Lifecycle_Stage"
DECL_PROFILE_FIELD = "(Linked) Lifecycle_Profile"


def _detect_id_field(rows: List[dict]) -> str:
    """
    Bubble CSV exports commonly use 'Unique ID'.
    Sometimes exports use '_id' or similar. We auto-detect.
    """
    if not rows:
        return "Unique ID"
    keys = set(rows[0].keys())
    for candidate in ("Unique ID", "_id", "unique_id", "uid", "ID"):
        if candidate in keys:
            return candidate
    # last resort: pick any column containing 'id'
    for k in rows[0].keys():
        if "id" in k.lower():
            return k
    return "Unique ID"


def _split_list(cell: Optional[str]) -> List[str]:
    if not cell:
        return []
    return [x.strip() for x in cell.split(",") if x.strip()]


@dataclass
class Profile:
    uid: str
    business_name: str
    email: str
    current_stage_uid: Optional[str]


@dataclass
class Stage:
    uid: str
    name: str
    description: str


@dataclass
class Module:
    uid: str
    title: str
    module_type: str
    stage_uid: Optional[str]
    completed_profiles: List[str]


class ContinuumEngine:
    def __init__(self, exports_dir: str):
        self.exports_dir = exports_dir
        self.profiles: Dict[str, Profile] = {}
        self.stages: Dict[str, Stage] = {}
        self.modules: Dict[str, Module] = {}
        self.declarations: List[dict] = []
        self.module_responses: List[dict] = []

        # Debug / transparency
        self.id_field_profiles: Optional[str] = None
        self.id_field_stages: Optional[str] = None
        self.id_field_modules: Optional[str] = None
        self.id_field_decls: Optional[str] = None
        self.profile_stage_field_used: Optional[str] = None

    def _load_csv(self, filename: str) -> List[dict]:
        path = os.path.join(self.exports_dir, filename)
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def load(self):
        # --- stages ---
        stage_rows = self._load_csv("lifecycle_stages.csv")
        self.id_field_stages = _detect_id_field(stage_rows)
        for r in stage_rows:
            uid = (r.get(self.id_field_stages) or "").strip()
            if not uid:
                continue
            self.stages[uid] = Stage(
                uid=uid,
                name=r.get("name", "") or r.get("Name", ""),
                description=r.get("long_description", "") or r.get("description", "") or r.get("Description", ""),
            )

        # --- profiles ---
        profile_rows = self._load_csv("lifecycle_profiles.csv")
        self.id_field_profiles = _detect_id_field(profile_rows)
        for r in profile_rows:
            uid = (r.get(self.id_field_profiles) or "").strip()
            if not uid:
                continue

            # Detect whether profile has stage field populated
            stage_uid = (r.get(PROFILE_STAGE_FIELD) or "").strip() or None
            if stage_uid and not self.profile_stage_field_used:
                self.profile_stage_field_used = PROFILE_STAGE_FIELD
            elif not stage_uid and self.profile_stage_field_used is None:
                # keep as None; demo can still show it if populated later
                pass

            self.profiles[uid] = Profile(
                uid=uid,
                business_name=r.get("business_name", "") or r.get("Business Name", "") or r.get("name", "") or r.get("Name", ""),
                email=r.get("email", "") or r.get("Email", ""),
                current_stage_uid=stage_uid,
            )

        # --- modules ---
        module_rows = self._load_csv("lifecycle_modules.csv")
        self.id_field_modules = _detect_id_field(module_rows)
        for r in module_rows:
            uid = (r.get(self.id_field_modules) or "").strip()
            if not uid:
                continue
            completed_list = _split_list(r.get(MODULE_COMPLETED_LIST_FIELD) or "")
            self.modules[uid] = Module(
                uid=uid,
                title=r.get("title", "") or r.get("Title", "") or r.get("name", "") or r.get("Name", "") or "(untitled module)",
                module_type=r.get("module_type", "") or r.get("Module Type", "") or r.get("type", ""),
                stage_uid=((r.get(MODULE_STAGE_FIELD) or "").strip() or None),
                completed_profiles=completed_list,
            )

        # --- declarations ---
        decl_rows = self._load_csv("lifecycle_declarations.csv")
        self.id_field_decls = _detect_id_field(decl_rows)
        self.declarations = decl_rows

        # --- module responses (Bubble readiness density) ---
        try:
            self.module_responses = self._load_csv("module_responses.csv")
        except FileNotFoundError:
            self.module_responses = []

    def latest_declared_stage_uid_for_profile(self, profile_uid: str) -> Optional[str]:
        latest = None
        latest_time = ""
        for r in self.declarations:
            pid = (r.get(DECL_PROFILE_FIELD) or "").strip()
            if pid != profile_uid:
                continue
            ts = (r.get("created_at") or r.get("Creation Date") or r.get("Created Date") or r.get("creation_date") or "").strip()
            if ts >= latest_time:
                latest_time = ts
                latest = r
        if not latest:
            return None
        return ((latest.get(DECL_STAGE_FIELD) or "").strip() or None)

    def current_stage_uid(self, profile_uid: str) -> Optional[str]:
        p = self.profiles.get(profile_uid)
        if not p:
            return None
        if p.current_stage_uid:
            return p.current_stage_uid
        return self.latest_declared_stage_uid_for_profile(profile_uid)

    def current_stage(self, profile_uid: str) -> Optional[Stage]:
        stage_uid = self.current_stage_uid(profile_uid)
        if not stage_uid:
            return None
        return self.stages.get(stage_uid)

    def modules_for_profile(self, profile_uid: str, view_all: bool = False) -> List[Module]:
        stage_uid = self.current_stage_uid(profile_uid)
        if view_all or not stage_uid:
            return list(self.modules.values())
        return [m for m in self.modules.values() if m.stage_uid == stage_uid]

    def is_complete(self, profile_uid: str, module_uid: str) -> bool:
        m = self.modules.get(module_uid)
        if not m:
            return False
        return profile_uid in m.completed_profiles

    def readiness_percent(self, profile_uid: str) -> int:
        mods = self.modules_for_profile(profile_uid)
        if not mods:
            return 0
        complete = sum(1 for m in mods if self.is_complete(profile_uid, m.uid))
        return int(round((complete / len(mods)) * 100))

    def admin_distribution_by_stage_name(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self.declarations:
            stage_uid = (r.get(DECL_STAGE_FIELD) or "").strip()
            if not stage_uid:
                continue
            name = self.stages.get(stage_uid).name if stage_uid in self.stages else stage_uid
            counts[name] = counts.get(name, 0) + 1
        return counts

    def community_readiness_density_percent(self) -> int:
        """
        Mirrors Bubble dashboard hack:
        Module_Responses:count / (Lifecycle_Modules:count * Lifecycle_Profiles:count)
        Interpreted as % of all possible module completions completed across community.
        """
        profiles = len(self.profiles)
        modules = len(self.modules)
        if profiles == 0 or modules == 0:
            return 0
        responses = len(self.module_responses)
        pct = (responses / (modules * profiles)) * 100
        return int(round(pct))
