// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Small DOM and formatting helpers shared by the catalogue, the player and the visualization views.

export function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") e.className = v;
    else if (k === "style" && typeof v === "object") Object.assign(e.style, v);
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (k === "html") e.innerHTML = v;
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) if (c !== null && c !== undefined && c !== false) e.append(c.nodeType ? c : String(c));
  return e;
}

// replaceChildren that, like el(), flattens arrays and skips null / undefined / false (the native one would print them)
export function fill(node, ...children) {
  node.replaceChildren(...children.flat(Infinity).filter((c) => c !== null && c !== undefined && c !== false));
  return node;
}

export function panel(title, body, { closed = false } = {}) {
  const p = el("div", { class: "panel" + (closed ? " closed" : "") }, el("h4", {}, title), el("div", { class: "body" }, body));
  p.firstChild.addEventListener("click", () => p.classList.toggle("closed"));
  return p;
}

const SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹";
function sup(n) { return String(n).replace("-", "⁻").replace(/\d/g, (d) => SUP[d]); }

// number with significant digits, scientific notation with a superscript exponent when large/small; one Russian format
// everywhere (review LB1-p02-ux X6): a decimal comma also in the mantissa, the minus sign −. The server's texts use the
// same rule (lfviz.playground.fmt)
export function num(x, digits = 6) {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  if (!Number.isFinite(x)) return x > 0 ? "∞" : "−∞";
  const a = Math.abs(x);
  if (a !== 0 && (a >= 1e7 || a < 1e-4)) {
    let e = Math.floor(Math.log10(a));
    let m = Number((x / 10 ** e).toPrecision(Math.min(digits, 12)));
    if (Math.abs(m) >= 10) { m /= 10; e += 1; }  // rounded up to 10
    const ms = m.toPrecision(Math.min(digits, 12)).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
    return `${ms.replace(".", ",").replace("-", "−")}·10${sup(e)}`;
  }
  return Number(x.toPrecision(digits)).toLocaleString("ru-RU", { maximumSignificantDigits: digits }).replace("-", "−");
}

// time in a human scale: ps..s, minutes, hours, days, years
export function time(t, digits = 6) {
  if (t === null || t === undefined || Number.isNaN(t)) return "—";
  const a = Math.abs(t), s = t < 0 ? "−" : "";
  const Y = 365.25 * 86400;
  if (a === 0) return "0 с";
  if (a < 1e-9) return s + num(a * 1e12, digits) + " пс";
  if (a < 1e-6) return s + num(a * 1e9, digits) + " нс";
  if (a < 1e-3) return s + num(a * 1e6, digits) + " мкс";
  if (a < 1) return s + num(a * 1e3, digits) + " мс";
  if (a < 120) return s + num(a, digits) + " с";
  if (a < 7200) { const m = Math.floor(a / 60); return `${s}${m} мин ${(a - 60 * m).toFixed(2)} с`; }
  if (a < 2 * 86400) return s + num(a / 3600, digits) + " ч";
  if (a < Y) return s + num(a / 86400, digits) + " сут";
  if (a < 1e6 * Y) return s + num(a / Y, digits) + " лет";
  if (a < 1e9 * Y) return s + num(a / Y / 1e6, digits) + " млн лет";
  return s + num(a / Y / 1e9, digits) + " млрд лет";
}

// SI length with optional preferred astronomical unit
export function length(x, units = {}, digits = 6) {
  const a = Math.abs(x);
  if (units.ly && a >= 0.01 * units.ly) return num(x / units.ly, digits) + " св. лет";
  if (units.au && a >= 0.01 * units.au) return num(x / units.au, digits) + " а.е.";
  if (a >= 1e3) return num(x / 1e3, digits) + " км";
  if (a >= 1) return num(x, digits) + " м";
  if (a >= 1e-3) return num(x * 1e3, digits) + " мм";
  if (a >= 1e-6) return num(x * 1e6, digits) + " мкм";
  if (a >= 1e-9) return num(x * 1e9, digits) + " нм";
  if (a === 0) return "0 м";
  return num(x * 1e12, digits) + " пм";
}

// A message in the corner (review LB1-p02-ux X8): one stack, the newest on top, at most TOAST_MAX; each stays at least
// `ms` and long enough to be read (about 70 ms a character), longer while the pointer is on it; a click closes it.
const TOAST_MAX = 6;
let toastBox = null;
export function toast(text, kind = "error", ms = 9000) {
  if (!toastBox || !toastBox.isConnected) { toastBox = el("div", { class: "toasts" }); document.body.append(toastBox); }
  const t = el("div", { class: "toast" + (kind === "notice" ? " notice" : "") }, el("span", { class: "tx", title: "Закрыть" }, "✕"), text);
  toastBox.append(t);
  while (toastBox.children.length > TOAST_MAX) toastBox.firstChild.remove();
  let timer = null;
  const arm = (d) => { clearTimeout(timer); timer = setTimeout(() => t.remove(), d); };
  t.addEventListener("click", () => { clearTimeout(timer); t.remove(); });
  t.addEventListener("mouseenter", () => clearTimeout(timer));
  t.addEventListener("mouseleave", () => arm(4000));
  arm(Math.max(ms, 70 * String(text).length));
  return t;
}

export function modal(content) {
  const m = el("div", { class: "modal" }, el("div", {}, content));
  m.addEventListener("click", (e) => { if (e.target === m) m.remove(); });
  document.addEventListener("keydown", function esc(e) { if (e.key === "Escape") { m.remove(); document.removeEventListener("keydown", esc); } });
  document.body.append(m);
  return m;
}

export function initTheme() {
  let th = null;
  try { th = localStorage.getItem("lfviz.theme"); } catch (e) { /* private mode */ }
  if (!th) th = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  document.documentElement.dataset.theme = th;
}
export function toggleTheme() {
  const th = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = th;
  try { localStorage.setItem("lfviz.theme", th); } catch (e) { /* ignore */ }
  window.dispatchEvent(new Event("themechange"));
}
export function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
// A 2-D context back in its default drawing state, scaled to the device pixels: called at the start of every frame. What
// one frame leaves behind (line width, dashes, alpha, alignment, font) would otherwise change the next one until the
// canvas is resized (which resets it), so the same moment would be drawn differently depending on how the cursor got
// there (found by the key frames' browser check).
export function fresh2d(g, dpr) {
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.globalAlpha = 1; g.globalCompositeOperation = "source-over"; g.filter = "none";
  g.lineWidth = 1; g.lineCap = "butt"; g.lineJoin = "miter"; g.miterLimit = 10; g.setLineDash([]); g.lineDashOffset = 0;
  g.font = "10px sans-serif"; g.textAlign = "start"; g.textBaseline = "alphabetic";
  g.fillStyle = "#000"; g.strokeStyle = "#000";
  g.shadowBlur = 0; g.shadowOffsetX = 0; g.shadowOffsetY = 0; g.shadowColor = "rgba(0, 0, 0, 0)";
  g.imageSmoothingEnabled = true;
  return g;
}

// --- controls that apply at once -----------------------------------------------------------------
// One control for a parameter (schema Param or an action argument spec). It commits a value by itself, without an
// "apply" button: a list or a checkbox on change, a number on Enter or when the field loses focus, a slider when it
// is released (while dragging only the number follows). Returns {el, set(v), pending(on), disable(on)}.
export function fmtInput(v) {
  if (typeof v !== "number" || !Number.isFinite(v)) return String(v ?? "");
  return String(Number(v.toPrecision(7)));
}

// A parameter as the forms name it, its allowed range, and why a typed value is refused — in the owner's words, as the
// server says it (lfviz.params; review UX-params P2: «lam_nm: 0.0 < min 300.0» for a field only cleared)
function pName(p) { const lab = p.label || p.id; return `«${p.unit && !lab.includes(p.unit) ? lab + ", " + p.unit : lab}»`; }
function fnum(x) { return num(x, 10); }
export function rangeText(p) {
  const lo = p.min, hi = p.max, has = (v) => v !== null && v !== undefined;
  return has(lo) && has(hi) ? `от ${fnum(lo)} до ${fnum(hi)}` : has(lo) ? `не меньше ${fnum(lo)}` : has(hi) ? `не больше ${fnum(hi)}` : "любое конечное число";
}
// why the text typed in a number field is not a value of p (null: it is), and the value
export function checkNumber(p, text) {
  const t = String(text ?? "").trim().replace(",", ".");
  if (t === "") return { err: `${pName(p)}: поле пустое — введите число ${rangeText(p)}` };
  const v = Number(t);
  if (!Number.isFinite(v)) return { err: `${pName(p)}: «${text}» — не число; нужно ${rangeText(p)}` };
  const x = p.type === "int" ? Math.round(v) : v;
  if (p.min !== null && p.min !== undefined && x < p.min) return { err: `${pName(p)}: ${fnum(x)} — меньше наименьшего ${fnum(p.min)}; можно ${rangeText(p)}` };
  if (p.max !== null && p.max !== undefined && x > p.max) return { err: `${pName(p)}: ${fnum(x)} — больше наибольшего ${fnum(p.max)}; можно ${rangeText(p)}` };
  return { value: x };
}
// options of a select shown for these values (an option may carry its own show_if: review UX-params P17)
export function optionShown(o, values) {
  return !o.show_if || Object.entries(o.show_if).every(([k, allowed]) => allowed.includes(values[k]));
}
// hide the options of a select that do not apply; when the value is hidden, the first shown option is chosen (select
// = true) and returned with a short note, else the note says why the value does not apply
function syncOptions(input, p, values, note, { select = true } = {}) {
  let first = null, curShown = false;
  for (const op of input.options) {
    const o = (p.options || []).find((x) => String(x.value) === op.value);
    const on = !o || optionShown(o, values);
    op.hidden = !on; op.disabled = !on;
    if (on && first === null) first = op.value;
    if (op.value === input.value && on) curShown = true;
  }
  if (curShown || first === null) { if (note) note.textContent = ""; return null; }
  const was = [...input.options].find((op) => op.value === input.value);
  const cond = Object.keys(((p.options || []).find((x) => String(x.value) === input.value) || {}).show_if || {}).join(", ");
  if (!select) { if (note) note.textContent = `«${was ? was.textContent : input.value}» здесь не действует${cond ? " (зависит от: " + cond + ")" : ""}`; return null; }
  input.value = first;
  if (note) note.textContent = `«${was ? was.textContent : ""}» здесь не подходит — выбрано «${input.selectedOptions[0].textContent}»`;
  return first;
}

export function control(p, value, onCommit, { compact = false, label = null } = {}) {
  const lab = label ?? p.label;
  const title = p.help || "";
  let input, slider = null, set;
  const num = p.type === "float" || p.type === "int";
  const lo = p.min, hi = p.max;
  const useLog = !!p.log && lo > 0;
  const canSlide = num && lo !== null && lo !== undefined && hi !== null && hi !== undefined && Number.isFinite(lo) && Number.isFinite(hi) && hi > lo;
  const toPos = (v) => useLog ? 1000 * (Math.log10(v) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo)) : 1000 * (v - lo) / (hi - lo);
  const fromPos = (x) => {
    let v = useLog ? 10 ** (Math.log10(lo) + x / 1000 * (Math.log10(hi) - Math.log10(lo))) : lo + x / 1000 * (hi - lo);
    if (p.type === "int") return Math.round(v);
    const q = 10 ** (Math.floor(Math.log10(Math.abs(v) || 1)) - 2);  // three significant digits from a slider
    return Math.round(v / q) * q;
  };
  if (p.type === "select") {
    input = el("select", { title }, (p.options || []).map((o) => el("option", { value: o.value }, o.label)));
    input.value = value;
    input.onchange = () => onCommit(input.value);
    set = (v) => { input.value = v; };
  } else if (p.type === "bool") {
    input = el("input", { type: "checkbox", title });
    input.checked = !!value;
    input.onchange = () => onCommit(input.checked);
    set = (v) => { input.checked = !!v; };
  } else {
    input = el("input", { type: "number", step: "any", title, class: compact ? "compact" : "" });
    input.value = fmtInput(value);
    if (lo !== null && lo !== undefined) input.min = lo;
    if (hi !== null && hi !== undefined) input.max = hi;
    input.onchange = () => {
      // refused here, in the owner's words, before anything is sent; the field goes back to the value in force (P2)
      const r = checkNumber(p, input.value);
      if (r.err) { input.value = fmtInput(value); showErr(r.err); return; }
      showErr("");
      onCommit(r.value);
    };
    input.onkeydown = (e) => { if (e.key === "Enter") input.blur(); };
    if (canSlide) {
      slider = el("input", { type: "range", min: 0, max: 1000, step: 1, title: title || lab });
      slider.value = toPos(Math.min(Math.max(value, lo), hi));
      slider.oninput = () => { input.value = fmtInput(fromPos(Number(slider.value))); };
      slider.onchange = () => onCommit(fromPos(Number(slider.value)));
    }
    set = (v) => { value = v; if (document.activeElement !== input) input.value = fmtInput(v); if (slider) slider.value = toPos(Math.min(Math.max(v, lo), hi)); };
  }
  // the slider follows its number field: out of the tab order, so that Tab goes from field to field (review UX-ui U10)
  if (slider) slider.tabIndex = -1;
  const note = el("div", { class: "ctl-err" });
  let errTimer = null;
  function showErr(text) {
    note.textContent = text || "";
    clearTimeout(errTimer);
    if (text) errTimer = setTimeout(() => { note.textContent = ""; }, 8000);
  }
  const box = compact
    ? el("label", { class: "qc", title }, el("span", { class: "muted" }, lab), slider, input, note)
    : el("div", { class: "ctl" + (slider ? " slide" : "") }, el("label", { title }, lab), input, slider, note);
  return {
    el: box,
    input,
    set(v) { set(v); },
    pending(on) { box.classList.toggle("pending", !!on); },
    disable(on) { for (const e of [input, slider]) if (e) e.disabled = !!on; },
    // the options that apply for these values (P17); a value in force that does not apply is only said here (a live
    // set-up is changed by the owner, not by the form)
    refreshOptions(values) { if (p.type === "select") syncOptions(input, p, values, note, { select: false }); },
    error: showErr,
  };
}

// --- parameter forms (schema from /api/viz) -------------------------------------------------------
// values: current values; onChange(id, value); readOnly: show values only; only(p): which parameters to show
export function paramForm(schema, values, { onChange, readOnly = false, only = null } = {}) {
  const box = el("div");
  const groups = new Map();
  const inputs = {};
  function shown(p) {
    if (!p.show_if) return true;
    return Object.entries(p.show_if).every(([k, allowed]) => allowed.includes(values[k]));
  }
  function refresh() {
    for (const p of schema.params) {
      if (!inputs[p.id]) continue;
      const row = inputs[p.id].row;
      row.style.display = shown(p) ? "" : "none";
      if (p.type === "select" && (p.options || []).some((o) => o.show_if)) {  // options for these values (P17)
        const nv = syncOptions(inputs[p.id].input, p, values, inputs[p.id].note);
        if (nv !== null) { values[p.id] = nv; onChange && onChange(p.id, nv); }
      }
      const std = row.querySelector(".std");
      if (std) std.textContent = p.standard !== null && p.standard !== undefined && !same(values[p.id], p.standard)
        ? "≠ стандарт" : "";
    }
    for (const [g, box] of groups) box.style.display = [...box.querySelectorAll(".field")].some((r) => r.style.display !== "none") ? "" : "none";
  }
  const params = schema.params.filter((p) => !p.hidden && (!only || only(p)));
  for (const p of params) {
    if (!groups.has(p.group)) {
      const gb = el("div", {}, el("div", { class: "help", style: { fontWeight: 600, marginTop: "8px" } }, p.group));
      groups.set(p.group, gb); box.append(gb);
    }
    let input;
    const v = values[p.id];
    if (p.type === "select") {
      input = el("select", { disabled: readOnly }, p.options.map((o) => el("option", { value: o.value, selected: o.value === v }, o.label)));
    } else if (p.type === "bool") {
      input = el("input", { type: "checkbox", disabled: readOnly });
      input.checked = !!v;
    } else {
      input = el("input", { type: "number", step: "any", value: v, disabled: readOnly });
      if (p.min !== null) input.min = p.min;
      if (p.max !== null) input.max = p.max;
    }
    input.title = p.help || "";
    const note = el("div", { class: "field-err" });
    input.addEventListener("change", () => {
      let x = p.type === "bool" ? input.checked : p.type === "select" ? input.value : null;
      if (x === null) {  // a number: checked here, in the owner's words (review UX-params P2)
        const r = checkNumber(p, input.value);
        if (r.err && input.value.trim() === "") {  // emptied: the value before stays, the field says what to type
          input.value = fmtInput(values[p.id]); note.textContent = r.err; row.classList.remove("bad"); return;
        }
        note.textContent = r.err || "";
        row.classList.toggle("bad", !!r.err);
        x = r.err ? input.value : r.value;  // kept as typed: the form's check (errors()) refuses to start with it
      } else { note.textContent = ""; row.classList.remove("bad"); }
      values[p.id] = x;
      onChange && onChange(p.id, x);
      refresh();
    });
    const row = el("div", { class: "field", "data-pid": p.id }, el("label", { title: p.help || "" }, p.label, el("span", { class: "std" })), input, note);
    inputs[p.id] = { row, input, note, p };
    groups.get(p.group).append(row);
  }
  refresh();
  function setValues(v) {
    Object.assign(values, v);
    for (const [id, { input }] of Object.entries(inputs)) {
      if (!(id in v)) continue;
      if (input.type === "checkbox") input.checked = !!v[id]; else input.value = input.tagName === "SELECT" ? v[id] : fmtInput(v[id]);
      inputs[id].row.classList.remove("bad"); inputs[id].note.textContent = "";
    }
    refresh();
  }
  // what the form would send that the schema refuses (a number out of range or not a number), by parameter
  function errors() {
    const out = {};
    for (const [id, { p, row }] of Object.entries(inputs)) {
      if (row.style.display === "none" || (p.type !== "float" && p.type !== "int")) continue;
      const r = checkNumber(p, values[id]);
      if (r.err) out[id] = r.err;
    }
    return out;
  }
  // refusals by parameter (the form's own, or the server's answer to a start: {pid: text}) shown at their fields
  function markErrors(fields) {
    for (const [id, { row, note }] of Object.entries(inputs)) {
      const t = (fields || {})[id];
      row.classList.toggle("bad", !!t);
      if (t) { note.textContent = t; if (row.style.display === "none") row.style.display = ""; }
      else if (row.classList.contains("bad")) note.textContent = "";
    }
  }
  return { el: box, values, refresh, setValues, errors, markErrors };
}

function same(a, b) {
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= 1e-12 * Math.abs(b);
  return a === b;
}
