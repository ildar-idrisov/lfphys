"""Short labels whose Russian is much longer than the English: msgid of <= 4 words, no sentence punctuation,
Russian >= 1.6x the English and >= 20 characters. Where it is used (grep of the msgid in the code) is printed
with the element kind guessed from the call site (button, option, th, tab, title).
Run: python3 -I r10_label_length.py > r10_label_length.out"""
import glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r00_load import load, REPO  # noqa: E402
E = load()
src = {}
for f in glob.glob(os.path.join(REPO, "**", "*.js"), recursive=True) + glob.glob(os.path.join(REPO, "**", "*.html"), recursive=True) + glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True):
    if any(s in f for s in ("/node_modules/", "/reviews/", "/vendor/", "/tests/")):
        continue
    src[os.path.relpath(f, REPO)] = open(f, encoding="utf-8", errors="replace").read().splitlines()
rows = []
for x in E:
    m, r = x["msgid"], x["ru"]
    if x["forms"] or len(m.split()) > 4 or re.search(r"[.;:]\s*$", m) or len(r) < 20:
        continue
    if len(r) < 1.6 * len(m):
        continue
    where = []
    for f, lines in src.items():
        for i, line in enumerate(lines):
            if ('"' + m + '"') in line or ("'" + m + "'") in line or ("`" + m + "`") in line or (">" + m + "<") in line:
                kind = next((k for k in ("button", "<option", "<th", "label:", "title", "tab", "name=", "label=") if k in line), "")
                where.append(f"{f}:{i+1} {kind}")
    rows.append((len(r) / len(m), x, where[:2]))
for ratio, x, where in sorted(rows, key=lambda t: -t[0]):
    print(f"{ratio:4.1f}x [{x['cat']}] {x['msgid']}  ->  {x['ru']}   ({'; '.join(where)})")
print(len(rows))
