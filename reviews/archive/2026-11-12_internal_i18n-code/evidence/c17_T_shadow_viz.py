"""The engine test's T-shadowing check (test_i18n_engine._shadowing) applied to the visualizations' Python, which no
test covers; plus every function there that makes T a local at all (a later T(...) call in it would raise
UnboundLocalError), and module-level rebinding of T. Also the engine's own blind spots: except ... as T, nested def T,
import ... as T."""
import ast, sys
from pathlib import Path
sys.path[:0] = ["/w/lfphys/tests", "/w/lfphys"]
REPO = Path("/w")
def locals_T(fn):
    a = fn.args
    hits = [f"param" for x in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg] if x and x.arg == "T"]
    calls = False
    stack = list(fn.body if isinstance(fn.body, list) else [fn.body])
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "T":
            hits.append("def T")
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(n, ast.Name) and n.id == "T" and isinstance(n.ctx, ast.Store):
            hits.append(f"assign line {n.lineno}")
        if isinstance(n, ast.ExceptHandler) and n.name == "T":
            hits.append("except as T")
        if isinstance(n, (ast.Import, ast.ImportFrom)) and any((al.asname or al.name) == "T" for al in n.names):
            hits.append("import as T")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "T":
            calls = True
        stack.extend(ast.iter_child_nodes(n))
    return hits, calls
for f in sorted((REPO / "visualizations").rglob("*.py")):
    if "/runs/" in str(f):
        continue
    src = f.read_text(encoding="utf-8")
    tree = ast.parse(src)
    imports_T = any(isinstance(n, ast.ImportFrom) and any(al.name == "T" for al in n.names) for n in tree.body)
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            hits, calls = locals_T(fn)
            if hits and imports_T:
                print(f"{f.relative_to(REPO)}:{fn.lineno} {'CALLS T(...) TOO' if calls else 'local T (no call now)'}: {hits[:3]}")
# the engine test's blind spots, demonstrated on a snippet
from test_i18n_engine import _shadowing
snip = Path("/tmp/rv18c_snip.py")
snip.write_text("from lfphys.i18n import T\n"
                "def a(x):\n    try:\n        pass\n    except ValueError as T:\n        pass\n    return T('x')\n"
                "def b(x):\n    def T(y):\n        return y\n    return T('x')\n"
                "def c(x):\n    from numpy import transpose as T\n    return T('x')\n")
import test_i18n_engine as te
te.PKG = Path("/tmp")
print("engine _shadowing on a snippet with except-as-T, nested def T, import-as-T:", _shadowing(snip))
