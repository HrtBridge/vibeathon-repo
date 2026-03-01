import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

# Bubble export field names we rely on
PROFILE_STAGE_FIELD = "(Linked) Lifecycle_Stage"
MODULE_STAGE_FIELD = "(Linked) Lifecycle_Stage"
DECL_STAGE_FIELD = "(Linked) Lifecycle_Stage"
DECL_PROFILE_FIELD = "(Linked) Lifecycle_Profile"

RESP_PROFILE_FIELD = "(Linked) Lifecycle_Profile"
RESP_MODULE_FIELD = "(Linked) Lifecycle_Module"

MODULE_COMPLETED_LIST_FIELD = "(Linked) Lifecycle_Profile_did_complete"


def _load_csv(path: str) -> List[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _split_list(cell: Optional[str]) -> List[str]:
    if not cell:
        return []
    return [x.strip() for x in cell.split(",") if x.strip()]


def _candidate_id_fields(rows: List[dict]) -> List[str]:
    if not rows:
        return []
    keys = list(rows[0].keys())
    # Strong candidates first
    preferred = []
    for k in keys:
        lk = k.lower().strip()
        if lk in ("unique id", "unique_id", "_id", "id", "uid"):
            preferred.append(k)
    # Then anything containing id
    for k in keys:
        if k not in preferred and "id" in k.lower():
            preferred.append(k)
    # Finally, all keys as a last resort (keeps function total)
    for k in keys:
        if k not in preferred:
            preferred.append(k)
    return preferred


def _pick_id_field_by_overlap(rows: List[dict], reference_ids: Set[str]) -> Optional[str]:
    """
    Pick the column whose values overlap most with reference_ids.
    This is the key to making Bubble linked fields joinable.
    """
    if not rows:
        return None
    candidates = _candidate_id_fields(rows)
    best: Tuple[int, int, str] = (-1, -1, candidates[0])  # (overlap, nonempty_count, field)
    for field in candidates:
        vals = [(r.get(field) or "").strip() for r in rows]
        nonempty = [v for v in vals if v]
        overlap = sum(1 for v in nonempty if v in reference_ids)
        score = (overlap, len(nonempty), field)
        if score > best:
            best = score
    return best[2]


def _pick_best_id_field_fallback(rows: List[dict]) -> Optional[str]:
    if not rows:
        return None
    candidates = _candidate_id_fields(rows)
    # Prefer exact-ish names
    for target in ("Unique ID", "unique id", "_id", "unique_id", "uid", "ID", "id"):
        for c in candidates:
            if c.strip() == target:
                return c
    # Otherwise just pick the first candidate
    return candidates[0]


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

        # For transparency/debug
        self.profile_id_field: Optional[str] = None
        self.stage_id_field: Optional[str] = None
        self.module_id_field: Optional[str] = None

    def load(self):
        # Load module_responses first so we can choose ID columns by overlap
        resp_path = os.path.join(self.exports_dir, "module_responses.csv")
        try:
            self.module_responses = _load_csv(resp_path)
        except FileNotFoundError:
            self.module_responses = []

        referenced_profile_ids = {
            (r.get(RESP_PROFILE_FIELD) or "").strip()
            for r in self.module_responses
            if (r.get(RESP_PROFILE_FIELD) or "").strip()
        }
        referenced_module_ids = {
            (r.get(RESP_MODULE_FIELD) or "").strip()
            for r in self.module_responses
            if (r.get(RESP_MODULE_FIELD) or "").strip()
        }

        # Declarations (helpful for stage-id overlap if needed)
        decl_path = os.path.join(self.exports_dir, "lifecycle_declarations.csv")
        self.declarations = _load_csv(decl_path)
        referenced_stage_ids = {
            (r.get(DECL_STAGE_FIELD) or "").strip()
            for r in self.declarations
            if (r.get(DECL_STAGE_FIELD) or "").strip()
        }

        # Load stages
        stage_rows = _load_csv(os.path.join(self.exports_dir, "lifecycle_stages.csv"))
        # Try overlap with referenced_stage_ids first; fallback to reasonable ID column
        self.stage_id_field = _pick_id_field_by_overlap(stage_rows, referenced_stage_ids) if referenced_stage_ids else None
        if not self.stage_id_field:
            self.stage_id_field = _pick_best_id_field_fallback(stage_rows)

        for r in stage_rows:
            uid = (r.get(self.stage_id_field) or "").strip()
            if not uid:
                continue
            self.stages[uid] = Stage(
                uid=uid,
                name=r.get("name", "") or r.get("Name", ""),
                description=r.get("long_description", "") or r.get("description", "") or r.get("Description", ""),
            )

        # Load profiles
        profile_rows = _load_csv(os.path.join(self.exports_dir, "lifecycle_profiles.csv"))
        self.profile_id_field = _pick_id_field_by_overlap(profile_rows, referenced_profile_ids) if referenced_profile_ids else None
        if not self.profile_id_field:
            self.profile_id_field = _pick_best_id_field_fallback(profile_rows)

        for r in profile_rows:
            uid = (r.get(self.profile_id_field) or "").strip()
            if not uid:
                continue
            self.profiles[uid] = Profile(
                uid=uid,
                business_name=r.get("business_name", "") or r.get("Business Name", "") or r.get("name", "") or r.get("Name", ""),
                email=r.get("email", "") or r.get("Email", ""),
                current_stage_uid=(r.get(PROFILE_STAGE_FIELD) or "").strip() or None,
            )

        # Load modules
        module_rows = _load_csv(os.path.join(self.exports_dir, "lifecycle_modules.csv"))
        self.module_id_field = _pick_id_field_by_overlap(module_rows, referenced_module_ids) if referenced_module_ids else None
        if not self.module_id_field:
            self.module_id_field = _pick_best_id_field_fallback(module_rows)

        for r in module_rows:
            uid = (r.get(self.module_id_field) or "").strip()
            if not uid:
                continue
            completed_list = _split_list(r.get(MODULE_COMPLETED_LIST_FIELD) or "")
            self.modules[uid] = Module(
                uid=uid,
                title=r.get("title", "") or r.get("Title", "") or r.get("name", "") or r.get("Name", "") or "(untitled module)",
                module_type=r.get("module_type", "") or r.get("Module Type", "") or r.get("type", ""),
                stage_uid=(r.get(MODULE_STAGE_FIELD) or "").strip() or None,
                completed_profiles=completed_list,
            )

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
        return (latest.get(DECL_STAGE_FIELD) or "").strip() or None

    def current_stage_uid(self, profile_uid: str) -> Optional[str]:
        p = self.profiles.get(profile_uid)
        if not p:
            return None
        if p.current_stage_uid:
            return p.current_stage_uid
        return self.latest_declared_stage_uid_for_profile(profile_uid)

    def current_stage(self, profile_uid: str) -> Optional[Stage]:
        sid = self.current_stage_uid(profile_uid)
        if not sid:
            return None
        return self.stages.get(sid)

    def modules_for_profile(self, profile_uid: str, view_all: bool = False) -> List[Module]:
        mods = list(self.modules.values())
        if view_all:
            return sorted(mods, key=lambda m: (m.stage_uid or "", m.title.lower()))

        sid = self.current_stage_uid(profile_uid)
        if not sid:
            return []
        stage_mods = [m for m in mods if m.stage_uid == sid]
        return sorted(stage_mods, key=lambda m: m.title.lower())

    def is_complete(self, profile_uid: str, module_uid: str) -> bool:
        # Prefer explicit completion list if present
        m = self.modules.get(module_uid)
        if m and profile_uid in (m.completed_profiles or []):
            return True

        # Fall back to Module_Response existence
        for r in self.module_responses:
            if (r.get(RESP_PROFILE_FIELD) or "").strip() == profile_uid and (r.get(RESP_MODULE_FIELD) or "").strip() == module_uid:
                return True
        return False

    def readiness_percent(self, profile_uid: str) -> int:
        """
        Mirrors Bubble-style completion tracking:
        count Module_Responses for this profile / total module count
        """
        total_modules = len(self.modules)
        if total_modules == 0:
            return 0
        completed = sum(1 for r in self.module_responses if (r.get(RESP_PROFILE_FIELD) or "").strip() == profile_uid)
        return int(round((completed / total_modules) * 100))

    def admin_distribution_by_stage_name(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self.declarations:
            sid = (r.get(DECL_STAGE_FIELD) or "").strip()
            if not sid:
                continue
            name = self.stages.get(sid).name if sid in self.stages else sid
            counts[name] = counts.get(name, 0) + 1
        return counts

    def community_readiness_density_percent(self) -> int:
        profiles = len(self.profiles)
        modules = len(self.modules)
        if profiles == 0 or modules == 0:
            return 0
        responses = len(self.module_responses)
        return int(round((responses / (profiles * modules)) * 100))

    # --- Admin metrics (mirror Bubble dashboard) ---

    def admin_average_bigq_score(self) -> float:
        """
        Average of lifecycle_declarations.bigq_score, ignoring blanks/non-numeric.
        Supports minor header variations by searching for a column containing 'bigq'.
        """
        if not self.declarations:
            return 0.0

        # Find BigQ column name
        keys = list(self.declarations[0].keys())
        bigq_key = None
        for k in keys:
            if "bigq" in k.lower():
                bigq_key = k
                break
        if not bigq_key:
            # common fallback
            for k in keys:
                if "score" in k.lower():
                    bigq_key = k
                    break
        if not bigq_key:
            return 0.0

        vals = []
        for r in self.declarations:
            raw = (r.get(bigq_key) or "").strip()
            if not raw:
                continue
            try:
                vals.append(float(raw))
            except ValueError:
                # sometimes Bubble exports weirdly; ignore non-numeric
                continue

        if not vals:
            return 0.0
        return sum(vals) / len(vals)

    def admin_average_readiness_percent(self) -> float:
        """
        Bubble metric:
        module_responses_count / (modules_count * profiles_count) * 100
        """
        profiles = len(self.profiles)
        modules = len(self.modules)
        if profiles == 0 or modules == 0:
            return 0.0
        responses = len(self.module_responses)
        return (responses / (profiles * modules)) * 100.0
