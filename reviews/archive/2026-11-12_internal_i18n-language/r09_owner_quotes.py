"""Owner quotes next to translatable texts: a T("…")/t("…") call within 3 lines of a comment that quotes the owner
(«…» with "owner" on the comment). Prints the quote, the msgid and its Russian, for a reading of meaning drift.
Run: python3 -I r09_owner_quotes.py > r09_owner_quotes.out"""
import glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r00_load import load, REPO  # noqa: E402
ru = {x["msgid"]: x["ru"] for x in load()}
files = [f for f in glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True) + glob.glob(os.path.join(REPO, "**", "*.js"), recursive=True)
         + glob.glob(os.path.join(REPO, "**", "*.html"), recursive=True)
         if not any(s in f for s in ("/node_modules/", "/reviews/", "/vendor/", "/tests/"))]
CALL = re.compile(r"""\b[tT]\(\s*(["'`])((?:(?!\1).)+)\1""")
for f in files:
    lines = open(f, encoding="utf-8", errors="replace").read().splitlines()
    for i, line in enumerate(lines):
        if "owner" in line and "«" in line and ("#" in line or "//" in line or "<!--" in line):
            quotes = re.findall(r"«([^»]+)»", line)
            for j in range(max(0, i - 3), min(len(lines), i + 4)):
                for m in CALL.finditer(lines[j]):
                    mid = m.group(2)
                    if mid in ru:
                        print(f"{os.path.relpath(f, REPO)}:{i+1}\n  owner: {' | '.join('«'+q+'»' for q in quotes)[:300]}\n  msgid: {mid[:200]}\n  ru:    {ru[mid][:200]}\n")
