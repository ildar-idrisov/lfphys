"""Placeholders that may carry an English word into a Russian sentence: T(...) calls in the Python code whose
keyword argument is a plain string (constant, f-string, str(), .name/.kind/.type attribute, a variable named like a
kind) rather than a number or another T. Run: python3 -I r07_placeholder_args.py > r07_placeholder_args.out"""
import ast, glob, os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r00_load import load, REPO  # noqa: E402
ru = {x["msgid"]: x["ru"] for x in load()}
files = [f for f in glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True)
         if "/tests/" not in f and "/reviews/" not in f and "/node_modules/" not in f]
SUSPECT = re.compile(r"^(kind|type|species|side|sides|pol|model|device|law|state|elem|comp|dir|route|tag|source|particle|"
                     r"mode|shape|axis|ax|plane|field|option|stat|measure|target|quantity|name|names|which|scheme|method|"
                     r"backend|precision|wall|boundary|material|medium|fluid|substance|body|obj|what)$")
hits = defaultdict(list)
for f in files:
    try:
        tree = ast.parse(open(f, encoding="utf-8").read())
    except Exception:
        continue
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "T"):
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
            continue
        msgid = node.args[0].value
        for kw in node.keywords:
            v = kw.value
            src = ast.get_source_segment(open(f, encoding="utf-8").read(), v) or ""
            why = None
            if isinstance(v, ast.Constant) and isinstance(v.value, str) and re.search(r"[A-Za-z]{3,}", v.value):
                why = "constant"
            elif isinstance(v, ast.JoinedStr):
                why = "f-string"
            elif isinstance(v, ast.Call) and getattr(v.func, "id", None) in ("str", "repr"):
                why = "str()"
            elif isinstance(v, ast.Attribute) and v.attr in ("name", "kind", "type", "species", "mode", "shape", "__name__"):
                why = "attribute ." + v.attr
            elif isinstance(v, ast.Name) and SUSPECT.match(v.id) and kw.arg not in ("n",):
                why = "variable " + v.id
            if why:
                hits[(msgid, kw.arg)].append((os.path.relpath(f, REPO), node.lineno, why, src[:80]))
for (msgid, arg), occ in sorted(hits.items(), key=lambda k: k[0][0]):
    r = ru.get(msgid, "(no ru entry)")
    print(f"{{{arg}}} in: {msgid[:140]}\n    ru: {r[:160]}")
    for o in occ[:3]:
        print(f"    {o[0]}:{o[1]}  {o[2]}  = {o[3]}")
print(len(hits))
