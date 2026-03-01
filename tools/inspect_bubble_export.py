import json

PATH = "bubble_app/continuum-81071.bubble"

def main():
    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    keys = sorted(list(data.keys()))
    pages = data.get("pages", {}) if isinstance(data, dict) else {}
    print(f"Top-level keys: {keys}")
    print(f"Pages: {len(pages)}")

    # Bubble exports vary; best-effort element count
    total_elements = 0
    for _, page in pages.items():
        elements = page.get("elements") if isinstance(page, dict) else None
        if isinstance(elements, dict):
            total_elements += len(elements)

    print(f"Total elements (best-effort): {total_elements}")

if __name__ == "__main__":
    main()