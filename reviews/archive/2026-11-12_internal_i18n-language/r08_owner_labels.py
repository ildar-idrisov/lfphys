"""Owner's and documents' Russian UI labels: short «…» phrases (1-5 words) quoted in AGENTS.md, RULES.md, PLAN.md,
STATUS.md, the READMEs (ru) and in code comments that are not present as a Russian catalogue entry (whole or inside).
Run: python3 -I r08_owner_labels.py > r08_owner_labels.out"""
import glob, os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r00_load import load, REPO  # noqa: E402
E = load()
ru_whole = {x["ru"].strip() for x in E}
corpus = "\n".join(x["ru"] for x in E)
docs = [os.path.join(REPO, p) for p in ("AGENTS.md", "STATUS.md", "README.ru.md", "visualizations/RULES.md", "lfphys/PLAN.md")]
docs += glob.glob(os.path.join(REPO, "visualizations", "*", "README.ru.md"))
code = [f for f in glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True) + glob.glob(os.path.join(REPO, "**", "*.js"), recursive=True)
        if "/node_modules/" not in f and "/reviews/" not in f and "/vendor/" not in f]
Q = re.compile(r"«([^«»\n]{3,60})»")
found = defaultdict(set)
for f in docs:
    for m in Q.finditer(open(f, encoding="utf-8").read()):
        found[m.group(1).strip()].add(os.path.relpath(f, REPO))
for f in code:
    for line in open(f, encoding="utf-8", errors="replace"):
        if "#" in line or "//" in line:
            com = line.split("#", 1)[-1] if "#" in line else line.split("//", 1)[-1]
            for m in Q.finditer(com):
                found[m.group(1).strip()].add(os.path.relpath(f, REPO))
rows = []
for q, fs in found.items():
    if not re.search(r"[А-Яа-яЁё]", q) or len(q.split()) > 5:
        continue
    qq = q.strip(" .…")
    if qq in ru_whole or qq in corpus:
        continue
    rows.append((sorted(fs)[0], q, len(fs)))
for f, q, n in sorted(rows):
    print(f"{f:55s} ({n}) «{q}»")
print(len(rows))
