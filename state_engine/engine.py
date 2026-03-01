import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


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

    def _load_csv(self, filename: str) -> List[dict]:
        path = os.path.join(self.exports_dir, filename)
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def load(self):
        # Load stages
        for r in self._load_csv("lifecycle_stages.csv"):
            self.stages[r["_id"]] = Stage(
                uid=r["_id"],
                name=r.get("name", ""),
                description=r.get("description", "")
            )

        # Load profiles
        for r in self._load_csv("lifecycle_profiles.csv"):
            self.profiles[r["_id"]] = Profile(
                uid=r["_id"],
                business_name=r.get("business_name", ""),
                email=r.get("email", ""),
                current_stage_uid=r.get("(Linked) Lifecycle_Stage") or None
            )

        # Load modules
        for r in self._load_csv("lifecycle_modules.csv"):
            completed = r.get("(Linked) Lifecycle_Profile_did_complete") or ""
            completed_list = [x.strip() for x in completed.split(",") if x.strip()]
            self.modules[r["_id"]] = Module(
                uid=r["_id"],
                title=r.get("title", ""),
                module_type=r.get("module_type", ""),
                stage_uid=r.get("(Linked) Lifecycle_Stage") or None,
                completed_profiles=completed_list
            )

        # Load declarations
        self.declarations = self._load_csv("lifecycle_declarations.csv")

    def latest_declared_stage_uid_for_profile(self, profile_uid: str) -> Optional[str]:
        latest = None
        latest_time = ""
        for r in self.declarations:
            pid = r.get("(Linked) Lifecycle_Profile") or ""
            if pid != profile_uid:
                continue
            ts = r.get("created_at") or r.get("Created Date") or ""
            if ts >= latest_time:
                latest_time = ts
                latest = r
        if not latest:
            return None
        return latest.get("(Linked) Lifecycle_Stage") or None

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
        return int((complete / len(mods)) * 100)

    def admin_distribution_by_stage_name(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self.declarations:
            stage_uid = r.get("(Linked) Lifecycle_Stage") or ""
            if not stage_uid:
                continue
            name = self.stages.get(stage_uid).name if stage_uid in self.stages else stage_uid
            counts[name] = counts.get(name, 0) + 1
        return counts
