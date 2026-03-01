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

    if not eng.profiles:
        print("NOTE: No profiles were loaded from CSV exports.")
        print("This happens when Bubble CSV exports omit the 'Unique ID' column.")
        print("Re-export lifecycle_profiles and lifecycle_stages including 'Unique ID' to enable readiness scoring.\n")

    # Choose a sample profile if any exist
    sample_uid = None
    if eng.profiles:
        for pid in eng.profiles.keys():
            if eng.latest_declared_stage_uid_for_profile(pid):
                sample_uid = pid
                break
        if not sample_uid:
            sample_uid = next(iter(eng.profiles.keys()))

    if sample_uid:
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
        for m in mods:
            status = "✅" if eng.is_complete(sample_uid, m.uid) else "⬜"
            print(f"{status} {m.title}  [{m.module_type}]")
        print()
        print(f"Succession Readiness: {eng.readiness_percent(sample_uid)}%")
        print()
    else:
        print("Sample Business Dashboard")
        print("------------------------")
        print("(skipped — no profile IDs available)\n")

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
