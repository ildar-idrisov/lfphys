// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The interface's languages (owner, 2026-11-12: «для всего фронта сделай i18n переводы на русский и английский, по
// дефолту английский и переключением языка»; AGENTS.md §3 rule 13, LANGUAGES.md, RULES.md «Languages and i18n»).
//
//   import { t, fmt, lang } from "/static/js/i18n.js";
//
// t("Run")                 a static text of the interface: its English msgid, looked up in the catalogue;
// t({"$t": msgid, "a": {}}) a text the server sent (lfphys.i18n.T), rendered in the viewer's language; its arguments
//                          are numbers (formatted by fmt with the placeholder's format), texts (T objects, rendered in
//                          turn) or plain strings (as they are); {x:cap} capitalises a text, {x:unit} keeps only the
//                          unit a label carries after its last comma;
// t(msgid, {x: 1})         a static msgid with arguments;
// fmt(x, ".3g")            a number in the viewer's language (ru: decimal comma, narrow-space thousands; en: point);
// lang(), setLang("ru")    the language in force and its change (stored in localStorage "lfviz.lang"; "?lang=ru" in
//                          the address overrides it; a change reloads the page).
//
// The catalogue of the language in force (GET /api/i18n/<lang>: the engine's, the framework's and every world's
// locales/<lang>.json merged) is loaded before any module that imports this one runs (top-level await), so t() is
// usable everywhere, also at a module's top level. Static texts of the HTML pages carry data-t (the element's text is
// its msgid) or data-t-title (its title attribute is); they are translated here, and every page's top bar gets the
// language switch EN | RU.

export const LANGS = [["en", "EN", "English"], ["ru", "RU", "Русский"]];  // each language by its own name, i18n-ok
const CODES = LANGS.map((l) => l[0]);
const KEY = "lfviz.lang";
const browser = typeof window !== "undefined" && typeof document !== "undefined";

let LANG = "en";
let CAT = {};
let PLURAL = null;
let NF = new Map();

function storedLang() {
  try { return localStorage.getItem(KEY); } catch (e) { return null; }  // private mode
}

// the language the page asks for: ?lang= wins, then the stored choice, then English
export function chosenLang() {
  if (!browser) return "en";
  let q = null;
  try { q = new URLSearchParams(location.search).get("lang"); } catch (e) { /* no location */ }
  if (q && CODES.includes(q)) return q;
  const s = storedLang();
  return s && CODES.includes(s) ? s : "en";
}

export function lang() { return LANG; }

// a catalogue given directly (Node: the browser tests render the record's texts as the page does; a static copy of the
// player without the server)
export function setCatalogue(code, messages) {
  LANG = code; CAT = messages || {}; PLURAL = null; NF = new Map();
}

let ready = null;
// loads the catalogue of the chosen language (once); English needs only its overrides (plural forms)
export function init() {
  if (ready) return ready;
  ready = (async () => {
    LANG = chosenLang();
    PLURAL = null; NF = new Map();
    if (!browser) return LANG;
    document.documentElement.lang = LANG;
    try {
      const r = await fetch(`/api/i18n/${LANG}`);
      if (r.ok) { const j = await r.json(); CAT = j.messages || {}; }
    } catch (e) { CAT = {}; }  // no server (a static copy): the English source texts
    translateDom(document);
    addSwitch();
    return LANG;
  })();
  return ready;
}

// a change of language: stored, the address's override dropped, the page reloaded (every text is drawn anew)
export function setLang(code) {
  if (!CODES.includes(code)) return;
  try { localStorage.setItem(KEY, code); } catch (e) { /* ignore */ }
  if (!browser) { LANG = code; return; }
  const u = new URL(location.href);
  u.searchParams.delete("lang");
  if (u.href !== location.href) location.replace(u.href); else location.reload();
}

export function isT(x) { return x !== null && typeof x === "object" && typeof x.$t === "string"; }

function pluralRules() {
  if (!PLURAL) { try { PLURAL = new Intl.PluralRules(LANG); } catch (e) { PLURAL = new Intl.PluralRules("en"); } }
  return PLURAL;
}

function lookup(msgid, args) {
  const e = Object.prototype.hasOwnProperty.call(CAT, msgid) ? CAT[msgid] : undefined;
  if (e === undefined || e === null || e === "") return msgid;
  if (typeof e === "string") return e;
  if (typeof e === "object") {  // plural forms (CLDR categories) chosen by the argument n
    const n = Number(args && args.n);
    const cat = Number.isFinite(n) ? pluralRules().select(n) : "other";
    return e[cat] ?? e.other ?? msgid;
  }
  return msgid;
}

const PH = /\{(\w+)(?::([^{}]*))?\}(\.?)/g;
const END = /[.!?…]$/;

function render(template, args) {
  return template.replace(PH, (whole, name, spec, dot) => {
    if (!args || !(name in args)) return whole;
    let s = arg(args[name], spec);
    if (spec === "cap") s = s.charAt(0).toUpperCase() + s.slice(1);
    return s + (dot && END.test(s) ? "" : dot);  // no doubled period after a text that ends a sentence
  });
}

const UNIT = /,\s*([^,(]+?)\s*(\(|$)/;
function arg(v, spec) {
  if (spec === "unit") { const m = UNIT.exec(arg(v, "")); return m ? m[1] : ""; }  // "Mass, M☉" -> "M☉"
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return fmt(v, spec === "cap" || spec === "unit" ? "" : spec);
  if (isT(v)) return t(v);
  if (Array.isArray(v)) return v.map((x) => arg(x, spec)).join(", ");
  return String(v);
}

// A text in the viewer's language. x: a msgid (plain string), a T object {"$t", "a"} from the server, a number, or
// nothing (""); args: the arguments of a plain msgid. A string that is not in the catalogue passes unchanged.
export function t(x, args) {
  if (x === null || x === undefined) return "";
  if (typeof x === "string") return args ? render(lookup(x, args), args) : lookup(x, null);
  if (typeof x === "number") return fmt(x);
  if (isT(x)) { const a = x.a || {}; return render(lookup(x.$t, a), a); }
  if (Array.isArray(x)) return x.map((y) => t(y)).join(", ");
  return String(x);
}

// --- numbers -----------------------------------------------------------------------------------------------------
const SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹";
function sup(n) { return String(n).replace("-", "⁻").replace(/\d/g, (d) => SUP[d]); }
const MINUS = "−";

function nf(opts) {
  const key = JSON.stringify(opts);
  let f = NF.get(key);
  if (!f) { f = new Intl.NumberFormat(LANG === "ru" ? "ru-RU" : "en-US", opts); NF.set(key, f); }
  return f;
}
// a non-negative number with the language's separators (ru: decimal comma, narrow no-break space between thousands)
function local(a, opts) {
  let s = nf({ useGrouping: true, ...opts }).format(a);
  if (LANG === "ru") s = s.replace(/[  ]/g, " ");
  return s;
}
function sci(a, digits, fixedDecimals) {
  let e = Math.floor(Math.log10(a));
  let m = a / 10 ** e;
  const mr = fixedDecimals !== undefined ? Number(m.toFixed(fixedDecimals)) : Number(m.toPrecision(digits));
  if (mr >= 10) { m = mr / 10; e += 1; } else m = mr;
  const ms = fixedDecimals !== undefined
    ? local(m, { minimumFractionDigits: fixedDecimals, maximumFractionDigits: fixedDecimals, useGrouping: false })
    : local(Number(m.toPrecision(digits)), { maximumSignificantDigits: digits, useGrouping: false });
  return `${ms}·10${sup(e)}`;
}

// A number in the viewer's language. spec: "" (6 significant digits), ".3g", ".2f", ".2e", "d", each optionally with
// "+" first (a sign also on positive numbers). Scientific form m·10ⁿ for |x| ≥ 10⁷ or < 10⁻⁴ (g) and always for e; the
// minus sign is "−" in every language.
export function fmt(x, spec = "") {
  if (x === null || x === undefined || (typeof x === "number" && Number.isNaN(x))) return "—";
  if (typeof x !== "number") { const y = Number(x); if (Number.isNaN(y)) return String(x); x = y; }
  const m = /^(\+)?(?:\.(\d+))?([gfed%])?$/.exec(spec || "") || [];
  const plus = !!m[1], prec = m[2] !== undefined ? Number(m[2]) : null, kind = m[3] || "g";
  const sign = x < 0 ? MINUS : plus ? "+" : "";
  const a = Math.abs(x);
  if (!Number.isFinite(x)) return (x < 0 ? MINUS : plus ? "+" : "") + "∞";
  let body;
  if (kind === "d") body = local(Math.round(a), { maximumFractionDigits: 0 });
  else if (kind === "f") { const p = prec ?? 6; body = local(Number(a.toFixed(p)), { minimumFractionDigits: p, maximumFractionDigits: p }); }
  else if (kind === "%") { const p = prec ?? 0; body = local(Number((a * 100).toFixed(p)), { minimumFractionDigits: p, maximumFractionDigits: p }) + " %"; }
  else if (kind === "e") body = a === 0 ? local(0, { minimumFractionDigits: prec ?? 6, maximumFractionDigits: prec ?? 6 }) : sci(a, 7, prec ?? 6);
  else {
    const d = Math.min(Math.max(prec ?? 6, 1), 15);
    if (a !== 0 && (a >= 1e7 || a < 1e-4)) body = sci(a, d);
    else body = local(Number(a.toPrecision(d)), { maximumSignificantDigits: d });
  }
  return sign + body;
}

// --- the HTML pages ------------------------------------------------------------------------------------------------
// [data-t]: the element's text is its msgid; [data-t-title]: its title is; [data-t-placeholder]: its placeholder is
export function translateDom(root) {
  if (!root || !root.querySelectorAll) return;
  for (const e of root.querySelectorAll("[data-t]")) {
    const id = e.dataset.tId || e.textContent.replace(/\s+/g, " ").trim();
    e.dataset.tId = id;
    e.textContent = t(id);
  }
  for (const e of root.querySelectorAll("[data-t-title]")) {
    const id = e.dataset.tTitleId || e.getAttribute("title") || "";
    e.dataset.tTitleId = id;
    if (id) e.setAttribute("title", t(id));
  }
  for (const e of root.querySelectorAll("[data-t-placeholder]")) {
    const id = e.dataset.tPhId || e.getAttribute("placeholder") || "";
    e.dataset.tPhId = id;
    if (id) e.setAttribute("placeholder", t(id));
  }
}

// the switch EN | RU: an element for a page's top bar (added to the first .topbar by init, before the theme button)
export function langSwitch() {
  const box = document.createElement("span");
  box.className = "lang-switch";
  box.title = t("Interface language");
  LANGS.forEach(([code, short, name], i) => {
    if (i) box.append(document.createTextNode(" | "));
    const b = document.createElement("a");
    b.href = "#";
    b.textContent = short;
    b.title = name;
    b.dataset.lang = code;
    if (code === LANG) { b.className = "on"; b.setAttribute("aria-current", "true"); }
    b.addEventListener("click", (ev) => { ev.preventDefault(); if (code !== LANG) setLang(code); });
    box.append(b);
  });
  return box;
}

function addSwitch() {
  const bar = document.querySelector(".topbar");
  if (!bar || bar.querySelector(".lang-switch")) return;
  const sw = langSwitch();
  const before = bar.querySelector("#theme");
  if (before) bar.insertBefore(sw, before); else bar.append(sw);
}

if (browser) await init();
