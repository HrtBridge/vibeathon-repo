import csv, pathlib

FILES = [
  ("lifecycle_declarations", "bubble_exports/lifecycle_declarations.csv"),
  ("lifecycle_modules", "bubble_exports/lifecycle_modules.csv"),
  ("lifecycle_stages", "bubble_exports/lifecycle_stages.csv"),
  ("lifecycle_profiles", "bubble_exports/lifecycle_profiles.csv"),
  ("module_responses", "bubble_exports/module_responses.csv"),
  ("users", "bubble_exports/users.csv"),
]

def main():
  out = []
  out.append("# Bubble Schema Snapshot\n")
  out.append("This file is generated from the CSV headers in `bubble_exports/`.\n")

  for name, path in FILES:
    p = pathlib.Path(path)
    out.append(f"## {name}\n")
    if not p.exists():
      out.append(f"**Missing:** `{path}`\n")
      continue
    with p.open(newline="", encoding="utf-8") as f:
      reader = csv.reader(f)
      header = next(reader, [])
    out.append(f"- File: `{path}`\n")
    out.append("### Columns\n")
    for col in header:
      out.append(f"- `{col}`")
    out.append("")

  pathlib.Path("spec").mkdir(parents=True, exist_ok=True)
  pathlib.Path("spec/bubble_schema_snapshot.md").write_text("\n".join(out), encoding="utf-8")
  print("Wrote spec/bubble_schema_snapshot.md")

if __name__ == "__main__":
  main()
