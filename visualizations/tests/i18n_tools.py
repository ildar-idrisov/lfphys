# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Static tools of the interface's languages (RULES.md «Languages and i18n»; used by ``tests/test_i18n.py``).

* ``cyrillic_lines(path)``: the code lines of a .py, .js, .mjs or .html file with Cyrillic outside comments and
  docstrings (the Cyrillic guard). A line may opt out with the marker ``i18n-ok`` in a comment on it (a language's own
  name in the switch, a pattern that recognises Cyrillic).
* ``msgids_py(path)``, ``msgids_js(path)``, ``msgids_html(path)``: the literal msgids a file uses — ``T("...")`` in
  Python (also ``T(...)`` with adjacent literals), ``t("...")`` in JavaScript (also ``t('...')`` and template literals
  without substitutions), ``data-t`` texts and ``data-t-title`` titles in HTML.
* ``placeholders(text)``: the placeholder names of a msgid or a translation.

    python tests/i18n_tools.py --pending     the files the guard refuses now (one per line, relative to the repository)
    python tests/i18n_tools.py --lines F...  the refused lines of the given files
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import sys
import tokenize
from html.parser import HTMLParser
from pathlib import Path

VIZ = Path(__file__).resolve().parents[1]
REPO = VIZ.parent
CYR = re.compile("[\u0400-\u04ff]")
OPT_OUT = "i18n-ok"
PH = re.compile(r"\{(\w+)(?::[^{}]*)?\}")
SKIP_DIRS = {"node_modules", "vendor", "__pycache__", "runs", ".git", "fixtures"}


def code_files() -> list[Path]:
    """Every code file of the engine and the visualizations that the guard looks at."""
    out = []
    for root in (REPO / "lfphys" / "lfphys", VIZ):
        for f in root.rglob("*"):
            if f.suffix in (".py", ".js", ".mjs", ".html") and f.is_file() \
                    and not (set(f.relative_to(REPO).parts) & SKIP_DIRS):
                out.append(f)
    return sorted(out)


# --- the Cyrillic guard --------------------------------------------------------------------------------------------
def _docstring_lines(tree) -> set[int]:
    lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                lines.update(range(body[0].lineno, body[0].end_lineno + 1))
    return lines


def _py_lines(text: str) -> list[int]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [i + 1 for i, line in enumerate(text.splitlines()) if CYR.search(line)]
    doc = _docstring_lines(tree)
    src = text.splitlines()
    bad = set()
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and tok.start[0] in doc:
            continue
        if CYR.search(tok.string):
            for ln in range(tok.start[0], tok.end[0] + 1):
                if CYR.search(src[ln - 1]) and OPT_OUT not in src[ln - 1]:
                    bad.add(ln)
    return sorted(bad)


def strip_js_comments(text: str) -> str:
    """The text with JavaScript comments replaced by spaces (newlines kept), strings and template literals kept."""
    out = []
    i, n = 0, len(text)
    mode = None  # None | "'" | '"' | "`"
    depth = []  # template literal nesting: brace depth at each ${
    prev_sig = ""
    while i < n:
        c = text[i]
        if mode is None:
            if c == "/" and i + 1 < n and text[i + 1] == "/":
                j = text.find("\n", i)
                j = n if j < 0 else j
                out.append(" " * (j - i))
                i = j
                continue
            if c == "/" and i + 1 < n and text[i + 1] == "*":
                j = text.find("*/", i + 2)
                j = n if j < 0 else j + 2
                out.append("".join("\n" if ch == "\n" else " " for ch in text[i:j]))
                i = j
                continue
            if c == "/" and prev_sig in ("", "(", ",", "=", ":", "[", "!", "&", "|", "?", "{", "}", ";", "+", "-",
                                         "*", "%", "<", ">", "~", "^", "return"):
                # a regular expression literal: copied as it is up to its closing slash
                j, cls = i + 1, False
                while j < n and text[j] != "\n":
                    if text[j] == "\\":
                        j += 2
                        continue
                    if text[j] == "[":
                        cls = True
                    elif text[j] == "]":
                        cls = False
                    elif text[j] == "/" and not cls:
                        break
                    j += 1
                out.append(text[i:j + 1])
                i = j + 1
                prev_sig = "x"
                continue
            if c in "'\"`":
                mode = c
            elif c == "}" and depth:
                if depth[-1] == 0:
                    depth.pop()
                    mode = "`"
                else:
                    depth[-1] -= 1
            elif c == "{" and depth:
                depth[-1] += 1
            if not c.isspace():
                if c.isalnum() or c in "_$":
                    m = re.match(r"[\w$]+", text[i:])
                    word = m.group(0)
                    out.append(word)
                    i += len(word)
                    prev_sig = "return" if word in ("return", "typeof", "case", "of", "in") else "x"
                    continue
                prev_sig = c
            out.append(c)
            i += 1
            continue
        # inside a string or a template literal
        if c == "\\":
            out.append(text[i:i + 2])
            i += 2
            continue
        if mode == "`" and c == "$" and i + 1 < n and text[i + 1] == "{":
            depth.append(0)
            mode = None
            out.append("${")
            i += 2
            prev_sig = "{"
            continue
        if c == mode:
            mode = None
            prev_sig = "x"
        elif c == "\n" and mode in "'\"":
            mode = None
        out.append(c)
        i += 1
    return "".join(out)


def _js_lines(text: str) -> list[int]:
    code = strip_js_comments(text).splitlines()
    src = text.splitlines()
    return [i + 1 for i, line in enumerate(code) if CYR.search(line) and OPT_OUT not in src[i]]


def _html_lines(text: str) -> list[int]:
    # comments out; scripts and styles: their own comments out
    def blank(m):
        return "".join("\n" if ch == "\n" else " " for ch in m.group(0))
    t = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    t = re.sub(r"(<script\b[^>]*>)(.*?)(</script>)",
               lambda m: m.group(1) + strip_js_comments(m.group(2)) + m.group(3), t, flags=re.S | re.I)
    t = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)",
               lambda m: m.group(1) + re.sub(r"/\*.*?\*/", blank, m.group(2), flags=re.S) + m.group(3), t,
               flags=re.S | re.I)
    src = text.splitlines()
    return [i + 1 for i, line in enumerate(t.splitlines()) if CYR.search(line) and OPT_OUT not in src[i]]


def cyrillic_lines(path: Path) -> list[int]:
    text = Path(path).read_text(encoding="utf-8")
    if not CYR.search(text):
        return []
    suf = Path(path).suffix
    if suf == ".py":
        return _py_lines(text)
    if suf in (".js", ".mjs"):
        return _js_lines(text)
    if suf == ".html":
        return _html_lines(text)
    return []


def pending_file() -> Path:
    return VIZ / "tests" / "i18n_pending.txt"


def read_pending() -> set[str]:
    f = pending_file()
    if not f.is_file():
        return set()
    return {ln.strip() for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")}


# --- msgids ---------------------------------------------------------------------------------------------------------
def _const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def msgids_py(path: Path) -> list[tuple[str, int]]:
    """``T("...")`` (and ``ParamError(T(...))`` etc.): the first positional argument when it is a string literal."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args:
            f = node.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if name == "T":
                s = _const_str(node.args[0])
                if s:
                    out.append((s, node.lineno))
    return out


_JS_T = re.compile(r"""(?:(?<![\w$.])t\(\s*|\$t:\s*)(?:"((?:[^"\\\n]|\\.)*)"|'((?:[^'\\\n]|\\.)*)'|`((?:[^`\\$]|\\.|\$(?!\{))*)`)""")


def _unescape_js(s: str) -> str:
    return re.sub(r"\\(u\{[0-9a-fA-F]+\}|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)", _unesc, s)


def _unesc(m):
    e = m.group(1)
    if e.startswith("u{"):
        return chr(int(e[2:-1], 16))
    if e[0] in "ux" and len(e) > 1:
        return chr(int(e[1:], 16))
    return {"n": "\n", "t": "\t", "r": "\r", "0": "\0"}.get(e, e)


def msgids_js(path: Path) -> list[tuple[str, int]]:
    """``t("...")``, ``t('...')`` and ``t(`...`)`` (no substitutions), and inline texts ``{ $t: "..." }``, outside
    comments."""
    code = strip_js_comments(Path(path).read_text(encoding="utf-8"))
    out = []
    for m in _JS_T.finditer(code):
        s = next(g for g in m.groups() if g is not None)
        out.append((_unescape_js(s), code.count("\n", 0, m.start()) + 1))
    return out


class _HTMLMsgids(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.stack = []  # (tag, collecting)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "data-t-title" in a and a.get("title"):
            self.out.append((a["title"], self.getpos()[0]))
        if "data-t-placeholder" in a and a.get("placeholder"):
            self.out.append((a["placeholder"], self.getpos()[0]))
        if tag in ("br", "img", "input", "meta", "link", "hr"):
            return
        self.stack.append([tag, "data-t" in a, [], self.getpos()[0]])

    def handle_endtag(self, tag):
        while self.stack:
            t, collecting, buf, line = self.stack.pop()
            if collecting:
                s = re.sub(r"\s+", " ", "".join(buf)).strip()
                if s:
                    self.out.append((s, line))
            if self.stack:
                self.stack[-1][2].extend(buf)
            if t == tag:
                break

    def handle_data(self, data):
        if self.stack:
            self.stack[-1][2].append(data)


def msgids_html(path: Path) -> list[tuple[str, int]]:
    p = _HTMLMsgids()
    p.feed(Path(path).read_text(encoding="utf-8"))
    return p.out


_IMPORTS_T = re.compile(r'import\s*\{[^}]*\bt\b[^}]*\}\s*from\s*["\'][^"\']*i18n\.js["\']')
_PARAMS = re.compile(r"function\s*[\w$]*\s*\(([^()]*)\)|\(([^()]*)\)\s*=>|(?<![\w$.])([\w$]+)\s*=>"
                     r"|(?:^|[\s,{;])(?!(?:if|for|while|switch|catch|function|return)\b)[\w$]+\s*\(([^()]*)\)\s*\{")  # a method
_SHADOW = re.compile(r"(?:^|[\s,({\[])t\s*(?=[,)}\]=:]|$)")
_DECL = re.compile(r"\b(?:const|let|var)\s+(?:t\b|[{\[][^=;]*?(?<![\w$.])t\s*[,}\]])|\bcatch\s*\(\s*t\s*\)"
                   r"|\b(?:const|let|var)\s[^;\n]*?,\s*t\s*=(?!=)")  # also t later in a list of declarations


def shadowed_t(path: Path) -> list[int]:
    """The lines of a module that imports ``t`` from i18n.js where a parameter or a local is also named ``t`` (it
    would hide the translator inside its scope: a call t("…") there calls a number or a string)."""
    text = Path(path).read_text(encoding="utf-8")
    if not _IMPORTS_T.search(text):
        return []
    code = strip_js_comments(text)
    code = re.sub(r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'', '""', code)  # string contents out
    bad = set()
    for m in _PARAMS.finditer(code):
        params = next((g for g in m.groups() if g is not None), None)
        if params == "t" or (params is not None and _SHADOW.search(" " + params)):
            bad.add(code.count("\n", 0, m.start()) + 1)
    for m in _DECL.finditer(code):
        bad.add(code.count("\n", 0, m.start()) + 1)
    return sorted(bad)


def placeholders(text) -> set[str]:
    if isinstance(text, dict):  # plural forms: the union of their placeholders
        out = set()
        for v in text.values():
            out |= placeholders(v)
        return out
    return set(PH.findall(text or ""))


def needs_translation(msgid: str) -> bool:
    """A msgid made only of placeholders, digits, punctuation and symbols needs no translation."""
    return bool(re.search(r"[A-Za-z]", PH.sub("", msgid)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Static tools of the interface's languages: the Cyrillic guard.")
    ap.add_argument("--pending", action="store_true", help="list the files the guard refuses now")
    ap.add_argument("--lines", nargs="*", help="the refused lines of these files")
    ap.add_argument("--shadow", action="store_true", help="list JavaScript lines where a local hides the imported t()")
    a = ap.parse_args(argv)
    if a.lines:
        for f in a.lines:
            p = Path(f).resolve()
            src = p.read_text(encoding="utf-8").splitlines()
            for ln in cyrillic_lines(p):
                print(f"{f}:{ln}: {src[ln - 1].strip()[:140]}")
        return 0
    if a.shadow:
        for f in code_files():
            if f.suffix in (".js", ".mjs"):
                for ln in shadowed_t(f):
                    print(f"{f.relative_to(REPO).as_posix()}:{ln}")
        return 0
    if a.pending:
        for f in code_files():
            if cyrillic_lines(f):
                print(f.relative_to(REPO).as_posix())
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
