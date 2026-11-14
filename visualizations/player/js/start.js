// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The start page (DESIGN of the start page §1, 2026-11-13; replaces the catalogue of catalog.js): learning materials in
// physics by audience — school, university, research and the laboratories (owner, 2026-11-13). One page with hash routes,
// the same file on the server and on the public site (<meta name="lf-mode">, js/base.js):
//
//   #                 the four audiences with their counts; «Continue» (server: the last runs open or paused)
//   #school           the school course: what is ready, and until AB1 the planned demonstrations, honestly (§2.2)
//   #university       the demonstrations of the university courses, by section in teaching order
//   #research         the research set-ups: each with its question, «Status: hypothesis» and its prior art
//   #labs             the laboratories (free benches): live on a server only; greyed on the site (old: #playground)
//   #<audience>/<id>  the same page with that card in view
//
// The lower the level, the simpler the card (rule 16): a school card has no parameters, seed or devices; a university
// card folds them under «▸ More»; a research card shows them open. On the server a card offers «▶ Compute live» and,
// when the scenario has one, «▷ Recording m:ss»; on the site it offers only the recordings. The runs are listed on
// /runs, not here.
import { MODE, apiGet, getJSON, page, url } from "./api.js";
import { lang, t, withLang } from "./i18n.js";
import { el, fill, initTheme, modal, paramForm, toast, toggleTheme } from "./ui.js";

const GITHUB = "https://github.com/ildar-idrisov/lfphys";
const SERVER = MODE === "server";
// the README's quick start in the viewer's language (how to run lfphys locally)
const quickStart = () => (lang() === "ru" ? `${GITHUB}/blob/main/README.ru.md#%D0%B1%D1%8B%D1%81%D1%82%D1%80%D1%8B%D0%B9-%D1%81%D1%82%D0%B0%D1%80%D1%82`
  : `${GITHUB}#quick-start`);

// the audiences and the sections in their order, with their texts (T): registry.AUDIENCES and registry.SECTIONS, read
// from apiGet("audiences") (the server's /api/audiences, the site's api/audiences.json); the laboratories' route is #labs
const HASH = { playground: "labs" };
const AUDS = () => D.audiences.map((a) => ({ id: a.id, hash: HASH[a.id] || a.id, label: t(a.label), text: t(a.description), picture: a.picture || null }));
const SECTIONS = () => D.sections.map((s) => [s.id, t(s.label)]);
const audOf = (id) => AUDS().find((a) => a.id === id) || null;
const audByHash = (h) => AUDS().find((a) => a.hash === h) || null;
const secLabel = (id) => (SECTIONS().find((s) => s[0] === id) || [id, id])[1];
const secOrder = (id) => { const i = SECTIONS().findIndex((s) => s[0] === id); return i < 0 ? 99 : i; };

// what the page shows: the catalogue, the planned items, the recordings (local or the site's), the runs (server)
const D = { viz: [], planned: [], audiences: [], sections: [], rec: { worlds: {}, site: "", published: false }, siteRec: null, runs: null, health: null, loaded: false };
const R = { aud: null, focus: null, section: "all", q: "", by: "section" };  // the route and the filters
let kernelInfo = null;  // the engine's kernels (from /api/devices), for a run's own choice of devices

initTheme();
document.getElementById("theme").onclick = toggleTheme;
document.getElementById("help").onclick = showHelp;
document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;
  if (e.code === "KeyT" || e.key === "t" || e.key === "T") toggleTheme();  // by the key's place: any keyboard layout
  if (e.key === "?") showHelp();
});
if (!SERVER) {  // the site: what it is, and the source
  const bar = document.querySelector(".topbar");
  const after = bar.querySelector(".grow").nextSibling;
  bar.insertBefore(el("span", { class: "muted", title: t("This site plays recordings of real runs; computing live needs lfphys on your computer") }, t("Recordings")), after);
  bar.insertBefore(el("a", { href: GITHUB, title: t("The source code and the documentation") }, "GitHub"), after);
}

// --- the data -------------------------------------------------------------------------------------------------------
async function load() {
  const [viz, planned, rec, auds] = await Promise.allSettled([apiGet("viz"), apiGet("planned"), apiGet("recordings"), apiGet("audiences")]);
  if (viz.status !== "fulfilled") throw viz.reason;
  if (auds.status !== "fulfilled") throw auds.reason;
  D.viz = viz.value;
  D.audiences = auds.value.audiences || [];
  D.sections = auds.value.sections || [];
  D.planned = planned.status === "fulfilled" && Array.isArray(planned.value) ? planned.value : [];
  D.rec = rec.status === "fulfilled" && rec.value ? { worlds: rec.value.worlds || {}, site: rec.value.site || "", published: rec.value.published === true }
    : { worlds: {}, site: "", published: false };
  // a server without a local recording of a world plays the public site's, only when the site is published and its
  // recording was made from the same version of the world (integrator D4): its index is read once, here
  if (SERVER && D.rec.published && D.rec.site) {
    try { const r = await fetch(`${D.rec.site}api/recordings.json`); D.siteRec = r.ok ? await r.json() : null; } catch (e) { D.siteRec = null; }
  }
  D.loaded = true;
}
const worlds = (aud) => D.viz.filter((v) => !v.error && v.audience === aud);
const plannedOf = (aud) => D.planned.filter((p) => p.audience === aud);
// a world's recordings: its specs (describe().recordings) with the index entry where one was recorded: here, or (server)
// on the published site from the same version of the world (fromSite); on the site only those recorded
function recsOf(v) {
  const idx = (D.rec.worlds || {})[v.id];
  const have = new Map(((idx && idx.recordings) || []).map((r) => [r.id, r]));
  const sidx = SERVER && D.siteRec && D.siteRec.worlds ? D.siteRec.worlds[v.id] : null;
  const remote = new Map(((sidx && sidx.recordings) || []).filter((r) => String(r.version ?? sidx.version) === String(v.version)).map((r) => [r.id, r]));
  const out = (v.recordings || []).map((s) => {
    const local = have.get(s.id) || null, site = local ? null : remote.get(s.id) || null;
    return { ...s, entry: local || site, fromSite: !!site };
  });
  return SERVER ? out : out.filter((r) => r.entry);
}
const mss = (s) => { s = Math.round(Number(s) || 0); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };
const recHref = (v, r) => withLang(page("run", { rec: `${v.id}/${r.id}` }));

// --- routes ---------------------------------------------------------------------------------------------------------
function parseHash() {
  let h = location.hash.replace(/^#/, "");
  try { h = decodeURIComponent(h); } catch (e) { /* a malformed escape (review P17-start-page F13): the hash as it is */ }
  if (h === "playground" || h.startsWith("playground/")) {  // the old name of the laboratories
    h = "labs" + h.slice("playground".length);
    history.replaceState(null, "", "#" + h);
  }
  const [a, focus] = h.split("/");
  const aud = audByHash(a);
  if ((aud ? aud.id : null) !== R.aud) { R.section = "all"; R.q = ""; }
  R.aud = aud ? aud.id : null;
  R.focus = focus || null;
  if (R.focus) { R.section = "all"; R.q = ""; }
}
window.addEventListener("hashchange", () => { parseHash(); render(); });

function render() {
  const box = document.getElementById("start");
  if (!D.loaded) return;
  if (!R.aud) fill(box, home());
  else if (R.aud === "playground") fill(box, labsPage());
  else fill(box, audiencePage(R.aud));
  document.title = R.aud ? `${audOf(R.aud).label} · lfphys` : t("lfphys · physics computed, not drawn");
  if (R.focus) {
    const c = document.getElementById("card-" + R.focus);
    if (c) { c.classList.add("focus"); c.scrollIntoView({ block: "center" }); }
  } else window.scrollTo(0, 0);
}

// --- the home: the four audiences ------------------------------------------------------------------------------------
function home() {
  const errs = D.viz.filter((v) => v.error);
  return [
    el("p", { class: "st-intro" }, t("Learning materials in physics. Every picture is computed by the run from the laws, and each run checks itself against the accepted formulas. Start at your level.")),
    SERVER ? null : siteNote(),
    el("div", { class: "st-tiles" }, AUDS().map(tile)),
    SERVER ? el("div", { id: "continue", class: "st-continue" }) : null,
    errs.length ? el("div", { class: "st-note warn" }, el("b", {}, t("Not loaded:")), " ",
      errs.map((v) => el("div", {}, el("span", { class: "mono" }, v.id), " — ", t(v.error)))) : null,
    footer(),
  ];
}
function siteNote() {
  return el("div", { class: "st-note" }, t("These are recordings of real runs: you can play them, go back and look at the checks. To compute live, change the set-up or use the laboratories, run lfphys on your computer (Docker)."),
    " ", el("a", { href: quickStart(), target: "_blank", rel: "noopener" }, t("How to run it →")));
}
function tile(a) {
  const W = worlds(a.id), P = plannedOf(a.id);
  // the audience's own picture (registry.AUDIENCES "picture"; review P17-start-page F10), else the first world with one
  const pic = W.find((v) => v.id === a.picture && v.picture) || W.find((v) => v.picture);
  const nRec = W.reduce((n, v) => n + recsOf(v).filter((r) => r.entry).length, 0);
  const off = a.id === "playground" && !SERVER;
  let lines;
  if (a.id === "school") {
    const next = P.filter((p) => p.state === "next").length;
    lines = W.length ? [t("{n:d} demonstrations", { n: W.length }), P.length ? t("{n:d} more planned", { n: P.length }) : null]
      : [t("In preparation: {next:d} next, {n:d} planned", { next, n: P.length })];
  } else if (a.id === "university") lines = [t("{n:d} demonstrations", { n: W.length }), SERVER ? null : t("{n:d} recordings", { n: nRec })];
  else if (a.id === "research") lines = [t("{n:d} research set-ups", { n: W.length }), SERVER ? t("hypotheses, marked as such") : t("{n:d} recordings", { n: nRec })];
  else lines = [t("{n:d} benches", { n: W.length }), off ? null : t("computed live")];
  return el("a", { class: `st-tile aud-${a.hash}` + (off ? " off" : ""), href: "#" + a.hash, id: "tile-" + a.hash },
    // a picture of one of its demonstrations, or the audience's colour (the tiles stay alike while pictures are missing)
    pic ? el("img", { class: "pic", src: url(`images/${pic.id}.jpg`), alt: "", loading: "lazy" }) : el("div", { class: "pic ph", "aria-hidden": "true" }),
    el("div", { class: "name" }, a.label),
    el("div", { class: "text" }, a.text),
    el("div", { class: "count" }, lines.filter(Boolean).map((s) => el("div", {}, s))),
    off ? el("div", { class: "warn" }, t("Works only with a running server")) : null,
    el("div", { class: "open" }, t("Open →")));
}
function footer() {
  return el("p", { class: "muted st-foot" },
    el("a", { href: "#", onclick: (e) => { e.preventDefault(); showHelp(); } }, t("How it works")), " · ",
    el("a", { href: withLang(page("legal")) }, t("Licence and citation")), " · ",
    el("a", { href: GITHUB, target: "_blank", rel: "noopener" }, t("Source (GitHub)")),
    el("br"),
    t("A research tool: the models and the results may contain errors, there is no warranty — check the results yourself. Noncommercial research, study and teaching only; if the software computed or checked what your publication reports, citing lfphys with its version is required."),
    el("br"),
    t("Credit for public use: {line}. The recordings, posters, atlases and worksheets: © 2026 Ildar Idrisov, CC BY-NC-SA 4.0 ({cc}), provided as is, without warranty.", { line: "lfphys — Ildar Idrisov — https://ildar-idrisov.github.io/lfphys/", cc: "https://creativecommons.org/licenses/by-nc-sa/4.0/" }));
}

// --- an audience's page -----------------------------------------------------------------------------------------------
function header(a) {
  return el("div", { class: "st-head" },
    el("a", { href: "#", class: "st-back" }, t("‹ All audiences")),
    el("h1", {}, el("span", { class: `st-aud aud-${a.hash}` }, a.label), el("span", { class: "st-sub" }, a.text)));
}
// the section chips with their counts, the search box; groups: [[key, label, items]]
function filters(groups, extra) {
  const all = groups.reduce((n, g) => n + g[2].length, 0);
  const chip = (key, label, n) => el("button", { class: "chip" + (R.section === key ? " on" : ""), "aria-pressed": String(R.section === key),
    onclick: () => { R.section = key; render(); } }, `${label} ${n}`);
  const search = el("input", { type: "search", class: "st-search", placeholder: t("Search…"), value: R.q, "aria-label": t("Search") });
  search.addEventListener("input", () => {
    R.q = search.value;
    const pos = search.selectionStart;
    render();
    const s2 = document.querySelector(".st-search");
    if (s2) { s2.focus(); try { s2.setSelectionRange(pos, pos); } catch (e) { /* not a text field */ } }
  });
  return el("div", { class: "st-filters" },
    el("div", { class: "st-chips" }, chip("all", t("All"), all), groups.filter((g) => g[2].length).map((g) => chip(g[0], g[1], g[2].length))),
    extra || null, search);
}
const matches = (texts) => {
  const q = R.q.trim().toLowerCase();
  return !q || texts.some((x) => x && String(t(x)).toLowerCase().includes(q));
};
const vizTexts = (v) => [v.id, v.title, v.teaser, v.summary, v.question, ...(v.courses || []).map((c) => c.text), ...(v.schema.presets || []).map((p) => p.label)];
const plannedTexts = (p) => [p.id, p.title, p.text];

function audiencePage(aud) {
  const a = audOf(aud);
  const W = worlds(aud), P = plannedOf(aud);
  const school = aud === "school";
  const byGrade = school && R.by === "grade";
  // groups in teaching order (school: or by grade), each with its worlds and its planned items
  let groups;
  if (byGrade) {
    const grades = [7, 8, 9, 10, 11];
    groups = grades.map((g) => [`g${g}`, t("Grade {n:d}", { n: g }), [], P.filter((p) => (p.grades || []).includes(g))]);
    const none = P.filter((p) => !(p.grades || []).length);
    if (none.length) groups.push(["g-", t("Other"), [], none]);
  } else {
    const secs = [...new Set([...W.map((v) => v.section), ...P.map((p) => p.section)])].sort((x, y) => secOrder(x) - secOrder(y));
    groups = secs.map((s) => [s, secLabel(s), W.filter((v) => v.section === s), P.filter((p) => p.section === s)]);
  }
  // the chips count what is ready; at school (nothing ready yet) also what is planned
  const chipGroups = groups.map((g) => [g[0], g[1], school ? [...g[2], ...g[3]] : g[2]]);
  if (R.section !== "all" && !chipGroups.some((g) => g[0] === R.section && g[2].length)) R.section = "all";
  const byToggle = school ? el("span", { class: "st-by" }, t("By:"), " ",
    ["section", "grade"].map((k) => el("button", { class: "chip" + (R.by === k ? " on" : ""), "aria-pressed": String(R.by === k), onclick: () => { R.by = k; R.section = "all"; render(); } },
      k === "section" ? t("section") : t("grade")))) : null;
  const out = [header(a)];
  if (school) out.push(schoolBanner(W, P));
  out.push(filters(chipGroups, byToggle));
  if (!SERVER && !school) out.push(el("div", { class: "help st-local" }, t("Compute live or change the set-up: run lfphys locally"), " → ",
    el("a", { href: quickStart(), target: "_blank", rel: "noopener" }, t("how"))));
  let shown = 0;
  const later = [];  // university, research: the sections with nothing ready yet, folded at the end
  for (const [key, label, ws, ps] of groups) {
    if (R.section !== "all" && R.section !== key) continue;
    const wv = ws.filter((v) => matches(vizTexts(v))), pv = ps.filter((p) => matches(plannedTexts(p)));
    if (!wv.length && !pv.length) continue;
    if (!school && !ws.length) { later.push([key, label, pv]); shown += pv.length; continue; }
    shown += wv.length + pv.length;
    const head = school ? t("{label} · {k:d} of {n:d} ready", { label, k: ws.length, n: ws.length + ps.length })
      : `${label} · ${ws.length}`;
    const sec = el("section", { class: "st-sec" }, el("h2", {}, head));
    if (wv.length) sec.append(el("div", { class: "cards" }, wv.map((v) => vizCard(v))));
    sec.append(...plannedBlock(aud, pv, byGrade ? null : key));
    out.push(sec);
  }
  if (later.length) {
    const open = later.some((g) => g[2].some((p) => p.id === R.focus)) || !!R.q.trim();
    out.push(el("section", { class: "st-sec" }, el("h2", {}, t("Planned in other sections")),
      later.map(([key, label, pv]) => el("details", { class: "st-more-planned", open },
        el("summary", {}, t("{label}: {n:d} planned", { label, n: pv.length })), el("div", { class: "cards" }, pv.map(plannedCard))))));
  }
  if (!shown) out.push(el("p", { class: "muted" }, R.q ? t("Nothing found for “{q}”.", { q: R.q }) : t("Nothing here yet.")));
  out.push(footer());
  return out;
}

// the school's state until AB1 lands (DESIGN §2.2): what is ready, what a school demonstration is, what comes next
function schoolBanner(W, P) {
  const next = P.filter((p) => p.state === "next");
  return el("div", { class: "st-note" },
    el("div", {}, t("The school demonstrations are being built along the curriculum. Each one is the usual lab experiment, computed: you measure, fill the table, draw the line and compare with the law.")),
    el("div", { class: "st-ready" }, el("b", {}, t("Ready: {k:d} of {n:d}.", { k: W.length, n: W.length + P.length })), " ",
      next.length ? t("Next: {list}.", { list: next.map((p) => `${p.id} ${t(p.title)}`).join("; ") }) : null));
}

// the planned items of a group: at school the next ones as cards and the rest folded; elsewhere all folded. Under a
// school section, the worlds of the same topic already there at university or research level (labelled so: rule 14).
function plannedBlock(aud, items, section) {
  const out = [];
  if (!items.length && !(aud === "school" && section)) return out;
  const card = (p) => plannedCard(p);
  if (aud === "school") {
    const next = items.filter((p) => p.state === "next" || R.focus === p.id || R.q.trim());
    const rest = items.filter((p) => !next.includes(p));
    if (next.length) out.push(el("div", { class: "cards" }, next.map(card)));
    if (rest.length) {
      out.push(el("details", { class: "st-more-planned" }, el("summary", {}, next.length ? t("{n:d} more planned", { n: rest.length }) : t("{n:d} planned", { n: rest.length })),
        el("div", { class: "cards" }, rest.map(card))));
    }
    if (section) {
      const ids = new Set(D.planned.filter((p) => p.audience === "school" && p.section === section).map((p) => p.id));
      const there = D.viz.filter((v) => !v.error && (v.audience === "university" || v.audience === "research") && (v.related || []).some((r) => ids.has(r)));
      if (there.length) {
        out.push(el("div", { class: "st-there" }, el("span", { class: "muted" }, t("Already there at another level:")), " ",
          there.flatMap((v, i) => [i ? " · " : "", el("a", { href: `#${audOf(v.audience).hash}/${v.id}` }, `${audOf(v.audience).label} · ${t(v.title)}`)])));
      }
    }
  } else if (items.length) {
    const open = !!items.find((p) => p.id === R.focus) || !!R.q.trim();
    out.push(el("details", { class: "st-more-planned", open }, el("summary", {}, t("{n:d} planned in this section", { n: items.length })),
      el("div", { class: "cards" }, items.map(card))));
  }
  return out;
}

// a planned item: dashed, greyed, nothing to start
const CODE = (c) => (c.system === "AP1" ? `AP 1 U${c.unit}` : c.system && c.system.startsWith("IB") ? `IB ${c.topic}`
  : c.system && c.system.startsWith("AQA") ? `AQA ${c.section}` : null);
function plannedCard(p) {
  const codes = (p.curriculum || []).map(CODE).filter(Boolean);
  const grades = (p.grades || []).length ? t("Grades: {list}", { list: p.grades.join(", ") }) : null;
  const state = p.state === "next" ? t("in preparation (next, {batch})", { batch: p.batch || "" }) : t("planned ({batch})", { batch: p.batch || "" });
  return el("div", { class: "card planned-card", id: "card-" + p.id },
    el("h3", {}, el("span", { class: "mono st-pid" }, p.id), " ", t(p.title)),
    p.text ? el("div", {}, t(p.text)) : null,
    el("div", { class: "muted" }, [grades, secLabel(p.section), codes.join(" · ")].filter(Boolean).join(" · ")),
    p.status ? el("div", {}, el("span", { class: "badge" }, t("Status: {status}", { status: statusText(p.status) }))) : null,
    relatedLine(p),
    el("div", { class: "st-state" }, state));
}
const statusText = (s) => (s === "hypothesis" ? t("hypothesis") : String(s));

// «Same topic»: the related worlds and planned items, each labelled with its audience
function relatedLine(v) {
  const links = [];
  for (const id of v.related || []) {
    const w = D.viz.find((x) => x.id === id && !x.error);
    const p = w ? null : D.planned.find((x) => x.id === id);
    if (!w && !p) continue;
    const a = audOf(w ? w.audience : p.audience);
    if (!a) continue;
    const text = w ? `${a.label} · ${t(w.title)}` : `${a.label} · ${id} ${t(p.title)} (${t("planned")})`;
    links.push(Object.assign(el("a", { href: `#${a.hash}/${id}` }, text), { _w: !!w }));
  }
  links.sort((x, y) => Number(y._w) - Number(x._w));
  if (!links.length) return null;
  // the worlds first, then the planned items; beyond three, the rest behind «+n»
  const box = el("div", { class: "st-related" }, el("span", { class: "muted" }, t("Same topic:")), " ");
  links.forEach((l, i) => { if (i < 3) box.append(...(i ? [" · ", l] : [l])); });
  if (links.length > 3) {
    const more = el("a", { href: "#", class: "st-relmore", onclick: (e) => {
      e.preventDefault();
      more.replaceWith(...links.slice(3).flatMap((l) => [" · ", l]));
    } }, " " + t("+{n:d} more", { n: links.length - 3 }));
    box.append(more);
  }
  return box;
}

// --- a demonstration's card ---------------------------------------------------------------------------------------------
function vizCard(v) {
  const school = v.audience === "school", research = v.audience === "research";
  const presets = v.schema.presets || [];
  const recs = recsOf(v);
  const errBox = el("div", { class: "start-err" });
  const parts = [];
  if (v.picture) parts.push(el("img", { class: "pic", src: url(`images/${v.id}.jpg`), alt: "", loading: "lazy" }));
  parts.push(el("h3", {}, t(v.title)), el("div", { class: "st-teaser" }, t(v.teaser) || t(v.summary)));
  if (v.courses && v.courses.length) {
    parts.push(el("div", { class: "st-books" }, v.courses.map((c) => t(c.text) + (c.chapters ? " " + t("ch. {list}", { list: c.chapters }) : "")).join(" · ")));
  }
  if (research) {
    parts.push(el("div", { class: "st-question" }, el("b", {}, t("Question:")), " ", t(v.question)));
    const refs = v.prior_art || [];
    parts.push(el("div", { class: "st-status" }, el("span", { class: "badge st-hyp" }, t("Status: {status}", { status: statusText(v.status) })), " ",
      refs.length ? el("details", { class: "st-prior" }, el("summary", {}, t("Prior art: {n:d} references", { n: refs.length })),
        el("ul", {}, refs.map((r) => el("li", {}, r.url ? el("a", { href: r.url, target: "_blank", rel: "noopener" }, r.ref) : r.ref)))) : null));
  }
  // the scenario: every preset on the server; on the site the recorded ones
  const options = SERVER ? presets.map((p) => ({ value: p.id, label: t(p.label), preset: p.id }))
    : recs.map((r) => ({ value: r.id, label: t(r.label), preset: r.preset, rec: r }));
  const sel = el("select", { "aria-label": t("Scenario") }, options.map((o) => el("option", { value: o.value }, o.label)));
  const pnote = el("div", { class: "help" });
  const recOf = () => (SERVER ? recs.find((r) => r.preset === sel.value) : (options.find((o) => o.value === sel.value) || {}).rec) || null;
  const btnRec = el("a", { class: "button" + (SERVER ? "" : " primary") });
  const showSel = () => {
    const pre = presets.find((p) => p.id === (SERVER ? sel.value : (recOf() || {}).preset)) || {};
    pnote.textContent = t(pre.note);
    const r = recOf();
    if (r && r.entry) {
      btnRec.classList.remove("disabled");
      btnRec.removeAttribute("aria-disabled");
      btnRec.href = recHref(v, r);
      btnRec.textContent = (SERVER ? t("▷ Recording {time}", { time: mss((r.entry || r).seconds) }) : t("▷ Watch the recording {time}", { time: mss((r.entry || r).seconds) }));
      btnRec.title = r.fromSite ? t("Play the recording of this scenario from the public site (none was made on this server)") : t("Play the saved recording of this scenario: no computation");
    } else {
      btnRec.classList.add("disabled");
      btnRec.setAttribute("aria-disabled", "true");
      btnRec.removeAttribute("href");
      btnRec.textContent = t("▷ Recording");
      // a scenario with a recording spec that nobody has recorded here (every fresh clone) and the published site has
      // not (integrator D4), or a scenario without one
      btnRec.title = r ? t("No recording yet: record it locally (site/record.py) or compute live") : t("No recording for this scenario: compute it live");
    }
  };
  if (SERVER && recs.length && presets.some((p) => p.id === recs[0].preset)) sel.value = recs[0].preset;  // a recorded one first
  sel.addEventListener("change", showSel);
  if (options.length) parts.push(el("div", { class: "row" }, el("span", { class: "muted" }, t("Scenario:")), sel), pnote);
  else parts.push(el("div", { class: "muted" }, t("No recording of this demonstration yet.")));
  // «▸ More»: the parameters, the seed, the devices and the precision (server, not at school)
  let form = null, seed = null, dev = null, prec = null, more = null;
  if (SERVER && !school) {
    const custom = el("div", { style: { display: "none", marginTop: "8px" } });
    const btnCustom = el("button", { onclick: () => {
      if (custom.style.display === "none") {
        const values = {};
        for (const p of v.schema.params) values[p.id] = p.default;
        Object.assign(values, (presets.find((p) => p.id === sel.value) || {}).params || {});
        form = paramForm(v.schema, values);
        custom.replaceChildren(form.el);
        custom.style.display = "";
      } else { custom.style.display = "none"; form = null; }
    } }, t("Parameters…"));
    seed = el("input", { type: "text", placeholder: t("seed (optional)"), style: { width: "11em" } });
    dev = el("select", { title: t("For this run only; by default the settings of the “Devices” page") },
      [["", t("device: as set")], ["auto", t("auto")], ["cpu", "CPU"], ["gpu", "GPU 0"]].map(([val, s]) => el("option", { value: val }, s)));
    prec = el("select", { title: t("The drawing's precision in this run; the checks are always fp64") },
      [["", t("precision: as set")], ["fp64", "fp64"], ["fp32", t("fp32 (where verified)")]].map(([val, s]) => el("option", { value: val }, s)));
    more = el("details", { class: "st-moreopts", open: research },
      el("summary", {}, t("More: parameters, seed, device, precision")),
      el("div", { class: "row" }, btnCustom, seed),
      el("div", { class: "row" }, el("span", { class: "muted" }, t("For this run:")), dev, prec, el("a", { href: withLang(page("settings")) }, t("⚙ Devices"))),
      custom);
  }
  const btns = [];
  if (SERVER && presets.length) {
    const btnRun = el("button", { class: "primary", onclick: async () => {
      const body = { viz: v.id, seed: seed && seed.value.trim() ? seed.value.trim() : null };
      if (form) body.params = form.values; else body.preset = sel.value;
      let over = null;
      try { over = dev ? await runOverride(dev, prec) : null; } catch (e) { toast(String(e.message || e)); return; }
      if (over) body.backend = over;
      await startRun(body, { btn: btnRun, label: t("▶ Compute live"), errBox, form });
    } }, t("▶ Compute live"));
    btns.push(btnRun);
  }
  if (options.length) btns.push(btnRec);
  if (btns.length) parts.push(el("div", { class: "row" }, btns));
  parts.push(errBox);
  showSel();
  parts.push(relatedLine(v));
  if (more) parts.push(more);
  parts.push(el("div", { class: "help st-id" }, t("{id} · version {version}", { id: v.id, version: String(v.version) })));
  return el("div", { class: "card st-card", id: "card-" + v.id }, parts);
}

// --- the laboratories -------------------------------------------------------------------------------------------------
function labsPage() {
  const a = audOf("playground");
  const W = worlds("playground").filter((v) => matches(vizTexts(v)));
  const P = plannedOf("playground");
  return [
    header(a),
    SERVER ? el("p", { class: "st-intro" }, t("A laboratory for each branch of physics: add objects, change their parameters on the go and watch how they move and interact. Nothing is set in advance — everything is computed by the engine's laws in real time; the conservation laws are checked live."))
      : el("div", { class: "st-note warn" }, el("b", {}, t("Works only with a running server:")), " ",
        t("these benches compute what you build, so there is nothing to replay. Run lfphys on your computer (Docker; a GPU is optional)."), " ",
        el("a", { href: quickStart(), target: "_blank", rel: "noopener" }, t("How to run it →"))),
    el("div", { class: "cards" }, W.map((v) => (SERVER ? labCard(v) : labCardOff(v)))),
    P.length ? el("section", { class: "st-sec" }, el("h2", {}, t("Planned")), el("div", { class: "cards" }, P.map(plannedCard))) : null,
    footer(),
  ];
}
function labCardOff(v) {
  return el("div", { class: "card st-card off", id: "card-" + v.id },
    v.picture ? el("img", { class: "pic", src: url(`images/${v.id}.jpg`), alt: "", loading: "lazy" }) : null,
    el("h3", {}, t(v.title)), el("div", { class: "st-teaser" }, t(v.teaser) || t(v.summary)),
    el("div", { class: "help" }, t(v.purpose)),
    el("div", { class: "warn" }, t("server only")));
}
// a laboratory: start from a scenario (a prepared scene, or an empty one) with the section's laws, or from a scene file
// saved earlier (its laws and objects)
async function sceneText(f) {  // at most 900 000 characters (the server's limit for a JSON parameter: review B6-F20)
  const text = await f.text();
  if (text.length > 900000) throw new Error(t("the scene file is longer than {max:d} characters ({n:d})", { max: 900000, n: text.length }));
  return text;
}
function labCard(v) {
  const presets = v.schema.presets;
  const sel = el("select", {}, presets.map((p) => el("option", { value: p.id }, p.label)));
  const pnote = el("div", { class: "help" });
  const showPnote = () => { pnote.textContent = t((presets.find((p) => p.id === sel.value) || {}).note); };
  sel.addEventListener("change", showPnote); showPnote();
  const errBox = el("div", { class: "start-err" });
  const custom = el("div", { style: { display: "none", marginTop: "8px" } });
  let form = null;
  const btnLaws = el("button", { title: t("The world's laws of this section (a change makes a new world)"), onclick: () => {
    if (custom.style.display === "none") {
      const values = {};
      for (const p of v.schema.params) values[p.id] = p.default;
      Object.assign(values, (presets.find((p) => p.id === sel.value) || {}).params || {});
      form = paramForm(v.schema, values);
      custom.replaceChildren(form.el);
      custom.style.display = "";
    } else { custom.style.display = "none"; form = null; }
  } }, t("Laws…"));
  const start = (body, btn, label) => startRun(body, { btn, label, errBox, form: body.params && !body.params.scene ? form : null });
  const btnRun = el("button", { class: "primary", onclick: () => start(form ? { viz: v.id, params: form.values } : { viz: v.id, preset: sel.value }, btnRun, t("▶ Begin")) }, t("▶ Begin"));
  const file = el("input", { type: "file", accept: ".lfscene,.json,application/json", style: { display: "none" } });
  file.onchange = async () => {
    const f = file.files[0];
    file.value = "";
    if (!f) return;
    let sc;
    try { sc = JSON.parse(await sceneText(f)); } catch (e) { toast(t("The scene file was not read: {why}", { why: e.message })); return; }
    if (!sc || sc.format !== "lfscene") { toast(t("This is not a scene file (lfscene)")); return; }
    if (sc.viz && sc.viz !== v.id) { toast(t("This is a scene of the section {other}, not of {this}", { other: sc.viz, this: v.id })); return; }
    start({ viz: v.id, params: { ...(sc.laws || {}), scene: sc } }, btnLoad, t("📂 From a scene file…"));
  };
  const btnLoad = el("button", { title: t("Begin with a scene saved to a file (“💾 Save the scene” in the player)"), onclick: () => file.click() }, t("📂 From a scene file…"));
  return el("div", { class: "card st-card", id: "card-" + v.id },
    v.picture ? el("img", { class: "pic", src: url(`images/${v.id}.jpg`), alt: "", loading: "lazy" }) : null,
    el("h3", {}, t(v.title)),
    el("div", { class: "st-teaser" }, t(v.teaser) || t(v.summary)),
    el("div", { class: "help", style: { marginTop: "6px" } }, t(v.purpose)),
    el("div", { class: "row" }, el("span", { class: "muted" }, t("Begin:")), sel), pnote,
    el("div", { class: "row" }, btnRun, btnLaws, btnLoad, file), errBox,
    custom,
    el("div", { class: "help st-id" }, t("{id} · version {version}", { id: v.id, version: String(v.version) })));
}

// --- starting a run (server) ------------------------------------------------------------------------------------------
// Refused parameters are said at their fields and next to the button, in the owner's words (review UX-params P2); a world
// refused when it is built is waited for a few seconds and said here too, on the form where the owner set the
// parameters, instead of an empty run page (P1). A world that takes longer to build opens in the player.
async function startRun(body, { btn, label, errBox, form }) {
  errBox.replaceChildren();
  if (form) {
    const local = form.errors();
    form.markErrors(local);
    if (Object.keys(local).length) { errBox.append(el("div", {}, t("Not started: {why}", { why: Object.values(local).map((x) => t(x)).join("; ") }))); return; }
  }
  btn.disabled = true;
  try {
    const r = await fetch(url("api/runs"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      if (form && j.fields) form.markErrors(j.fields);
      errBox.append(el("div", {}, t("Not started: {why}", { why: j.error !== undefined ? t(j.error) : r.statusText })));
      btn.disabled = false;
      return;
    }
    btn.textContent = t("⟳ building the world…");
    const t0 = Date.now();
    while (Date.now() - t0 < 8000) {
      await new Promise((ok) => setTimeout(ok, 400));
      let m;
      try { m = await getJSON(url(`api/runs/${encodeURIComponent(j.id)}`)); } catch (e) { break; }
      if (m.state === "failed" || m.state === "finished") {
        const why = (m.errors || []).slice(-1)[0] || t("the world was not created");
        errBox.append(el("div", {}, t(why)), el("div", { class: "muted" }, t("Change the parameters (“Parameters…”) and start again. The record of the refusal is in “My runs”.")));
        btn.disabled = false; btn.textContent = label;
        return;
      }
      if ((m.worlds || []).length) break;
    }
    location.href = withLang(page("run", { id: j.id }));  // a link's language goes along (F7)
  } catch (e) { errBox.append(el("div", {}, String(e.message || e))); btn.disabled = false; btn.textContent = label; }
}

// devices and precision for one run (plan P11: global defaults on the settings page, per-run overrides here); the
// choice applies to the kernels that have a GPU implementation, fp32 only where the kernel allows it
async function runOverride(dev, prec) {
  if (dev.value === "" && prec.value === "") return null;
  if (!kernelInfo) kernelInfo = (await getJSON(url("api/devices"))).kernels;
  const kernels = {};
  for (const k of kernelInfo.filter((x) => x.gpu)) {
    const ok32 = ((k.precisions || {}).fp32 || {}).allowed;
    kernels[k.name] = { device: dev.value || "auto", precision: prec.value === "fp32" && ok32 ? "fp32" : "fp64" };
  }
  return { kernels };
}

// --- the server's runs: «My runs (n)», the health, «Continue» ----------------------------------------------------------
async function poll() {
  try {
    const [runs, h] = await Promise.all([getJSON(url("api/runs")), getJSON(url("api/health"))]);
    D.runs = runs; D.health = h;
    document.getElementById("health").textContent = t("{n:d} of {max:d} running", { n: h.running, max: h.max_workers });
    document.getElementById("myruns").textContent = t("My runs ({n:d})", { n: runs.length });
  } catch (e) { document.getElementById("health").textContent = t("the server is not available"); }
  drawContinue();
}
let continueKey = "";
function drawContinue() {
  const box = document.getElementById("continue");
  if (!box || !D.runs) return;
  // the last two runs someone is watching or that are paused, newest first
  const list = D.runs.filter((r) => r.state === "running" && (r.viewers > 0 || !r.playing))
    .sort((x, y) => String(y.last_action || y.created || "").localeCompare(String(x.last_action || x.created || ""))).slice(0, 2);
  const key = JSON.stringify(list.map((r) => [r.id, r.playing, r.viewers]));
  if (key === continueKey && box.childNodes.length) return;
  continueKey = key;
  if (!list.length) { box.replaceChildren(); return; }
  fill(box, el("span", { class: "muted" }, t("Continue:")),
    list.map((r) => el("a", { class: "st-cont", href: withLang(page("run", { id: r.id })) },
      el("span", { class: "dot " + (r.playing ? "live" : "paused") }), t(r.title),
      el("span", { class: "muted" }, " · " + (r.playing ? t("computing") : t("paused"))))),
    el("a", { href: withLang(page("runs")) }, t("All my runs →")));
}

function showHelp() {
  modal(el("div", {},
    el("h3", {}, t("How it works")),
    el("p", {}, t("Choose your level: school, university or research. Each demonstration is a real computation: the run computes the picture from the laws of physics, and next to every computed value the reference of accepted physics is shown (“Checks”). Nothing is drawn “because it is known”.")),
    SERVER ? el("p", {}, t("“▶ Compute live” starts a run on this server: the world is computed as you watch, and you can change the set-up on the go. “▷ Recording” plays a saved recording of the same scenario at once, with no computation; it can be played back and forth, but not changed.")) : null,
    SERVER ? null : el("p", {}, t("This site holds recordings of real runs. You can play them back and forth and look at the checks and the measured quantities; to compute live, change the set-up or use the laboratories, run lfphys on your computer.")),
    el("p", {}, t("The laboratories are free benches for each branch of physics: you build the scene, and the engine computes it live. They need a running server.")),
    el("p", {}, t("Research set-ups go beyond what has been computed before. Whatever they show that is new is a hypothesis until it is reproduced, and each card says so.")),
    el("p", { class: "muted" }, t("Keys: T — theme, ? — help."))));
}

// --- start ----------------------------------------------------------------------------------------------------------
load().then(() => { parseHash(); render(); }).catch((e) => {  // the routes need the audiences (#labs and the others)
  fill(document.getElementById("start"), el("div", { class: "st-note warn" }, t("Catalogue: {why}", { why: e.message })));
});
if (SERVER) { poll(); setInterval(poll, 3000); }
