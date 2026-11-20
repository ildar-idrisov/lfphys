// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The formula columns of a lab step (design lfphys/sources/explore_EX2_2026-11-18_design.md §5 F5): a column
// {id, label, expr} is a formula of the step's earlier columns, evaluated on each row with its error propagated. This is
// server/lfviz/expr.py in the browser, the same grammar and the same arithmetic operation for operation; the shared
// fixture tests/fixtures/expr_cases.json (made with mpmath's derivatives by fixtures/make_expr_cases.py) holds both to
// 1e-12 (expr.test.mjs, tests/test_expr.py). There is no eval and no Function: a small parser of this grammar only,
// names looked up in Maps (a column named "constructor" or "__proto__" is an unknown name, never a property), and the
// formulas come from the registry, never from the viewer.
//
//   expr    := term (("+" | "-") term)*
//   term    := unary (("*" | "/") unary)*
//   unary   := ("-" | "+") unary | power
//   power   := primary ("^" unary)?           right-associative; -2^2 = -(2^2); 2^-1 = 0.5
//   primary := number | "pi" | column | function "(" expr ")" | "(" expr ")"
//
// FUNCTIONS: sqrt ln exp abs, sin cos tan asin acos atan (radians), sind cosd tand asind acosd atand (degrees).
// The error: σ_f² = Σᵢ (∂f/∂xᵢ·σᵢ)² + ½ ΣᵢΣⱼ (∂²f/∂xᵢ∂xⱼ·σᵢσⱼ)² (the second-order variance for independent normal
// inputs: the mixed terms since review R2-F F2) over the formula's distinct columns in the order of their first
// appearance, the derivatives by hyper-dual numbers [a, b, c, d] = a + b·ε₁ + c·ε₂ + d·ε₁ε₂ (ε₁² = ε₂² = 0): with the
// input [x, 1, 1, 0] the result's b is ∂f/∂x and its d is ∂²f/∂x²; with xᵢ [xᵢ, 1, 0, 0] and xⱼ [xⱼ, 0, 1, 0] its d is
// ∂²f/∂xᵢ∂xⱼ. t1 is the first-order sum, t2 the second-order one (diagonal and mixed). An input with σ = 0 adds nothing;
// |x| at x = 0 (a kink) and √x at 0 have no error for an input with σ > 0 (Undefined "error_undefined").
//
//   parse(text, {columns, later})  → {text, node, names} or throws ExprError {code, pos, name}
//   evaluate(expr, values)         → {v, e, t1, t2}, values: Map or object of {v, e} (or [v, e], or a number); throws
//                                    Undefined {reason} (REASONS) for a value the formula does not define

export const FUNCTIONS = ["sqrt", "ln", "exp", "abs", "sin", "cos", "tan", "asin", "acos", "atan",
  "sind", "cosd", "tand", "asind", "acosd", "atand"];
const FN = new Set(FUNCTIONS);
const CONST = new Map([["pi", Math.PI]]);
export const RESERVED = new Set([...FUNCTIONS, ...CONST.keys()]);
export const MAX_CHARS = 400, MAX_DEPTH = 48;
export const CODES = ["syntax", "number", "unknown_name", "later_column", "not_callable", "no_argument", "too_long", "too_deep", "empty"];
export const REASONS = ["sqrt_negative", "division_by_zero", "log_nonpositive", "asin_domain", "acos_domain", "power",
  "not_finite", "missing", "error_undefined"];
const DEG = Math.PI / 180, RAD = 180 / Math.PI;

export class ExprError extends Error {
  constructor(code, pos = 0, name = null, text = "") {
    super(`${code} at ${pos}${name ? ` (${name})` : ""}${text ? `: ${text}` : ""}`);
    this.code = code; this.pos = pos; this.name = name;
  }
}
export class Undefined extends Error {
  constructor(reason) { super(reason); this.reason = reason; }
}

// --- the parser -------------------------------------------------------------------------------------------------------
const NUM = /(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?/y;
const NAME = /[A-Za-z_][A-Za-z0-9_]*/y;
const OPS = new Set(["-", "+", "*", "/", "^", "(", ")"]);
// ASCII only, as expr.py (review R2-F F8: JavaScript's \s took Unicode spaces that Python refused, Python's isspace
// \x1c–\x1f and \x85 that JavaScript refused; \d is ASCII in both now): a formula parses in both or in neither
const isSpace = (ch) => ch === " " || ch === "\t" || ch === "\n" || ch === "\r" || ch === "\f" || ch === "\v";

function tokens(text) {
  const out = [];
  let i = 0;
  const n = text.length;
  while (i < n) {
    const ch = text[i];
    if (isSpace(ch)) { i++; continue; }
    NUM.lastIndex = i; NAME.lastIndex = i;
    const mn = NUM.exec(text);
    if (mn) {
      const v = Number(mn[0]);
      if (!Number.isFinite(v)) throw new ExprError("number", i, null, "a number too large");
      out.push(["num", v, i]); i += mn[0].length; continue;
    }
    const mm = NAME.exec(text);
    if (mm) { out.push(["name", mm[0], i]); i += mm[0].length; continue; }
    if (OPS.has(ch)) { out.push(["op", ch, i]); i++; continue; }
    throw new ExprError("syntax", i, null, `unexpected character ${JSON.stringify(ch)}`);
  }
  out.push(["end", null, n]);
  return out;
}

class Parser {
  constructor(text, columns, later) {
    this.toks = tokens(text); this.k = 0;
    this.columns = columns === null || columns === undefined ? null : new Set(columns);
    this.later = new Set(later || []);
    this.names = [];
  }
  peek() { return this.toks[this.k]; }
  take() { return this.toks[this.k++]; }
  isOp(ch) { const tk = this.peek(); return tk[0] === "op" && tk[1] === ch; }
  expect(ch) { const tk = this.take(); if (tk[0] !== "op" || tk[1] !== ch) throw new ExprError("syntax", tk[2], null, `${JSON.stringify(ch)} expected`); }
  expr(depth) {
    if (depth > MAX_DEPTH) throw new ExprError("too_deep", this.peek()[2]);
    let node = this.term(depth);
    while (this.isOp("+") || this.isOp("-")) { const op = this.take()[1]; node = ["bin", op, node, this.term(depth)]; }
    return node;
  }
  term(depth) {
    let node = this.unary(depth);
    while (this.isOp("*") || this.isOp("/")) { const op = this.take()[1]; node = ["bin", op, node, this.unary(depth)]; }
    return node;
  }
  unary(depth) {
    if (depth > MAX_DEPTH) throw new ExprError("too_deep", this.peek()[2]);
    if (this.isOp("-")) { this.take(); return ["neg", this.unary(depth + 1)]; }
    if (this.isOp("+")) { this.take(); return this.unary(depth + 1); }
    return this.power(depth);
  }
  power(depth) {
    const base = this.primary(depth);
    if (this.isOp("^")) { this.take(); return ["bin", "^", base, this.unary(depth + 1)]; }
    return base;
  }
  primary(depth) {
    const [kind, val, pos] = this.take();
    if (kind === "num") return ["num", val];
    if (kind === "op" && val === "(") { const node = this.expr(depth + 1); this.expect(")"); return node; }
    if (kind === "name") {
      const call = this.isOp("(");
      if (FN.has(val)) {
        if (!call) throw new ExprError("no_argument", pos, val, "a function needs its argument in parentheses");
        this.take();
        const arg = this.expr(depth + 1);
        this.expect(")");
        return ["call", val, arg];
      }
      if (call) throw new ExprError("not_callable", pos, val, "only the grammar's functions can be called");
      if (CONST.has(val)) return ["num", CONST.get(val)];
      if (this.later.has(val)) throw new ExprError("later_column", pos, val, "a formula names earlier columns only");
      if (this.columns !== null && !this.columns.has(val)) throw new ExprError("unknown_name", pos, val);
      if (!this.names.includes(val)) this.names.push(val);
      return ["var", val];
    }
    if (kind === "end") throw new ExprError("syntax", pos, null, "the formula ends too early");
    throw new ExprError("syntax", pos, null, `${JSON.stringify(val)} unexpected`);
  }
}

export function parse(text, { columns = null, later = [] } = {}) {
  if (typeof text !== "string") throw new ExprError("syntax", 0, null, "a formula is a string");
  if (text.length > MAX_CHARS) throw new ExprError("too_long", MAX_CHARS);
  if (!text.trim()) throw new ExprError("empty", 0);
  const p = new Parser(text, columns, later);
  const node = p.expr(0);
  const tk = p.peek();
  if (tk[0] !== "end") throw new ExprError("syntax", tk[2], null, `${JSON.stringify(tk[1])} unexpected`);
  return Object.freeze({ text, node, names: Object.freeze([...p.names]) });
}

// --- hyper-dual arithmetic [a, b, c, d] = a + b·ε₁ + c·ε₂ + d·ε₁ε₂ (server/lfviz/expr.py, operation for operation) ------
const isConst = (x) => x[1] === 0 && x[2] === 0 && x[3] === 0;
// g(x) for g(a) = f0, g′(a) = f1, g″(a) = f2; a constant stays a constant
const chain = (x, f0, f1, f2) => (isConst(x) ? [f0, 0, 0, 0] : [f0, f1 * x[1], f1 * x[2], f1 * x[3] + f2 * x[1] * x[2]]);
const mul = (x, y) => [x[0] * y[0], x[0] * y[1] + x[1] * y[0], x[0] * y[2] + x[2] * y[0], x[0] * y[3] + x[1] * y[2] + x[2] * y[1] + x[3] * y[0]];
const scale = (x, k) => [x[0] * k, x[1] * k, x[2] * k, x[3] * k];
function div(x, y) {
  if (y[0] === 0) throw new Undefined("division_by_zero");
  const q = x[0] / y[0];
  const qb = (x[1] - q * y[1]) / y[0];
  const qc = (x[2] - q * y[2]) / y[0];
  const qd = (x[3] - q * y[3] - qb * y[2] - qc * y[1]) / y[0];
  return [q, qb, qc, qd];
}
// a ** e as IEEE gives it (an overflow is Infinity, 0 ** negative is Infinity), for a ≥ 0 or a whole e
const pw = (a, e) => (a === 0 && e < 0 ? Infinity : Math.pow(a, e));
const whole = (e) => Number.isFinite(e) && e === Math.floor(e);
function pow(x, y) {
  if (isConst(y)) {
    const p = y[0];
    if (x[0] < 0 && !whole(p)) throw new Undefined("power");
    if (x[0] === 0 && p < 0) throw new Undefined("division_by_zero");
    if (isConst(x)) return [pw(x[0], p), 0, 0, 0];
    if (p === 0) return [1, 0, 0, 0];
    if (p === 1) return x;
    const f0 = pw(x[0], p);
    const f1 = x[0] !== 0 || p >= 1 ? p * pw(x[0], p - 1) : NaN;
    const f2 = x[0] !== 0 || p >= 2 ? p * (p - 1) * pw(x[0], p - 2) : NaN;
    return chain(x, f0, f1, f2);
  }
  if (x[0] <= 0) throw new Undefined("power");
  return apply("exp", mul(y, apply("ln", x)));
}
function apply(fn, x) {
  const a = x[0];
  switch (fn) {
    case "sqrt": {
      if (a < 0) throw new Undefined("sqrt_negative");
      const r = Math.sqrt(a);
      if (a === 0) return chain(x, 0, NaN, NaN);
      return chain(x, r, 0.5 / r, -0.25 / (a * r));
    }
    case "ln":
      if (a <= 0) throw new Undefined("log_nonpositive");
      return chain(x, Math.log(a), 1 / a, -1 / (a * a));
    case "exp": { const e = Math.exp(a); return chain(x, e, e, e); }
    case "abs":  // the kink: no derivative at 0 (as √ at 0; review R2-F F9)
      if (a === 0) return chain(x, 0, NaN, NaN);
      return a < 0 ? [-x[0], -x[1], -x[2], -x[3]] : x;
    case "sin": { const s = Math.sin(a), c = Math.cos(a); return chain(x, s, c, -s); }
    case "cos": { const s = Math.sin(a), c = Math.cos(a); return chain(x, c, -s, -c); }
    case "tan": { const tn = Math.tan(a), sec2 = 1 + tn * tn; return chain(x, tn, sec2, 2 * tn * sec2); }
    case "asin": case "acos": {
      if (!(a >= -1 && a <= 1)) throw new Undefined(`${fn}_domain`);
      const v = fn === "asin" ? Math.asin(a) : Math.acos(a);
      if (a === -1 || a === 1) return chain(x, v, NaN, NaN);
      const s = 1 - a * a, r = Math.sqrt(s), k = fn === "asin" ? 1 : -1;
      return chain(x, v, k / r, k * a / (s * r));
    }
    case "atan": { const s = 1 + a * a; return chain(x, Math.atan(a), 1 / s, -2 * a / (s * s)); }
    case "sind": case "cosd": case "tand": return apply(fn.slice(0, -1), scale(x, DEG));
    case "asind": case "acosd": case "atand": return scale(apply(fn.slice(0, -1), x), RAD);
    default: throw new Undefined("not_finite");  // unreachable: the parser admits the grammar's functions only
  }
}
function ev(node, env) {
  switch (node[0]) {
    case "num": return [node[1], 0, 0, 0];
    case "var": return env.get(node[1]);
    case "neg": { const x = ev(node[1], env); return [-x[0], -x[1], -x[2], -x[3]]; }
    case "call": return apply(node[1], ev(node[2], env));
    case "bin": {
      const op = node[1], a = ev(node[2], env), b = ev(node[3], env);
      if (op === "+") return [a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3]];
      if (op === "-") return [a[0] - b[0], a[1] - b[1], a[2] - b[2], a[3] - b[3]];
      if (op === "*") return mul(a, b);
      if (op === "/") return div(a, b);
      return pow(a, b);
    }
    default: throw new Undefined("not_finite");
  }
}

// an input as [value, sigma]: {v, e}, [v, e] or a number (σ 0); null: empty
function pair(x) {
  if (x === null || x === undefined) return [null, 0];
  if (Array.isArray(x)) return [x[0] === null || x[0] === undefined ? null : Number(x[0]), x.length > 1 ? Number(x[1]) : 0];
  if (typeof x === "object") return [x.v === null || x.v === undefined ? null : Number(x.v), x.e === undefined ? 0 : x.e === null ? NaN : Number(x.e)];
  return [Number(x), 0];
}
const lookup = (values, name) => (values instanceof Map ? values.get(name) : Object.hasOwn(values || {}, name) ? values[name] : undefined);

// The formula's value and error at `values` (Map or object of {v, e}): {v, e, t1, t2}; throws Undefined (its reason)
export function evaluate(expr, values) {
  if (typeof expr === "string") expr = parse(expr);
  const env = new Map(), sig = new Map();
  for (const name of expr.names) {
    const [v, e] = pair(lookup(values, name));
    if (v === null || !Number.isFinite(v)) throw new Undefined("missing");
    env.set(name, [v, 0, 0, 0]); sig.set(name, e);
  }
  const value = ev(expr.node, env)[0];
  if (!Number.isFinite(value)) throw new Undefined("not_finite");
  let t1 = 0, t2 = 0;
  const live = [];  // the inputs with an error, in the order of the names
  for (const name of expr.names) {
    const s = sig.get(name);
    if (s === 0) continue;  // an exact input adds nothing
    if (!Number.isFinite(s) || s < 0) throw new Undefined("error_undefined");
    const v = env.get(name)[0];
    env.set(name, [v, 1, 1, 0]);
    const r = ev(expr.node, env);
    env.set(name, [v, 0, 0, 0]);
    const a = r[1] * s;
    const b = r[3] * s * s;
    t1 += a * a;
    t2 += 0.5 * b * b;
    live.push(name);
  }
  for (let i = 0; i < live.length; i++) {  // the mixed second derivatives (review R2-F F2): xᵢ = [v,1,0,0], xⱼ = [v,0,1,0]
    for (let j = i + 1; j < live.length; j++) {
      const ni = live[i], nj = live[j], vi = env.get(ni)[0], vj = env.get(nj)[0];
      env.set(ni, [vi, 1, 0, 0]); env.set(nj, [vj, 0, 1, 0]);
      const r = ev(expr.node, env);
      env.set(ni, [vi, 0, 0, 0]); env.set(nj, [vj, 0, 0, 0]);
      const c = r[3] * sig.get(ni) * sig.get(nj);
      t2 += c * c;
    }
  }
  const err = Number.isFinite(t1 + t2) ? Math.sqrt(t1 + t2) : NaN;
  if (!Number.isFinite(err)) throw new Undefined("error_undefined");
  return { v: value, e: err, t1, t2 };
}
