from .engine import ContinuumEngine

ADMIN_ALLOWLIST = {"brentrosenauer@gmail.com"}

def main():
    eng = ContinuumEngine(exports_dir="bubble_exports")
    eng.load()

    print("Continuum — Reference Engine Demo (mirrors Bubble prototype)")
    print("==========================================================")
    print(f"Profiles:      {len(eng.profiles)}")
    print(f"Stages:        {len(eng.stages)}")
    print(f"Modules:       {len(eng.modules)}")
    print(f"Declarations:  {len(eng.declarations)}")
    print()

    # --- Modules per stage (helps judges understand coverage) ---
    print("Modules per stage")
    print("-----------------")
    stage_to_count = {}
    for m in eng.modules.values():
        stage_to_count[m.stage_uid] = stage_to_count.get(m.stage_uid, 0) + 1
    # Print in a stable order: Growth/Stable/Exit Curious/Transition Seeking if present
    stage_names = [s.name for s in eng.stages.values()]
    preferred = ["Growth", "Stable", "Exit Curious", "Transition Seeking"]
    ordered_stage_uids = []
    for name in preferred:
        for uid, s in eng.stages.items():
            if s.name == name:
                ordered_stage_uids.append(uid)
    # include any leftovers
    for uid in eng.stages.keys():
        if uid not in ordered_stage_uids:
            ordered_stage_uids.append(uid)

    for uid in ordered_stage_uids:
        s = eng.stages.get(uid)
        label = s.name if s else uid
        print(f"- {label}: {stage_to_count.get(uid, 0)}")
    print()

    # --- Pick a sample profile that yields the richest module list ---
    best_uid = None
    best_count = -1
    for pid in eng.profiles.keys():
        mods = eng.modules_for_profile(pid)
        if len(mods) > best_count:
            best_count = len(mods)
            best_uid = pid
    sample_uid = best_uid

    p = eng.profiles[sample_uid]
    s = eng.current_stage(sample_uid)

    print("Sample Business Dashboard")
    print("------------------------")
    print(f"Business: {p.business_name}")
    print(f"Email:    {p.email}")
    print(f"Stage:    {s.name if s else '(unknown)'}")
    print()

    print("Modules for current stage")
    mods = eng.modules_for_profile(sample_uid)
    if not mods:
        print("(none linked to this stage)")
    else:
        for m in mods:
            status = "✅" if eng.is_complete(sample_uid, m.uid) else "⬜"
            print(f"{status} {m.title}  [{m.module_type}]")
    print()
    print(f"Succession Readiness: {eng.readiness_percent(sample_uid)}%")
    print()

    # --- Readiness summary by stage (policy usefulness) ---
    print("Readiness summary by stage")
    print("--------------------------")
    for uid in ordered_stage_uids:
        stage = eng.stages.get(uid)
        label = stage.name if stage else uid
        # profiles in stage (derived)
        pids = [pid for pid in eng.profiles.keys() if eng.current_stage_uid(pid) == uid]
        if not pids:
            print(f"- {label}: (no profiles)")
            continue
        scores = [eng.readiness_percent(pid) for pid in pids]
        avg = round(sum(scores) / len(scores))
        high = max(scores)
        print(f"- {label}: avg {avg}% (n={len(scores)}, max={high}%)")
    print()

    print("Admin Dashboard (gated)")
    print("-----------------------")
    admin_email = "brentrosenauer@gmail.com"
    if admin_email in ADMIN_ALLOWLIST:
        print(f"Access GRANTED for {admin_email}")
        dist = eng.admin_distribution_by_stage_name()
        print("Declaration distribution:")
        for name, count in dist.items():
            print(f"- {name}: {count}")
    else:
        print(f"Access DENIED for {admin_email}")

if __name__ == "__main__":
    main()
