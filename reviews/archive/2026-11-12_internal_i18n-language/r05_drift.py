"""Meaning drift through the conversion: Russian string literals removed from the code by the i18n commit
(88e7811 -> d9da7cb) that do not reappear in any Russian catalogue entry.

Read-only git (git diff). Run from anywhere: python3 -I r05_drift.py > r05_drift.out
A literal "reappears" when each of its fixed fragments (between placeholders and ${...} / {...} interpolations, with
>= 8 Cyrillic letters) occurs verbatim in some catalogue translation or plural form. Short literals (< 12 letters) are skipped.
Literals that quote the owner («…» inside comments are not literals; only code strings are considered).
"""
import os, re, subprocess, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r00_load import load, REPO  # noqa: E402

diff = subprocess.run(["git", "-C", REPO, "diff", "--no-color", "-U0", "88e7811", "d9da7cb", "--",
                       "*.py", "*.js", "*.mjs", "*.html"], capture_output=True, text=True).stdout
STR = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'|`((?:[^`\\]|\\.)*)`')
CYR = re.compile(r"[А-Яа-яЁё]")
removed = defaultdict(list)
fname = None
for line in diff.splitlines():
    if line.startswith("+++ b/"):
        fname = line[6:]
        continue
    if not line.startswith("-") or line.startswith("---"):
        continue
    code = line[1:]
    s = code.lstrip()
    if s.startswith("#") or s.startswith("//") or s.startswith("*"):
        continue
    for m in STR.finditer(code):
        lit = next(g for g in m.groups() if g is not None)
        if CYR.search(lit) and len(re.findall(r"[А-Яа-яЁё]", lit)) >= 12:
            removed[lit].append(fname)

E = load()
corpus = []
for x in E:
    if x["forms"]:
        corpus.extend(x["forms"].values())
    else:
        corpus.append(x["ru"])
corpus_flat = "\n".join(corpus)


def fragments(lit):
    parts = re.split(r"\$\{[^}]*\}|\{[^{}]*\}|%[sdgf]|\\n|\\\"|\\'", lit)
    return [p.strip(" :;,.—-()«»") for p in parts if len(re.findall(r"[А-Яа-яЁё]", p)) >= 8]


miss = []
for lit, files in removed.items():
    frs = fragments(lit)
    if not frs:
        continue
    if not all(f in corpus_flat for f in frs):
        miss.append((files[0], lit))
print(f"removed Russian literals: {len(removed)}; not found verbatim (modulo placeholders) in the catalogues: {len(miss)}")
for f, lit in sorted(miss):
    print(f"[{f}] {lit[:300]}")
