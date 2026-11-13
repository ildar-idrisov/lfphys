# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Static tools of the interface's languages (RULES.md «Languages and i18n»; used by ``tests/test_i18n.py``).

* ``cyrillic_lines(path)``: the code lines of a .py, .js, .mjs or .html file with Cyrillic outside comments and
  docstrings (the Cyrillic guard). A line may opt out with the marker ``i18n-ok`` in a comment on it (a language's own
  name in the switch, a pattern that recognises Cyrillic).
* ``msgids_py(path)``, ``msgids_js(path)``, ``msgids_html(path)``: the literal msgids a file uses — ``T("...")`` in
  Python (also ``T(...)`` with adjacent literals), ``t("...")`` in JavaScript (also ``t('...')`` and template literals
  without substitutions), ``data-t`` texts and ``data-t-title`` titles in HTML.
* ``placeholders(text)``, ``placeholder_specs(text)``: the placeholder names (and formats) of a msgid or a translation;
  ``bad_specs(text)``: the formats the player cannot render.
* ``composed_py(path)``, ``composed_js(path)``: calls ``T(...)`` / ``t(...)`` whose msgid is built at run time
  (``"a" + b``, a template with ``${}``, ``.join``, a format): their msgids are invisible to the static test, so such a
  line names them in a comment ``i18n-msgids: "…" "…"`` (none: a text made elsewhere) — review i18n-code F6.
* ``msgids_data()``: the msgids the code shows from data files rather than from literals: every file of ``DATA_MSGIDS``
  with the keys whose values are English msgids (``planned.json``: ``title`` and ``text``, which the start page, the
  README and the site render with ``t()`` / ``render_in``). A msgid passed through a variable in code (a unit, a label
  used as a key) is named by a marker ``i18n-msgids:`` on its line instead.
* ``shadowed_t(path)`` (JavaScript: a parameter, a local or a function named ``t`` in a module that imports the
  translator) and ``shadowed_T(path)`` (Python: a function that binds ``T`` locally in a module that imports it) —
  review i18n-code F8.

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


def _py_value(tok: str) -> str:
    """A string token's value (escapes decoded: "\\u0428", "\\N{CYRILLIC …}"); the token itself when it is not a
    plain literal (an f-string's parts are read as written)."""
    try:
        v = ast.literal_eval(tok)
        return v if isinstance(v, str) else tok
    except (ValueError, SyntaxError):
        return tok


def _py_lines(text: str) -> list[int]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [i + 1 for i, line in enumerate(text.splitlines()) if CYR.search(line)]
    doc = _docstring_lines(tree)
    toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    marked = {tok.start[0] for tok in toks if tok.type == tokenize.COMMENT and OPT_OUT in tok.string}  # in a comment only
    bad = set()
    for tok in toks:
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and tok.start[0] in doc:
            continue
        s = _py_value(tok.string) if tok.type == tokenize.STRING else tok.string
        if CYR.search(s) or CYR.search(tok.string):
            lines = range(tok.start[0], tok.end[0] + 1)
            if not any(ln in marked for ln in lines):
                bad.add(tok.start[0])
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


_JS_ESC = re.compile(r"\\u(?:\{0*4[0-9a-fA-F]{2}\}|04[0-9a-fA-F]{2})")  # an escaped Cyrillic letter: \u0428, \u{428}


def _js_lines(text: str) -> list[int]:
    """Lines of code (comments out) with Cyrillic, also escaped; the marker counts in a comment only (not inside a
    string of the line: review i18n-code F8)."""
    code = strip_js_comments(text).splitlines()
    src = text.splitlines()
    return [i + 1 for i, line in enumerate(code)
            if (CYR.search(line) or _JS_ESC.search(line)) and not (OPT_OUT in src[i] and OPT_OUT not in line)]


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
#: the data files whose values are msgids, by the keys that hold them (relative to the repository): the static scan
#: counts them as used (test_i18n), so a catalogue entry for a planned item's title is not reported as unused
DATA_MSGIDS = {"visualizations/planned.json": ("title", "text")}


def msgids_data() -> dict[str, list[tuple[str, int]]]:
    """{file: [(msgid, item number)]} of the data files of ``DATA_MSGIDS`` (a list of objects each)."""
    import json
    out = {}
    for rel, keys in DATA_MSGIDS.items():
        items = json.loads((REPO / rel).read_text(encoding="utf-8"))
        out[rel] = [(x[k], n) for n, x in enumerate(items, 1) if isinstance(x, dict)
                    for k in keys if isinstance(x.get(k), str) and x[k].strip()]
    return out


def _const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


MARK = re.compile(r"i18n-msgids:(.*)$")
_QUOTED = re.compile(r"""\"((?:[^\"\\]|\\.)*)\"""")


def _marked_msgids(comment: str) -> list[str] | None:
    """The msgids a marker ``i18n-msgids: "…" "…"`` in a comment names (an empty list: none; None: no marker)."""
    m = MARK.search(comment or "")
    return None if m is None else [_unescape_js(x) for x in _QUOTED.findall(m.group(1))]


def _literals(node, consts: dict) -> list[str] | None:
    """The msgids an argument can be: a literal, a module constant, or a choice between such (``a if c else b``,
    ``c and "a" or "b"``); None when it is anything else."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.Name) and node.id in consts:
        return [consts[node.id]]
    if isinstance(node, ast.IfExp):
        a, b = _literals(node.body, consts), _literals(node.orelse, consts)
        return a + b if a is not None and b is not None else None
    if isinstance(node, ast.BoolOp):
        parts = [_literals(v, consts) for v in node.values]
        lits = [x for p in parts if p for x in p]
        return lits or None
    return None


def _py_tree(path: Path):
    text = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(text)
    consts = {}
    for node in tree.body:  # module constants: MSG = "…"
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            consts[node.targets[0].id] = node.value.value
    comments = {}
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            comments[tok.start[0]] = tok.string
    return tree, consts, comments


def _t_calls(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args:
            f = node.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if name == "T":
                yield node


def msgids_py(path: Path) -> list[tuple[str, int]]:
    """``T("...")`` (and ``ParamError(T(...))`` etc.): the first positional argument when it is a string literal, a
    module constant or a choice between such; and the msgids a marker ``i18n-msgids:`` on a call's lines names."""
    tree, consts, comments = _py_tree(path)
    out = []
    for node in _t_calls(tree):
        for s in _literals(node.args[0], consts) or []:
            if s:
                out.append((s, node.lineno))
        for ln in range(node.lineno, (node.end_lineno or node.lineno) + 1):
            for s in _marked_msgids(comments.get(ln, "")) or []:
                out.append((s, ln))
    return out


def composed_py(path: Path) -> list[int]:
    """Lines of ``T(...)`` calls whose msgid is built at run time (a concatenation, an f-string, a call, a format)
    without a marker ``i18n-msgids:`` in a comment on the call's lines. ``T(x)`` of a name or an attribute is a text
    made elsewhere (rebuilt), not a msgid."""
    tree, consts, comments = _py_tree(path)
    bad = []
    for node in _t_calls(tree):
        a = node.args[0]
        if _literals(a, consts) is not None or isinstance(a, (ast.Name, ast.Attribute, ast.Subscript)):
            continue
        if any(_marked_msgids(comments.get(ln, "")) is not None
               for ln in range(node.lineno, (node.end_lineno or node.lineno) + 1)):
            continue
        bad.append(node.lineno)
    return bad


def _imports_T(tree) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any((a.asname or a.name) == "T" for a in node.names):
            return True
    return False


def shadowed_T(path: Path) -> list[int]:
    """In a module that imports ``T``: the functions that bind ``T`` in their own scope — a parameter, an assignment, a
    loop or ``with`` target, ``except … as T``, a nested ``def T`` / ``class T``, ``import … as T`` (a later
    ``T("…")`` there would raise UnboundLocalError or call something else: review i18n-code F8)."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    if not _imports_T(tree):
        return []
    out = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        a = fn.args
        local = any(x.arg == "T" for x in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg] if x)
        body = fn.body if isinstance(fn.body, list) else [fn.body]
        stack = list(body)
        while stack and not local:  # this function's own scope
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                local = n.name == "T"
                continue
            if isinstance(n, ast.Lambda):
                continue
            if isinstance(n, ast.Name) and n.id == "T" and isinstance(n.ctx, (ast.Store, ast.Del)):
                local = True
            elif isinstance(n, ast.ExceptHandler) and n.name == "T":
                local = True
            elif isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.asname or x.name.split(".")[0]) == "T"
                                                                       for x in n.names):
                local = True
            stack.extend(ast.iter_child_nodes(n))
        if local:
            out.append(fn.lineno)
    return sorted(out)


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


def _blank_strings(code: str) -> str:
    """Code (comments out) with the contents of strings and template literals blanked (their quotes kept), so that
    brackets inside strings do not count; the ``${…}`` of a template stays code."""
    out, i, n = [], 0, len(code)
    stack = []  # template nesting: brace depth at each ${
    mode = None
    while i < n:
        c = code[i]
        if mode is None:
            if c in "'\"`":
                mode = c
                out.append(c)
            elif c == "}" and stack:
                if stack[-1] == 0:
                    stack.pop()
                    mode = "`"
                else:
                    stack[-1] -= 1
                out.append(c)
            else:
                if c == "{" and stack:
                    stack[-1] += 1
                out.append(c)
            i += 1
            continue
        if c == "\\":
            out.append("  " if code[i + 1:i + 2] != "\n" else " \n")
            i += 2
            continue
        if mode == "`" and c == "$" and code[i + 1:i + 2] == "{":
            stack.append(0)
            mode = None
            out.append("${")
            i += 2
            continue
        if c == mode or (c == "\n" and mode in "'\""):
            mode = None
            out.append(c)
        else:
            out.append("\n" if c == "\n" else " ")
        i += 1
    return "".join(out)


def _close(code: str, i: int) -> int:
    """The index of the bracket closing the one at ``i`` (in blanked code)."""
    depth = 0
    for j in range(i, len(code)):
        if code[j] in "([{":
            depth += 1
        elif code[j] in ")]}":
            depth -= 1
            if depth == 0:
                return j
    return len(code)


def _split_top(s: str, sep: str = ",") -> list[tuple[int, str]]:
    """``s`` split at top-level separators: (offset, part)."""
    out, depth, start = [], 0, 0
    for j, c in enumerate(s):
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == sep and depth == 0:
            out.append((start, s[start:j]))
            start = j + 1
    out.append((start, s[start:]))
    return out


_LIT = re.compile(r"""\s*(?:"((?:[^"\\\n]|\\.)*)"|'((?:[^'\\\n]|\\.)*)'|`((?:[^`\\$]|\\.|\$(?!\{))*)`)\s*$""")
_CALL_T = re.compile(r"(?<![\w$.])t\(")


def _js_calls(path: Path):
    """(line, first argument as written, the same blanked) of every call ``t(…)``, outside comments."""
    code = strip_js_comments(Path(path).read_text(encoding="utf-8"))
    blank = _blank_strings(code)
    for m in _CALL_T.finditer(blank):
        o = m.end() - 1
        c = _close(blank, o)
        parts = _split_top(blank[o + 1:c])
        off, first_b = parts[0]
        first = code[o + 1 + off:o + 1 + off + len(first_b)]
        yield code.count("\n", 0, m.start()) + 1, first, first_b


def _js_choice(first: str, first_b: str) -> list[str] | None:
    """The msgids of ``cond ? "a" : "b"`` (also nested) when every branch is a literal; None otherwise."""
    q = next((j for j, c in enumerate(first_b) if c == "?" and first_b[j + 1:j + 2] not in ".?"
              and first_b[max(j - 1, 0)] != "?"), -1)
    if q < 0:
        return None
    rest, rest_b = first[q + 1:], first_b[q + 1:]
    depth, colon = 0, -1
    for j, c in enumerate(rest_b):  # the ":" of this "?" (nested ternaries in the branches)
        if c in "([{?":
            depth += 1 if c != "?" else 0
        if c in ")]}":
            depth -= 1
        if c == ":" and depth == 0:
            colon = j
            break
    if colon < 0:
        return None
    out = []
    for part, part_b in ((rest[:colon], rest_b[:colon]), (rest[colon + 1:], rest_b[colon + 1:])):
        m = _LIT.match(part)
        if m and not (m.group(3) is not None and "${" in m.group(3)):
            out.append(_unescape_js(next(g for g in m.groups() if g is not None)))
            continue
        sub = _js_choice(part, part_b)
        if sub is None:
            return None
        out += sub
    return out


def msgids_js(path: Path) -> list[tuple[str, int]]:
    """``t("...")``, ``t('...')`` and ``t(`...`)`` (no substitutions), a choice between literals ``t(c ? "a" : "b")``,
    inline texts ``{ $t: "..." }``, and the msgids a marker ``i18n-msgids:`` names, outside comments."""
    text = Path(path).read_text(encoding="utf-8")
    code = strip_js_comments(text)
    out = []
    for m in _JS_T.finditer(code):
        s = next(g for g in m.groups() if g is not None)
        out.append((_unescape_js(s), code.count("\n", 0, m.start()) + 1))
    for line, first, first_b in _js_calls(path):
        for s in _js_choice(first, first_b) or []:
            out.append((s, line))
    for i, ln in enumerate(text.splitlines()):
        code_ln = code.splitlines()[i] if i < len(code.splitlines()) else ""
        if "i18n-msgids:" in ln and "i18n-msgids:" not in code_ln:  # in a comment
            out += [(s, i + 1) for s in _marked_msgids(ln[ln.index("i18n-msgids:"):]) or []]
    return out


def composed_js(path: Path) -> list[int]:
    """Lines of ``t(…)`` calls whose msgid is built at run time — a template with ``${…}``, a concatenation with a
    literal — without a marker ``i18n-msgids:`` in a comment on the line. ``t(x)`` of a name, a member or a call is a
    text the server sent (the dynamic test reads those)."""
    text = Path(path).read_text(encoding="utf-8")
    src = text.splitlines()
    code = strip_js_comments(text).splitlines()
    bad = []
    for line, first, first_b in _js_calls(path):
        f = first.strip()
        composed = (f.startswith("`") and "${" in f) or (
            any(c == "+" for c in first_b) and re.search(r"""["'`]""", first_b) is not None and _js_choice(first, first_b) is None)
        if not composed:
            continue
        ln = src[line - 1] if line - 1 < len(src) else ""
        cl = code[line - 1] if line - 1 < len(code) else ""
        if "i18n-msgids:" in ln and "i18n-msgids:" not in cl:
            continue
        bad.append(line)
    return bad


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
_NOT_PARAMS = {"if", "for", "while", "switch", "catch", "with", "return", "typeof", "await", "new", "in", "of", "do"}


def _names(pattern: str) -> list[str]:
    """The names a parameter or a declarator binds: ``a = f(1)`` → a; ``...a`` → a; ``{ a, b: c, t }`` → a, c, t;
    ``[a, , t]`` → a, t."""
    p = pattern.strip()
    # its default value or initialiser out (the first top-level "=" that is not "==", "=>")
    depth = 0
    for j, c in enumerate(p):
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "=" and depth == 0 and p[j + 1:j + 2] not in "=>" and p[j - 1:j] not in "=!<>":
            p = p[:j].strip()
            break
    p = p.lstrip(".").strip()
    if p[:1] in "{[":
        inner = p[1:_close(p, 0)]
        out = []
        for _, part in _split_top(inner):
            part = part.strip()
            if not part:
                continue
            if p[0] == "{" and ":" in part.split("=")[0]:
                part = part.split(":", 1)[1]
            out += _names(part)
        return out
    m = re.match(r"([\w$]+)", p)
    return [m.group(1)] if m else []


def shadowed_t(path: Path) -> list[int]:
    """The lines of a module that imports ``t`` from i18n.js where a parameter, a local, a catch variable or a function
    is also named ``t`` (it would hide the translator inside its scope: a call t("…") there calls a number or a
    string). Parameter lists and declarations are split at their top-level commas, so defaults with calls, later names
    without "=", destructuring and methods are seen (review i18n-code F8)."""
    text = Path(path).read_text(encoding="utf-8")
    if not _IMPORTS_T.search(strip_js_comments(text)):  # an import in a comment (i18n.js's own usage note) is none
        return []
    code = _blank_strings(strip_js_comments(text))
    line = lambda i: code.count("\n", 0, i) + 1  # noqa: E731
    bad = set()
    # parameter lists: "(…)" followed by "=>" or "{" (a function, a method), not after if/for/while/…; "x =>"
    for m in re.finditer(r"\(", code):
        o = m.start()
        c = _close(code, o)
        after = code[c + 1:c + 40].lstrip()
        before = re.search(r"([\w$]+)\s*$", code[max(0, o - 40):o])
        if not (after.startswith("=>") or after.startswith("{")):
            continue
        if before and before.group(1) in _NOT_PARAMS:
            if before.group(1) == "catch" and "t" in _names(code[o + 1:c]):
                bad.add(line(o))
            continue
        if any("t" in _names(part) for _, part in _split_top(code[o + 1:c])):
            bad.add(line(o))
    for m in re.finditer(r"(?<![\w$.])t\s*=>", code):
        bad.add(line(m.start()))
    for m in re.finditer(r"\bfunction\s*\*?\s*t\s*\(|\bclass\s+t\b", code):
        bad.add(line(m.start()))
    # declarations: let / const / var up to the end of the statement (";" or a line end at depth 0)
    for m in re.finditer(r"(?<![\w$.])(?:let|const|var)\s", code):
        j, depth = m.end(), 0
        while j < len(code):
            ch = code[j]
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif depth == 0 and (ch == ";" or (ch == "\n" and not code[m.end():j].rstrip().endswith((",", "=")))):
                break
            j += 1
        decl = code[m.end():j]
        decl = re.split(r"\s(?:of|in)\s", decl)[0]  # for (const t of …)
        if any("t" in _names(part) for _, part in _split_top(decl)):
            bad.add(line(m.start()))
    return sorted(bad)


PH_SPEC = re.compile(r"\{(\w+)(?::([^{}]*))?\}")
#: the formats the player renders (player/js/i18n.js fmt, lfphys.i18n): nothing, .Ng/.Nf/.Ne, d, each with "+"; cap, unit
SPEC_OK = re.compile(r"^(\+?((\.\d+)?[gfe]|d)?|cap|unit)$")


def placeholder_specs(text) -> set[tuple[str, str]]:
    """(name, format) of every placeholder; plural forms: the union."""
    if isinstance(text, dict):
        out = set()
        for v in text.values():
            out |= placeholder_specs(v)
        return out
    return {(m.group(1), m.group(2) or "") for m in PH_SPEC.finditer(text or "")
            if not (m.group(2) or "")[:1].isspace()}  # "{kind: law, id}": braces of the text, not a placeholder


def bad_specs(text) -> list[str]:
    """The placeholder formats of a text the player cannot render (a width, ",", "%", "x": review i18n-code F6, F10)."""
    return sorted({f"{{{n}:{sp}}}" for n, sp in placeholder_specs(text) if not SPEC_OK.match(sp)})


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
