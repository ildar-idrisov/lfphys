"""Load every Russian (and English override) catalogue of the lfphys repo into one flat list.

Run: python3 -I r00_load.py [--dump] from this folder (or any folder; paths are absolute to the repo).
Each entry: {cat, msgid, ru, forms} where ru is the 'other'/'many' form for plural entries and forms the dict.
"""
import json, os, sys, glob

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))


def catalogues(lang="ru"):
    out = [("engine", os.path.join(REPO, "lfphys", "lfphys", "locales", f"{lang}.json")),
           ("framework", os.path.join(REPO, "visualizations", "locales", f"{lang}.json"))]
    for p in sorted(glob.glob(os.path.join(REPO, "visualizations", "*", "locales", f"{lang}.json"))):
        out.append((p.split(os.sep)[-3], p))
    return [(n, p) for n, p in out if os.path.exists(p)]


def load(lang="ru"):
    entries = []
    for name, path in catalogues(lang):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        for k, v in d.items():
            if isinstance(v, dict):
                ru = v.get("many") or v.get("other") or next(iter(v.values()))
                entries.append({"cat": name, "msgid": k, "ru": ru, "forms": v})
            else:
                entries.append({"cat": name, "msgid": k, "ru": v, "forms": None})
    return entries


if __name__ == "__main__":
    e = load()
    from collections import Counter
    print(Counter(x["cat"] for x in e))
    print("total", len(e))
    if "--dump" in sys.argv:
        for x in e:
            print(f"[{x['cat']}] {x['msgid']}\n    -> {x['ru'] if not x['forms'] else json.dumps(x['forms'], ensure_ascii=False)}")
