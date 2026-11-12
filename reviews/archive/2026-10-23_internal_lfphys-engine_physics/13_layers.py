"""13: layering inventory. (1) core modules whose code paths implement refuted/alternative kinematics (searched for
'emission', 'ether', 'Galilean' in core sources); (2) the kind and validity of every module, to compare the admission
rule of LAYERS.md (controlled approximations -> theories/approx) with what the core contains; (3) the conflicts the
interpretations declare. Usage: python3 13_layers.py
"""
import argparse
import pathlib
import re

argparse.ArgumentParser(description=__doc__).parse_args()

from lfphys import registry

root = pathlib.Path(registry.__file__).parent
print("=== (1) core sources mentioning alternative kinematics ===")
for p in sorted((root / "core").rglob("*.py")):
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if re.search(r"\b(emission|ether|Galilean|absolute time)\b", line):
            print(f"{p.relative_to(root.parent)}:{i}: {line.strip()[:110]}")

print("\n=== (2) core modules whose own validity text declares an approximation / omitted physics ===")
keys = ("приближен", "нерелятив", "низший порядок", "без лэмбовск", "без спин", "дипольн", "КЭД высших")
for d in registry.catalogue():
    if d["layer"] == "core" and any(k in (d["validity"] + d["statement"]) for k in keys):
        print(f"{d['id']:32s} kind={d['kind']:20s} validity: {d['validity'][:100]}")

print("\n=== (3) declared conflicts of the interpretations and of newton ===")
for d in registry.catalogue():
    if d.get("kind") == "interpretation" or d["id"].endswith("newton"):
        print(f"{d['id']}: kind={d['kind']}; conflicts={d['conflicts']}; validity={d['validity'][:120]}")
