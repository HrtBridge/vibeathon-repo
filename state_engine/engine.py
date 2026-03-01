from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import csv
import pathlib

MODULE_COMPLETED_LIST_FIELD = "(Linked) Lifecycle_Profile_did_complete"

def _read_csv(path: str) -> Tuple[List[Dict[str, str]], List[str]]:
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        cols = reader.fieldnames or []
    return rows, cols

def _bubble_uid(row: Dict[str, str]) -> str:
    return row.get("Unique ID") or row.get("unique_id") or row.get("uid") or ""

def _split_list(cell: Optional[str]) -> List[str]:
    if not cell:
        return []
    parts = [p.strip() for p in cell.split(",")]
    return [p for p in parts if p]

def _get(row: Dict[str, str], *names: str) -> str:
    for n in names:
        if n in row and row[n]:
            return row[n]
    return ""

@dataclass
class Profile:
    uid: str
    business_name: str
    email: str
    current_stage_uid: Optional[str]
    raw: Dict[str, Any]

@dataclass
class Stage:
    uid: str
    name: str
    raw: Dict[str, Any]

@dataclass
class Module:
    uid: str
    stage_uid: Optional[str]
    module_type: str
    title: str
    description: str
    url: Optional[str]
    checklist: List[str]
    form_question: Optional[str]
    completed_profile_uids: List[str]
    raw: Dict[str, Any]

class ContinuumEngine:
    """
    Reference engine that mirrors Bubble prototype behavior:
    - current stage stored on Lifecycle_Profile (latest declaration written there)
    - modules filtered by current stage (or view-all)
    - completion stored on module as list of completed profiles:
      `(Linked) Lifecycle_Profile_did_complete`
    """

    def __init__(self, exports_dir: str = "bubble_exports"):
        self.exports_dir = exports_dir
        self.profiles: Dict[str, Profile] = {}
        self.stages: Dict[str, Stage] = {}
        self.modules: Dict[str, Module] = {}
        self.declarations: List[Dict[str, str]] = []

        # discovered during load (for debugging)
        self.profile_stage_field_used: Optional[str] = None
        self.module_title_field_used: Optional[str] = None

    def load(self) -> None:
        # stages
        stage_rows, _ = _read_csv(f"{self.exports_dir}/lifecycle_stages.csv")
        for r in stage_rows:
            uid = _bubble_uid(r)
            name = _get(r, "name", "Name", "stage_name")
            self.stages[uid] = Stage(uid=uid, name=name, raw=r)

        # profiles
        profile_rows, profile_cols = _read_csv(f"{self.exports_dir}/lifecycle_profiles.csv")

        # best-effort: find a column that looks like current stage link
        candidate_fields = [
            "(Linked) Lifecycle_Stage_current",
            "(Linked) Lifecycle_Stage",
            "(Linked) current_lifecycle_stage",
            "current_stage",
        ]
        existing_candidates = [c for c in candidate_fields if c in profile_cols]

        for r in profile_rows:
            uid = _bubble_uid(r)
            business_name = _get(r, "business_name", "Business Name", "name", "Name")
            email = _get(r, "email", "Email")

            current_stage_uid = None
            for c in existing_candidates:
                if r.get(c):
                    current_stage_uid = r.get(c)
                    self.profile_stage_field_used = c
                    break

            self.profiles[uid] = Profile(
                uid=uid,
                business_name=business_name,
                email=email,
                current_stage_uid=current_stage_uid,
                raw=r,
            )

        # modules
        module_rows, module_cols = _read_csv(f"{self.exports_dir}/lifecycle_modules.csv")
        title_candidates = [c for c in ["title", "Title", "name", "Name"] if c in module_cols]

        for r in module_rows:
            uid = _bubble_uid(r)
            stage_uid = _get(r, "(Linked) Lifecycle_Stage", "lifecycle_stage")
            module_type = _get(r, "module_type", "Module Type", "type")
            title = ""
            for c in title_candidates:
                if r.get(c):
                    title = r.get(c)
                    self.module_title_field_used = c
                    break
            description = _get(r, "description", "Description")

            url = _get(r, "ModuleTypeURL_link") or None
            checklist = _split_list(_get(r, "ModuleTypeChecklist_list"))
            form_q = _get(r, "ModuleTypeForm_Question") or None

            completed = _split_list(r.get(MODULE_COMPLETED_LIST_FIELD) or "")

            self.modules[uid] = Module(
                uid=uid,
                stage_uid=stage_uid or None,
                module_type=module_type,
                title=title or "(untitled module)",
                description=description,
                url=url,
                checklist=checklist,
                form_question=form_q,
                completed_profile_uids=completed,
                raw=r,
            )

        # declarations (for admin aggregation)
        decl_rows, _ = _read_csv(f"{self.exports_dir}/lifecycle_declarations.csv")
        self.declarations = decl_rows

    def current_stage(self, profile_uid: str) -> Optional[Stage]:
        p = self.profiles.get(profile_uid)
        if not p or not p.current_stage_uid:
            return None
        return self.stages.get(p.current_stage_uid)

    def modules_for_profile(self, profile_uid: str, view_all: bool = False) -> List[Module]:
        p = self.profiles.get(profile_uid)
        if not p:
            return []
        if view_all or not p.current_stage_uid:
            return list(self.modules.values())
        return [m for m in self.modules.values() if m.stage_uid == p.current_stage_uid]

    def is_complete(self, profile_uid: str, module_uid: str) -> bool:
        m = self.modules.get(module_uid)
        if not m:
            return False
        return profile_uid in m.completed_profile_uids

    def readiness_percent(self, profile_uid: str) -> int:
        mods = self.modules_for_profile(profile_uid, view_all=False)
        if not mods:
            return 0
        done = sum(1 for m in mods if self.is_complete(profile_uid, m.uid))
        return int(round(done / len(mods) * 100))

    def admin_distribution_by_stage_uid(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self.declarations:
            stage_uid = r.get("(Linked) Lifecycle_Stage") or r.get("lifecycle_stage") or ""
            if not stage_uid:
                continue
            counts[stage_uid] = counts.get(stage_uid, 0) + 1
        return counts
