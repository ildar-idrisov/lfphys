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
//                          a whole number without a format is shown exactly ("12 345 678", review i18n-code F3);
// fmtField(x), parseNum(s) a number in an editable field and the number typed into one: both decimal separators are
//                          read, an ambiguous text is refused (review i18n-browser F1, F2);
// lang(), setLang("ru")    the language in force and its change (stored in localStorage "lfviz.lang"; a change reloads
//                          the page). "?lang=ru" in the address overrides it for this tab: it is kept in sessionStorage
//                          and carried on the links to the other pages (review i18n-code F7, i18n-browser F4).
//
// The catalogue of the language in force (the engine's, the framework's and every world's locales/<lang>.json merged)
// is loaded before any module that imports this one runs (top-level await), so t() is usable everywhere, also at a
// module's top level. It is fetched from url("static/locales/<lang>.json") (base.js): the server answers there with the
// merged catalogue (as at /api/i18n/<lang>), and the public site carries the files written by
// `python -m lfviz.i18n --export` (review i18n-code F9). A catalogue that cannot be loaded leaves the
// English texts and marks the switch. Static texts of the HTML pages carry data-t (the element's text is its msgid) or
// data-t-title (its title attribute is); they are translated here, and every page's top bar gets the switch EN | RU.
//
// Records made before the translation (2026-11-12) hold Russian strings where new ones hold texts: legacy(x) loads,
// once and only when x holds such strings, the frozen map of the Russian strings of that time to their msgids
// (../legacy/ru-2026-11-12.json, from the catalogues of the translation's commit), and t() then shows such a string
// as its msgid in the language in force (review i18n-browser F3). Sentences formatted with numbers stay as recorded.

import { isPagePath, url } from "./base.js";

export const LANGS = [["en", "EN", "English"], ["ru", "RU", "Русский"]];  // each language by its own name, i18n-ok
const CODES = LANGS.map((l) => l[0]);
const KEY = "lfviz.lang";
const KEY_LINK = "lfviz.lang.link";  // the language a ?lang= link asked for, for this tab (sessionStorage)
const browser = typeof window !== "undefined" && typeof document !== "undefined";

let LANG = "en";
let CAT = {};
let PLURAL = new Map();
let NF = new Map();
let FAILED = false;  // the catalogue could not be loaded
let REV = null;  // Russian translation -> msgid, for records made before the translation (legacy)

// area: "localStorage" or "sessionStorage" (reading the property itself throws when storage is off)
function stored(area, key) {
  try { return globalThis[area].getItem(key); } catch (e) { return null; }  // private mode, storage off
}
function store(area, key, v) {
  try { if (v === null) globalThis[area].removeItem(key); else globalThis[area].setItem(key, v); } catch (e) { /* ignore */ }
}

// the language the page asks for: ?lang= wins (and is kept for this tab), then a language a link asked for earlier in
// this tab, then the stored choice, then English
export function chosenLang() {
  if (!browser) return "en";
  let q = null;
  try { q = new URLSearchParams(location.search).get("lang"); } catch (e) { /* no location */ }
  q = q ? q.toLowerCase().split(/[-_]/)[0] : q;
  if (q && CODES.includes(q)) { store("sessionStorage", KEY_LINK, q); return q; }
  const l = stored("sessionStorage", KEY_LINK);
  if (l && CODES.includes(l)) return l;
  const s = stored("localStorage", KEY);
  return s && CODES.includes(s) ? s : "en";
}

export function lang() { return LANG; }

// whether a link's language is in force (the address or this tab), not the stored choice
function linkLang() {
  if (!browser) return null;
  const l = stored("sessionStorage", KEY_LINK);
  return l && CODES.includes(l) && l === LANG ? l : null;
}

// an address of one of the pages, with the language a link asked for when one is in force (for navigation by code)
export function withLang(href) {
  const l = linkLang();
  if (!l) return href;
  try {
    const u = new URL(href, location.href);
    if (u.origin !== location.origin || !isPagePath(u.pathname) || u.searchParams.has("lang")) return href;
    u.searchParams.set("lang", l);
    return u.pathname + u.search + u.hash;
  } catch (e) { return href; }
}

// a link about to be followed (click, middle click, keyboard, "open in a new tab") takes the link's language along
function carry(ev) {
  const a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
  if (!a || a.hasAttribute("download") || !linkLang()) return;
  const h = a.getAttribute("href");
  if (!h || h.startsWith("#") || h.startsWith("blob:") || h.startsWith("data:")) return;
  const n = withLang(h);
  if (n !== h) a.setAttribute("href", n);
}

// a catalogue given directly (Node: the browser tests render the record's texts as the page does; a static copy of the
// player without the server)
export function setCatalogue(code, messages) {
  LANG = code; CAT = messages || {}; PLURAL = new Map(); NF = new Map(); REV = null;
}

const catalogueUrl = (code) => url(`static/locales/${code}.json`);

async function fetchCatalogue(code) {
  const r = await fetch(catalogueUrl(code));
  if (!r.ok) throw new Error(`${r.status}`);
  const j = await r.json();
  return j.messages || {};
}

let ready = null;
// loads the catalogue of the chosen language (once); English needs its overrides (plural forms)
export function init() {
  if (ready) return ready;
  ready = (async () => {
    LANG = chosenLang();
    PLURAL = new Map(); NF = new Map();
    if (!browser) return LANG;
    document.documentElement.lang = LANG;
    try { CAT = await fetchCatalogue(LANG); } catch (e) { CAT = {}; FAILED = LANG !== "en"; }
    translateDom(document);
    addSwitch();
    for (const k of ["pointerdown", "focusin", "auxclick", "contextmenu"]) document.addEventListener(k, carry, true);
    return LANG;
  })();
  return ready;
}

// a change of language: stored, the link's language and the address's override dropped, the page reloaded (every text
// is drawn anew)
export function setLang(code) {
  if (!CODES.includes(code)) return;
  store("localStorage", KEY, code); store("sessionStorage", KEY_LINK, null);
  if (!browser) { LANG = code; return; }
  const u = new URL(location.href);
  u.searchParams.delete("lang");
  if (u.href !== location.href) location.replace(u.href); else location.reload();
}

export function isT(x) { return x !== null && typeof x === "object" && typeof x.$t === "string"; }

// --- records made before the translation ------------------------------------------------------------------------------
const CYR = /[Ѐ-ӿ]/;  // i18n-ok: recognises the Russian strings of old records
// whether a structure holds a plain Russian string outside a text (T): a record made before 2026-11-12
export function isLegacy(x, depth = 0) {
  if (depth > 12 || x === null || x === undefined) return false;
  if (typeof x === "string") return CYR.test(x);
  if (isT(x)) return false;
  if (Array.isArray(x)) return x.some((v) => isLegacy(v, depth + 1));
  if (typeof x === "object") return Object.values(x).some((v) => isLegacy(v, depth + 1));
  return false;
}
// loads the frozen map once (in a language other than Russian) when x holds a record made before the translation;
// afterwards t() shows its Russian labels in the language in force. Returns whether x is such a record.
export async function legacy(x) {
  if (!isLegacy(x)) return false;
  if (LANG === "ru" || REV) return true;
  try {
    const r = await fetch(url("static/legacy/ru-2026-11-12.json"));
    REV = new Map(Object.entries(r.ok ? (await r.json()).messages || {} : {}));
  } catch (e) { REV = new Map(); }
  return true;
}
// a plain string as shown: a Russian label of an old record in the language in force (when legacy() loaded the map),
// any other string as it is (el() and fill() pass their plain strings through it)
export function relabel(s) {
  if (!REV || typeof s !== "string") return s;
  const id = REV.get(s);
  return id === undefined ? s : lookup(id, null);
}
// the map given directly (Node tests): msgid -> the Russian string of that time
export function setLegacy(ruMessages) {
  REV = new Map();
  for (const [k, v] of Object.entries(ruMessages || {})) if (typeof v === "string" && !REV.has(v)) REV.set(v, k);
}

// --- rendering ---------------------------------------------------------------------------------------------------------
function pluralRules(fraction) {
  const key = fraction || 0;
  let p = PLURAL.get(key);
  if (!p) {
    const o = fraction ? { minimumFractionDigits: fraction } : {};
    try { p = new Intl.PluralRules(LANG, o); } catch (e) { p = new Intl.PluralRules("en", o); }
    PLURAL.set(key, p);
  }
  return p;
}

const SPEC = /^(\+)?(?:\.(\d+))?([gfed%])?$/;
// the plural category of n as the placeholder shows it: {n:d} of 4.6 shows 5, {n:.2f} shows decimals (review i18n-code
// F11); a missing or non-finite n is "other"
function category(n, spec) {
  if (typeof n !== "number" || !Number.isFinite(n)) return "other";
  const m = SPEC.exec(spec || "");
  if (!m) return pluralRules(0).select(n);
  const prec = m[2] !== undefined ? Number(m[2]) : null, kind = m[3] || "g";
  if (kind === "d") return pluralRules(0).select(Math.round(Math.abs(n)));
  if (kind === "f") { const p = prec ?? 6; return pluralRules(p).select(Number(Math.abs(n).toFixed(p))); }
  if (kind === "e" || kind === "%") return "other";
  if (!spec && Number.isInteger(n)) return pluralRules(0).select(Math.abs(n));
  return pluralRules(0).select(Number(Math.abs(n).toPrecision(Math.min(Math.max(prec ?? 6, 1), 15))));
}

const NSPEC = /\{n(?::([^{}]*))?\}/;
function lookup(msgid, args) {
  const own = (k) => Object.prototype.hasOwnProperty.call(CAT, k) ? CAT[k] : undefined;
  let e = own(msgid);
  if ((e === undefined || e === null || e === "") && REV && !args && REV.has(msgid)) {  // a Russian label of an old record
    const id = REV.get(msgid);
    e = own(id);
    if (e === undefined || e === null || e === "") return id;
  }
  if (e === undefined || e === null || e === "") return msgid;
  if (typeof e === "string") return e;
  if (typeof e === "object") {  // plural forms (CLDR categories) chosen by the argument n as it is shown
    const m = NSPEC.exec(msgid);
    const n = args && Object.prototype.hasOwnProperty.call(args, "n") ? Number(args.n) : NaN;
    return e[category(n, m ? m[1] : "")] ?? e.other ?? msgid;
  }
  return msgid;
}

const PH = /\{(\w+)(?::([^{}]*))?\}(\.?)/g;
const END = /[.!?…]$/;

function render(template, args) {
  return template.replace(PH, (whole, name, spec, dot) => {
    if (!args || !Object.prototype.hasOwnProperty.call(args, name)) return whole;  // not the prototype's (F10)
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
  if (LANG === "ru") s = s.replace(/[\u00a0\u202f]/g, "\u202f");  // Intl's spaces: a narrow no-break space
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

// A number in the viewer's language. spec: "" (a whole number exactly, any other number with 6 significant digits),
// ".3g", ".2f", ".2e", "d", each optionally with "+" first (a sign also on positive numbers). Scientific form m·10ⁿ for
// |x| ≥ 10⁷ or < 10⁻⁴ (g) and always for e; the minus sign is "−" in every language.
export function fmt(x, spec = "") {
  if (x === null || x === undefined || (typeof x === "number" && Number.isNaN(x))) return "—";
  if (typeof x === "boolean") return String(x);
  if (typeof x !== "number") { const y = Number(x); if (Number.isNaN(y)) return String(x); x = y; }
  const m = SPEC.exec(spec || "") || [];
  const plus = !!m[1], prec = m[2] !== undefined ? Number(m[2]) : null, kind = m[3] || "g";
  const sign = x < 0 ? MINUS : plus ? "+" : "";
  const a = Math.abs(x);
  if (!Number.isFinite(x)) return (x < 0 ? MINUS : plus ? "+" : "") + "∞";
  let body;
  if (kind === "d" || (!spec && Number.isInteger(a) && a < 2 ** 53)) body = local(Math.round(a), { maximumFractionDigits: 0 });
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

// A number in an editable field, in the viewer's language (review i18n-browser F2): its decimal separator and the
// minus sign −, 7 significant digits, m·10ⁿ as fmt; thousands grouped only where the group separator cannot be read as
// a decimal one (ru: a narrow space; en: none, since a comma is read as a decimal comma too). int: a whole number. A
// value that is not a finite number (a text typed and refused) is shown as it is.
export function fmtField(v, int = false) {
  if (typeof v !== "number" || !Number.isFinite(v)) return v === null || v === undefined || Number.isNaN(v) ? "" : String(v);
  const sign = v < 0 ? MINUS : "", a = Math.abs(v), g = LANG === "ru";
  if (int || (Number.isInteger(a) && a < 1e15)) return sign + local(Math.round(a), { maximumFractionDigits: 0, useGrouping: g });
  if (a !== 0 && (a >= 1e7 || a < 1e-4)) return sign + sci(a, 7);
  return sign + local(Number(a.toPrecision(7)), { maximumSignificantDigits: 7, useGrouping: g });
}

const SPACES = /[\s\u00a0\u202f\u2009]/g;
const SUPS = "⁰¹²³⁴⁵⁶⁷⁸⁹";
// A number typed by the viewer (review i18n-browser F1: a field of type=number dropped a decimal comma, 650,5 became
// 6505). Read: a decimal comma or point; thousands separated by spaces (also the narrow ones fmt writes), by commas or
// points in groups of three (1,234,567; 1.234,5; 1,234.5); the signs + - − ; exponents 1e-5, 1,5·10⁻⁵, 1.5×10^-5.
// Returns {value} or {err: "empty" | "nan" | "ambiguous", a, b}: "ambiguous" is a single comma before exactly three
// digits in English ("1,500"), which may be a thousands separator (a = "1500") or a decimal comma (b = "1.500").
export function parseNum(text) {
  let s = String(text ?? "").trim();
  if (s === "") return { err: "empty" };
  s = s.replace(/[−‒–]/g, "-");
  let sign = 1;
  if (s[0] === "-" || s[0] === "+") { if (s[0] === "-") sign = -1; s = s.slice(1).trim(); }
  let exp = 0, m;
  if ((m = /^(.*\d[.,]?)\s*[eE]\s*([+-]?\d+)$/.exec(s))) { s = m[1]; exp = Number(m[2]); }
  else if ((m = /^(?:(.*?)\s*[·×xX*⋅]\s*)?10\s*(?:\^\s*\(?\s*([+-]?\d+)\s*\)?|([⁺⁻]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+))$/.exec(s))) {
    exp = m[2] !== undefined ? Number(m[2])
      : Number(m[3].replace("⁺", "").replace("⁻", "-").replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]/g, (d) => String(SUPS.indexOf(d))));
    s = m[1] === undefined ? "1" : m[1];
  }
  if (!/^[\d.,\s\u00a0\u202f\u2009]*$/.test(s) || !/\d/.test(s)) return { err: "nan" };
  const commas = (s.match(/,/g) || []).length, points = (s.match(/\./g) || []).length;
  let dec = null, grp = "";
  if (commas && points) {
    dec = s.lastIndexOf(",") > s.lastIndexOf(".") ? "," : ".";
    grp = dec === "," ? "." : ",";
    if ((dec === "," ? commas : points) > 1) return { err: "nan" };
  } else if (commas + points === 1) dec = commas ? "," : ".";
  else if (commas + points > 1) grp = commas ? "," : ".";
  let int = s, frac = "";
  if (dec) { const i = s.lastIndexOf(dec); int = s.slice(0, i); frac = s.slice(i + 1); }
  if (/\D/.test(frac.trim()) || /\s/.test(frac.trim())) return { err: "nan" };
  frac = frac.trim();
  const parts = int.trim().split(grp ? new RegExp(`[\\s\\u00a0\\u202f\\u2009${grp === "." ? "\\." : ","}]`) : SPACES);
  if (parts.length > 1 && !(/^\d{1,3}$/.test(parts[0]) && parts.slice(1).every((p) => /^\d{3}$/.test(p)))) return { err: "nan" };
  if (parts.some((p) => /\D/.test(p))) return { err: "nan" };
  const whole = parts.join("");
  if (dec === "," && LANG === "en" && commas === 1 && !points && parts.length === 1 && frac.length === 3 && /^[1-9]\d{0,2}$/.test(whole) && !exp) {
    const sg = sign < 0 ? "-" : "";
    return { err: "ambiguous", a: `${sg}${whole}${frac}`, b: `${sg}${whole}.${frac}` };
  }
  const digits = (whole || "0") + (frac ? "." + frac : "");
  const value = sign * Number(`${digits}e${exp}`);
  return Number.isFinite(value) ? { value } : { err: "nan" };
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

// the switch EN | RU: an element for a page's top bar (added to the first .topbar by init, before the theme button);
// marked when the catalogue of the language in force could not be loaded (the texts are then English)
export function langSwitch() {
  const box = document.createElement("span");
  box.className = "lang-switch" + (FAILED ? " failed" : "");
  box.title = FAILED ? t("The translation could not be loaded: the interface is in English") : t("Interface language");
  LANGS.forEach(([code, short, name], i) => {
    if (i) box.append(document.createTextNode(" | "));
    const b = document.createElement("a");
    b.href = "#";
    b.textContent = short + (FAILED && code === LANG ? " ⚠" : "");
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
