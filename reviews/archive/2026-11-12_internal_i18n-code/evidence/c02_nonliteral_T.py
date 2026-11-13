"""Every T(...) call whose msgid is not one string literal (the static completeness test cannot see these msgids),
and every t(...) call in JS whose first argument is not a literal."""
import ast, re, sys
from pathlib import Path
REPO = Path("/w")
roots = [REPO / "lfphys" / "lfphys", REPO / "visualizations"]
n = 0
for root in roots:
    for f in sorted(root.rglob("*.py")):
        if any(p in f.parts for p in ("node_modules", "runs", "tests")) and "p99_toy" not in str(f) and "p97_osc" not in str(f):
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and node.args:
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
                if name == "T" and not (isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    seg = ast.get_source_segment(f.read_text(encoding="utf-8"), node.args[0]) or "?"
                    print(f"PY {f.relative_to(REPO)}:{node.lineno}: T({seg[:90]})")
                    n += 1
print("python non-literal T calls:", n)
sys.path.insert(0, "/w/visualizations/tests")
import i18n_tools as tools
m = 0
CALL = re.compile(r"(?<![\w$.])t\(\s*([^\s)\"'`][^,)]{0,60})")
for f in sorted((REPO / "visualizations").rglob("*.js")):
    if any(p in f.parts for p in ("node_modules", "vendor", "tests")) and "p99_toy" not in str(f):
        continue
    code = tools.strip_js_comments(f.read_text(encoding="utf-8"))
    for mm in CALL.finditer(code):
        print(f"JS {f.relative_to(REPO)}:{code.count(chr(10), 0, mm.start()) + 1}: t({mm.group(1)[:70]}")
        m += 1
print("js non-literal t calls:", m)
