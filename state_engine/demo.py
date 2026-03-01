from state_engine.engine import ContinuumEngine

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

    # Pick a sample profile
    sample_uid = next(iter(eng.profiles.keys()))
    p = eng.profiles[sample_uid]
    s = eng.current_stage(sample_uid)

    print("Sample Business Dashboard")
    print("------------------------")
    print(f"Business: {p.business_name}")
    print(f"Email:    {p.email}")
    print(f"Stage:    {s.name if s else '(no stage set on profile)'}")
    if eng.profile_stage_field_used:
        print(f"(Stage sourced from profile field: {eng.profile_stage_field_used})")
    print()

    print("Modules for current stage")
    mods = eng.modules_for_profile(sample_uid, view_all=False)
    for m in mods:
        status = "✅" if eng.is_complete(sample_uid, m.uid) else "⬜"
        print(f"{status} {m.title}  [{m.module_type}]")
    print()
    print(f"Succession Readiness: {eng.readiness_percent(sample_uid)}%")
    print()

    print("Admin Dashboard (gated)")
    print("-----------------------")
    admin_email = "brentrosenauer@gmail.com"
    if admin_email in ADMIN_ALLOWLIST:
        print(f"Access GRANTED for {admin_email}")
        dist = eng.admin_distribution_by_stage_uid()
        print("Declaration distribution (by stage):")
        for stage_uid, count in dist.items():
            stage = eng.stages.get(stage_uid)
            label = stage.name if stage else stage_uid
            print(f"- {label}: {count}")
    else:
        print(f"Access DENIED for {admin_email}")

if __name__ == "__main__":
    main()
