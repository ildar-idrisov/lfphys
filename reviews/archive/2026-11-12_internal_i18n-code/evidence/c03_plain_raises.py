"""Every raise of the engine (lfphys/lfphys) whose message is a plain string (not a T): file:line, exception, text."""
import ast
from pathlib import Path
from collections import Counter
PKG = Path("/w/lfphys/lfphys")
by_dir = Counter()
rows = []
for f in sorted(PKG.rglob("*.py")):
    src = f.read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and node.exc.args:
            a = node.exc.args[0]
            fn = node.exc.func
            name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "?")
            if isinstance(a, ast.Call) and getattr(a.func, "id", None) == "T":
                continue
            if isinstance(a, (ast.Constant, ast.JoinedStr, ast.BinOp)) or (isinstance(a, ast.Call) and getattr(a.func, "attr", "") == "format"):
                seg = ast.get_source_segment(src, a) or ""
                rel = f.relative_to(PKG)
                rows.append(f"{rel}:{node.lineno}: {name}({seg[:110]})")
                by_dir[str(rel.parent)] += 1
for r in rows:
    print(r)
print("TOTAL", len(rows))
for k, v in by_dir.most_common():
    print(f"{v:4d} {k}")
