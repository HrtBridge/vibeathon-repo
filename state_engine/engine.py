import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

MODULE_COMPLETED_LIST_FIELD = "(Linked) Lifecycle_Profile_did_complete"
PROFILE_STAGE_FIELD = "(Linked) Lifecycle_Stage"
MODULE_STAGE_FIELD = "(Linked) Lifecycle_Stage"
DECL_STAGE_FIELD = "(Linked) Lifecycle_Stage"
DECL_PROFILE_FIELD = "(Linked) Lifecycle_Profile"


def _detect_id_field(rows: List[dict]) -> str:
    if not rows:
        return "Unique ID"
    keys = set(rows[0].keys())
    for candidate in ("Unique ID", "_id", "unique_id", "uid", "ID"):
        if candidate in keys:
            return candidate
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

    def _load_csv(self, filename: str) -> List[dict]:
        path = os.path.join(self.exports_dir, filename)
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def load(self):
        # Load stages
        stage_rows = self._load_csv("lifecycle_stages.csv")
        id_field_stages = _detect_id_field(stage_rows)
        for r in stage_rows:
            uid = (r.get(id_field_stages) or "").strip()
            if not uid:
                continue
            self.stages[uid] = Stage(
                uid=uid,
                name=r.get("name", "") or r.get("Name", ""),
                description=r.get("long_description", "") or r.get("description", "")
            )

        # Load profiles
        profile_rows = self._load_csv("lifecycle_profiles.csv")
        id_field_profiles = _detect_id_field(profile_rows)
        for r in profile_rows:
            uid = (r.get(id_field_profiles) or "").strip()
            if not uid:
                continue
            stage_uid = (r.get(PROFILE_STAGE_FIELD) or "").strip() or None
            self.profiles[uid] = Profile(
                uid=uid,
                business_name=r.get("business_name", "") or r.get("Business Name", ""),
                email=r.get("email", "") or r.get("Email", ""),
                current_stage_uid=stage_uid,
            )

        # Load modules
        module_rows = self._load_csv("lifecycle_modules.csv")
        id_field_modules = _detect_id_field(module_rows)
        for r in module_rows:
            uid = (r.get(id_field_modules) or "").strip()
            if not uid:
                continue
            completed_list = _split_list(r.get(MODULE_COMPLETED_LIST_FIELD) or "")
            self.modules[uid] = Module(
                uid=uid,
                title=r.get("title", "") or r.get("Title", "") or r.get("name", "") or r.get("Name", ""),
                module_type=r.get("module_type", "") or r.get("Module Type", ""),
                stage_uid=(r.get(MODULE_STAGE_FIELD) or "").strip() or None,
                completed_profiles=completed_list,
            )

        # Load declarations
        self.declarations = self._load_csv("lifecycle_declarations.csv")

        # Load module responses (Bubble readiness logic)
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
            ts = (r.get("created_at") or r.get("Creation Date") or "").strip()
            if ts >= latest_time:
                latest_time = ts
                latest = r
        if not latest:
            return None
        return (latest.get(DECL_STAGE_FIELD) or "").strip() or None

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

    def modules_for_profile(self, profile_uid: str) -> List[Module]:
        stage_uid = self.current_stage_uid(profile_uid)
        if not stage_uid:
            return []
        return [m for m in self.modules.values() if m.stage_uid == stage_uid]

    def readiness_percent(self, profile_uid: str) -> int:
        """
        Mirrors Bubble logic:
        number of Module_Responses for this profile
        divided by total module count.
        """
        total_modules = len(self.modules)
        if total_modules == 0:
            return 0

        responses = [
            r for r in self.module_responses
            if (r.get("(Linked) Lifecycle_Profile") or "").strip() == profile_uid
        ]

        return int(round((len(responses) / total_modules) * 100))

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
        profiles = len(self.profiles)
        modules = len(self.modules)
        if profiles == 0 or modules == 0:
            return 0
        responses = len(self.module_responses)
        pct = (responses / (modules * profiles)) * 100
        return int(round(pct))
