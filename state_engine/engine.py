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
    Sometimes exports use '_id' or 'unique_id'. We auto-detect.
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

        # Debug / transparency
        self.id_field_profiles: Optional[str] = None
        self.id_field_stages: Optional[str] = None
        self.id_field_modules: Optional[str] = None
        self.id_field_decls: Optional[str] = None

    def _load_csv(self, filename: str) -> List[dict]:
        path = os.path.join(self.exports_dir, filename)
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def load(self):
        stage_rows = self._load_csv("lifecycle_stages.csv")
        self.id_field_stages = _detect_id_field(stage_rows)
        for r in stage_rows:
            uid = r.get(self.id_field_stages, "")
            if not uid:
                continue
            self.stages[uid] = Stage(
                uid=uid,
                name=r.get("name", "") or r.get("Name", ""),
                description=r.get("description", "") or r.get("Description", ""),
            )

        profile_rows = self._load_csv("lifecycle_profiles.csv")
        self.id_field_profiles = _detect_id_field(profile_rows)
        for r in profile_rows:
            uid = r.get(self.id_field_profiles, "")
            if not uid:
                continue
            self.profiles[uid] = Profile(
                uid=uid,
                business_name=r.get("business_name", "") or r.get("Business Name", "") or r.get("name", "") or r.get("Name", ""),
                email=r.get("email", "") or r.get("Email", ""),
                current_stage_uid=r.get(PROFILE_STAGE_FIELD) or None,
            )

        module_rows = self._load_csv("lifecycle_modules.csv")
        self.id_field_modules = _detect_id_field(module_rows)
        for r in module_rows:
            uid = r.get(self.id_field_modules, "")
            if not uid:
                continue
            completed_list = _split_list(r.get(MODULE_COMPLETED_LIST_FIELD) or "")
            self.modules[uid] = Module(
                uid=uid,
                title=r.get("title", "") or r.get("Title", "") or r.get("name", "") or r.get("Name", "") or "(untitled module)",
                module_type=r.get("module_type", "") or r.get("Module Type", "") or r.get("type", ""),
                stage_uid=r.get(MODULE_STAGE_FIELD) or None,
                completed_profiles=completed_list,
            )

        decl_rows = self._load_csv("lifecycle_declarations.csv")
        self.id_field_decls = _detect_id_field(decl_rows)
        self.declarations = decl_rows

    def latest_declared_stage_uid_for_profile(self, profile_uid: str) -> Optional[str]:
        latest = None
        latest_time = ""
        for r in self.declarations:
            pid = r.get(DECL_PROFILE_FIELD) or ""
            if pid != profile_uid:
                continue
            ts = r.get("created_at") or r.get("Created Date") or r.get("creation_date") or ""
            if ts >= latest_time:
                latest_time = ts
                latest = r
        if not latest:
            return None
        return latest.get(DECL_STAGE_FIELD) or None

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
            stage_uid = r.get(DECL_STAGE_FIELD) or ""
            if not stage_uid:
                continue
            name = self.stages.get(stage_uid).name if stage_uid in self.stages else stage_uid
            counts[name] = counts.get(name, 0) + 1
        return counts
