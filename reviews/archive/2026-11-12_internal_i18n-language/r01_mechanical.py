"""Mechanical checks over all Russian catalogues (review 2026-11-12 i18n-language).

Run: python3 -I r01_mechanical.py > r01_mechanical.out
Sections: A identity, B Latin words in Russian, C placeholder sets, D first-letter case, E cross-catalogue conflicts,
F plural forms, G American spellings in msgids, H quotes, I yo (ё) consistency.
"""
import json, os, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r00_load import load, REPO  # noqa: E402

E = load()
PH = re.compile(r"\{(\w+)(?::([^{}]*))?\}")


def strip_ph(s):
    return PH.sub(" ", s)


def show(x):
    ru = x["ru"] if not x["forms"] else json.dumps(x["forms"], ensure_ascii=False)
    return f"  [{x['cat']}] {x['msgid']}\n      -> {ru}"


def section(t):
    print("\n" + "=" * 100 + "\n" + t + "\n" + "=" * 100)


# A identity
section("A. identity translations (ru == msgid) with Latin words of >= 3 letters")
for x in E:
    if not x["forms"] and x["ru"] == x["msgid"] and re.search(r"[A-Za-z]{3,}", strip_ph(x["msgid"])):
        print(show(x))

# B Latin words inside Russian
section("B. Latin tokens (>= 3 letters) inside Russian texts: frequency, then entries with tokens not in the allow list")
ALLOW = set("""CPU GPU fp64 fp32 lfphys lfviz auto JSON CSV PNG WebM GIF MP4 Docker URL API ID id RAM VRAM CUDA NumPy
numpy SciPy scipy GitHub Pages TDSE LBM BGK FDTD MD LJ HTTP Shift Ctrl Alt Enter Esc Delete Space Tab PDF SVG FPS fps
max min sin cos exp log tan arg Re Im sec AGPL CLA DOI ORCID arXiv README WebGL
""".split())
tok = Counter()
per = defaultdict(list)
for x in E:
    for s in ([x["ru"]] if not x["forms"] else list(x["forms"].values())):
        t = strip_ph(s)
        t = re.sub(r"`[^`]*`", " ", t)
        t = re.sub(r"https?://\S+", " ", t)
        t = re.sub(r"\b[\w.-]+@[\w.-]+\b", " ", t)
        t = re.sub(r"\b\w+\.(py|js|json|md|html|npz|txt)\b", " ", t)
        t = re.sub(r"\b[a-z]+_[a-z_0-9]+\b", " ", t)  # identifiers
        for w in re.findall(r"(?<![\w\\])[A-Za-z][A-Za-z]{2,}(?![\w])", t):
            tok[w] += 1
            if w not in ALLOW:
                per[w].append(x)
print(" ".join(f"{w}:{c}" for w, c in tok.most_common()))
print()
seen = set()
for w in sorted(per, key=lambda w: -len(per[w])):
    print(f"-- {w} ({len(per[w])})")
    for x in per[w][:6]:
        key = (x["cat"], x["msgid"])
        print(show(x))

# C placeholders
section("C. placeholder sets differ between msgid and translation")
for x in E:
    a = Counter(m.group(0) for m in PH.finditer(x["msgid"]))
    forms = [x["ru"]] if not x["forms"] else list(x["forms"].values())
    for s in forms:
        b = Counter(m.group(0) for m in PH.finditer(s))
        if a != b:
            # plural 'one' forms may legitimately drop parts; report anyway with a mark
            print(show(x))
            print(f"      msgid {dict(a)}  ru {dict(b)}")
            break

# D first-letter case
section("D. first letter case differs (msgid upper, ru lower or vice versa)")
def first_letter(s):
    s = PH.sub("", s)
    m = re.search(r"[A-Za-zА-Яа-яЁё]", s)
    return m.group(0) if m else None
nd = 0
for x in E:
    a, b = first_letter(x["msgid"]), first_letter(x["ru"])
    if not a or not b:
        continue
    if PH.match(x["msgid"]) or PH.match(x["ru"]):
        continue
    if a.isupper() != b.isupper():
        nd += 1
        print(show(x))
print("count", nd)

# E conflicts
section("E. the same msgid translated differently in different catalogues (merged catalogue: one wins)")
by = defaultdict(list)
for x in E:
    by[x["msgid"]].append(x)
for k, xs in by.items():
    vals = {json.dumps(x["forms"], ensure_ascii=False, sort_keys=True) if x["forms"] else x["ru"] for x in xs}
    if len(vals) > 1:
        for x in xs:
            print(show(x))
        print()

# F plurals
section("F1. plural objects: forms present, key argument")
for x in E:
    if x["forms"]:
        ks = sorted(x["forms"])
        args = {m.group(1) for m in PH.finditer(x["msgid"])}
        bad = []
        if set(ks) != {"one", "few", "many", "other"}:
            bad.append(f"forms {ks}")
        if "n" not in args:
            bad.append("no {n} in msgid: the category is chosen by n")
        if bad:
            print(show(x)); print("      ", "; ".join(bad))
section("F2. non-plural Russian entries with an integer/number placeholder directly followed by a Cyrillic word "
        "(the noun's form then depends on the number)")
NUMPH = re.compile(r"\{(\w+)(?::(d|\.\d*[gfe]|[+]?d|[+]?\.\d*[gfe]))?\}\s+([а-яё]+)")
for x in E:
    if x["forms"]:
        continue
    for m in NUMPH.finditer(x["ru"]):
        w = m.group(3)
        if w in ("и", "из", "в", "на", "до", "от", "по", "с", "к", "или", "а", "раз"):
            continue
        print(show(x)); print(f"      at «{m.group(0)}»")
        break
section("F3. English msgids with {x:d} followed by a plural noun but no plural object in en/ru")
for x in E:
    if x["forms"]:
        continue
    m = re.search(r"\{(\w+):d\}\s+([a-z]+s)\b", x["msgid"])
    if m:
        print(show(x)); print(f"      at «{m.group(0)}»")

# G American spellings
section("G. American spellings in msgids")
AM = re.compile(r"\b(\w*(?:iz(?:e|es|ed|ing|ation|ations|er|ers))|color\w*|behavior\w*|center\w*|centered|"
                r"analyz\w*|catalog|catalogs|license|licensed|licenses|neighbor\w*|favor\w*|honor\w*|"
                r"modeled|modeling|labeled|labeling|traveled|traveling|canceled|canceling|meter|meters|liter\w*|"
                r"gray|fiber\w*|program|programs|defense|offense|aluminum|sulfur|toward|artifact\w*|"
                r"fulfill|enroll|judgment|aging|dialog|signaled|totaled|focused|focusing)\b", re.I)
cnt = Counter()
for x in E:
    for m in AM.finditer(x["msgid"]):
        cnt[m.group(0).lower()] += 1
print(cnt.most_common())
BR = re.compile(r"\b(\w*(?:is(?:e|es|ed|ing|ation|ations))|colour\w*|behaviour\w*|centre\w*|analys\w*|catalogue\w*|"
                r"licence\w*|neighbour\w*|modelled|modelling|labelled|travelled|cancelled|metre\w*|litre\w*|grey|"
                r"fibre\w*|towards|artefact\w*)\b", re.I)
cb = Counter()
for x in E:
    for m in BR.finditer(x["msgid"]):
        cb[m.group(0).lower()] += 1
print("British forms:", cb.most_common(80))
print()
for x in E:
    if AM.search(x["msgid"]):
        print(show(x)); print("      ", [m.group(0) for m in AM.finditer(x["msgid"])])

# H quotes
section("H. English-style quotes “ ” or straight quotes \" in Russian; « » in English msgids")
for x in E:
    if re.search(r"[“”\"]", x["ru"]) and not re.search(r"[“”\"]", x["msgid"]) is None:
        pass
for x in E:
    s = x["ru"] if not x["forms"] else " ".join(x["forms"].values())
    if re.search(r"[“”„\"]", strip_ph(s)):
        print(show(x))
    if re.search(r"[«»]", x["msgid"]):
        print("  EN «»:", show(x))

# I yo
section("I. ё / е: words seen both ways")
words = Counter()
for x in E:
    for w in re.findall(r"[а-яёА-ЯЁ]+", x["ru"]):
        words[w.lower()] += 1
pairs = []
for w in words:
    if "ё" in w:
        e = w.replace("ё", "е")
        if e in words:
            pairs.append((w, words[w], e, words[e]))
for p in sorted(pairs, key=lambda p: -p[3]):
    print(p)
