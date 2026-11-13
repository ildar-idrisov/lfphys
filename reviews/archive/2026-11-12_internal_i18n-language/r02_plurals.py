"""Plural agreement: non-plural Russian entries where a number placeholder governs a noun.

Run: python3 -I r02_plurals.py > r02_plurals.out
Prints (1) a number placeholder directly followed by a countable noun; (2) English msgids with a count placeholder before
a plural noun that have no plural object (the English then reads "1 values"); (3) plural objects whose forms are not
the expected ones.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r00_load import load  # noqa: E402

E = load()
UNITS = set("""нм м мкм рад км пс нс мм кг фс сут см мс мкс фм пм мин ч с г эВ кэВ МэВ ГэВ ТэВ К Па Дж Вт Гц кГц МГц ГГц
ТГц ТВт А В Тл а.е. пк кпк Мпк ед знач ст э б""".split())
FUNC = set("""не её его при против меньше больше нет уже сразу слишком для вместо через без вдоль у она он оно они это этой
этот и из в на до от по с к или а раз как то же ли бы так также только ещё уже всё все где когда стало стала стал
стали снова целиком прямо свободно должен должна должно должны""".split())
NUM = re.compile(r"\{(\w+)(?::([+]?(?:d|\.\d*[gfe]|g)))?\}\s+([а-яё]+)")
COUNT = re.compile(r"\{(\w+):[+]?d\}")

print("1. number placeholder followed by a word that may need agreement (units and function words skipped)")
n1 = 0
for x in E:
    if x["forms"]:
        continue
    hits = []
    for m in NUM.finditer(x["ru"]):
        w = m.group(3)
        if w in UNITS or w in FUNC or len(w) < 3:
            continue
        hits.append(m.group(0))
    if hits:
        n1 += 1
        print(f"  [{x['cat']}] {x['msgid']}\n      -> {x['ru']}\n      at {hits}")
print("count", n1)

print("\n2. count placeholder before a plural English noun, no plural object")
n2 = 0
for x in E:
    if x["forms"]:
        continue
    m = re.search(r"\{(\w+):[+]?d\}\s+(?:[a-z-]+\s+)?([a-z]+s)\b", x["msgid"])
    if m:
        n2 += 1
        print(f"  [{x['cat']}] {x['msgid']}\n      -> {x['ru']}\n      at «{m.group(0)}»")
print("count", n2)

print("\n3. plural objects")
for x in E:
    if x["forms"]:
        print(f"  [{x['cat']}] {x['msgid']}\n      -> {json.dumps(x['forms'], ensure_ascii=False)}")
