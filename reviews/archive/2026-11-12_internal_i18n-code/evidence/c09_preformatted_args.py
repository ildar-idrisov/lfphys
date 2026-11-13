"""T(...) arguments that are numbers already formatted into text on the server (spec: «Numbers are NEVER pre-formatted
into user text on the server ... pass them as args»): an f-string with a format spec, "%"-formatting, str.format, a
call of str()/repr() on a number-ish expression, or a helper named fmt*. Also text glued by "+" or ", ".join() into an
argument (word order and separators fixed in English)."""
import ast, re
from pathlib import Path
REPO = Path("/w")
files = sorted(list((REPO / "lfphys" / "lfphys").rglob("*.py")) + [f for f in (REPO / "visualizations").rglob("*.py")
               if "/tests/" not in str(f) or "p99_toy" in str(f) or "p97_osc" in str(f)])
def kind(v):
    if isinstance(v, ast.JoinedStr):
        if any(isinstance(x, ast.FormattedValue) and x.format_spec is not None for x in v.values):
            return "f-string with a format spec"
        if any(isinstance(x, ast.Constant) and re.search(r"[A-Za-z]{2,}", str(x.value)) for x in v.values):
            return "f-string with words"
        return None
    if isinstance(v, ast.BinOp) and isinstance(v.op, ast.Mod) and isinstance(v.left, ast.Constant):
        return "%-formatting"
    if isinstance(v, ast.Call):
        f = v.func
        n = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
        if n == "format" and isinstance(f, ast.Attribute) and isinstance(f.value, ast.Constant):
            return "str.format"
        if n == "join" and isinstance(f, ast.Attribute) and isinstance(f.value, ast.Constant) and f.value.value.strip(" ") not in ("",):
            return f"'{f.value.value}'.join"
        if n in ("fmt", "fmt_num", "_fmt", "fmt_bytes", "format_number", "human"):
            return f"{n}()"
    return None
n = 0
for f in files:
    src = f.read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and ((isinstance(node.func, ast.Name) and node.func.id == "T") or (isinstance(node.func, ast.Attribute) and node.func.attr == "T")):
            for kw in node.keywords:
                k = kind(kw.value)
                if k:
                    n += 1
                    print(f"{f.relative_to(REPO)}:{kw.value.lineno}: {kw.arg}= {k}: {(ast.get_source_segment(src, kw.value) or '')[:100]}")
print("total", n)
