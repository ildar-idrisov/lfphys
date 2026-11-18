// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// One page per demonstration (design lfphys/sources/explore_2026-11-14_design.md §3.1–§3.3, §3.8, §3.9):
// run.html?demo=<world>&screen=watch|explore|lab on the site, /run?demo=… on a server. The tabs are the world's screens
// (VIZ["screens"], the catalogue's form registry.screens_of): «Watch · Explore · Lab work» («Наблюдение · Исследование ·
// Лабораторная работа»). The layout is PhET-like: the phenomenon (the world's own view) in the centre, the controls at
// the side, the time at the bottom; checks, «Physics of this world», events and the passport fold into one drawer, «How we
// know this is right». Switching tabs keeps each screen's state; the tab is part of the address. On a server the top bar
// also has «▶ Compute live»: a live run of the screen's preset with the controls' current values (the full player).
//
// Each screen is a module (watch.js, explore.js, lab.js) given a kit: the world, its recordings' index, a factory of
// views (each screen has its own instance of the world's view, told ctx.screen and ctx.ui), the drawer's builder and the
// transport bar. The views draw only what the engine computed: a recording's messages or an atlas point's (record_core.js).
// A world without screens opens its first recording, as before.
//
// Keys (integrator D7, review EX1-screens F2): Space, ← / → and Home are the screen's shortcuts (play/pause, a frame,
// the start) only when the focus is not on an interactive control; on a button Space is the button's own key, on a
// slider the arrows move the slider. T (theme), ? (help) and Escape (close the drawer) work anywhere but in a text field.
// Accessibility (F10): the tabs and their panels are linked (aria-controls / role="tabpanel"), the drawer is a dialog
// (inert while closed; on open the focus goes to its heading, on close back to the opener), symbol buttons are named.
//
// Atlases and recordings (integrator D11, review EX1-screens F9): a screen uses the local atlas only when its key is the
// one this server would build now (GET /api/recordings "expected"); else, on a server whose public site is published
// (site/site.json), the site's atlas of the same world version and the same key; else the screen says «Not built here:
// run site/record.py --world …». Watch plays the local recording, else the site's of the same version (as the player).
import { MODE, apiGet, getJSON, page, postJSON, url } from "./api.js";
import { lang, t, withLang } from "./i18n.js";
import { asOf } from "./record_core.js";
import { el, fill, fmt, initTheme, modal, num, time, toast, toggleTheme } from "./ui.js";

const Q = new URLSearchParams(location.search);
const DEMO = Q.get("demo");
const GITHUB = "https://github.com/ildar-idrisov/lfphys";
const quickStart = () => (lang() === "ru" ? `${GITHUB}/blob/main/README.ru.md#%D0%B1%D1%8B%D1%81%D1%82%D1%80%D1%8B%D0%B9-%D1%81%D1%82%D0%B0%D1%80%D1%82`
  : `${GITHUB}#quick-start`);
const ICON = { watch: "▷", explore: "◎", lab: "✎" };

const D = { viz: null, index: null, screens: [], mods: {}, built: new Map(), active: null, drawerOpen: false, expected: null,
  site: "", published: false, siteIndex: null };

if (DEMO) main().catch((e) => { console.error(e); fail(t("The demonstration could not be opened: {why}", { why: e.message })); });

function fail(text) {
  const box = document.getElementById("demo");
  document.getElementById("app").style.display = "none";
  box.hidden = false;
  fill(box, el("div", { class: "page" }, el("p", {}, el("a", { href: withLang(page("")) }, t("← Start page"))), el("p", {}, text)));
}

async function main() {
  initTheme();
  const app = document.getElementById("app"), box = document.getElementById("demo");
  let world = DEMO;
  if (MODE === "static") {
    try { world = (await getJSON(url("aliases.json")))[DEMO] || DEMO; } catch (e) { /* no alias table: the id as it is */ }
  }
  // a world that does not load says why (the server's text, e.g. "restart the server"; 2026-11-18), else there is none
  try { D.viz = await apiGet(`viz/${encodeURIComponent(world)}`); } catch (e) { fail(e.body && e.body.detail ? e.message : t("No such demonstration")); return; }
  world = D.viz.id;
  D.screens = D.viz.screens || [];
  const [rec, auds] = await Promise.allSettled([apiGet("recordings"), apiGet("audiences")]);
  const all = rec.status === "fulfilled" ? rec.value : null;
  D.index = all && all.worlds ? all.worlds[world] || null : null;
  D.expected = all && all.expected ? all.expected[world] || null : null;
  D.site = (all && all.site) || ""; D.published = !!(all && all.published === true);
  D.audiences = auds.status === "fulfilled" ? auds.value.audiences || [] : [];
  // a server without a current local atlas or recording of a screen: the public site's index, read once (D11), from the
  // site's list of every world's index (api/recordings.json), so that a world not yet published there logs no 404
  if (MODE === "server" && D.published && D.site && D.screens.some((s) => !localReady(s))) {
    try {
      const r = await fetch(`${D.site}api/recordings.json`);
      D.siteIndex = r.ok ? ((await r.json()).worlds || {})[world] || null : null;
    } catch (e) { D.siteIndex = null; }
  }
  if (!D.screens.length) {  // a world without screens: its first recording, as now (design §3.1)
    const r = (D.index && D.index.recordings || [])[0] || (D.viz.recordings || [])[0];
    if (r) { location.replace(withLang(page("run", { rec: `${world}/${r.id}` }))); return; }
    fail(t("This demonstration has no screens and no recording yet.")); return;
  }
  D.mod = await import(`/viz/${world}/view.js`);  // the import map points /viz/ at the site's copy
  app.style.display = "none";
  box.hidden = false;
  document.title = t(D.viz.title) + " · lfphys";
  layout(box);
  const want = Q.get("screen");
  await show(D.screens.find((s) => s.id === want) ? want : D.screens[0].id);
  requestAnimationFrame(loop);
}

// --- the frame: top bar, tabs, the screens' boxes, the drawer ------------------------------------------------------------
function layout(box) {
  const aud = D.audiences.find((a) => a.id === D.viz.audience);
  const back = el("a", { class: "dm-back", href: withLang(page("") + (aud ? `#${aud.id === "playground" ? "labs" : aud.id}/${D.viz.id}` : "")),
    title: t("To the start page: the demonstrations by audience and the laboratories") }, (aud ? "← " + t(aud.label) : t("← Start page")));
  D.tabs = el("div", { class: "dm-tabs", role: "tablist" }, D.screens.map((s) => el("button", {
    role: "tab", id: `dm-tab-${s.id}`, "aria-controls": `dm-panel-${s.id}`, "data-screen": s.id, class: "dm-tab",
    onclick: () => show(s.id), onkeydown: (e) => tabKey(e, s.id) }, el("span", { class: "dm-ic", "aria-hidden": "true" }, ICON[s.kind] || ""), " ", t(s.label))));
  const how = el("button", { class: "dm-how link", onclick: (e) => toggleDrawer(true, e.currentTarget) }, t("How we know this is right"));
  const live = MODE === "server" ? el("button", { class: "dm-live", title: t("A live run of this screen's set-up with the controls' current values: the full player, where everything can be changed"),
    onclick: () => computeLive(live) }, t("▶ Compute live")) : null;
  const theme = el("button", { id: "dm-theme", title: t("Theme (T)"), "aria-label": t("Theme (T)"), onclick: toggleTheme }, "◐");
  const help = el("button", { title: t("Help (?)"), "aria-label": t("Help (?)"), onclick: showHelp }, "?");
  const menu = el("details", { class: "dm-menu" }, el("summary", { title: t("More"), "aria-label": t("More") }, "☰"),
    el("div", { class: "dm-menu-box" },
      el("button", { class: "link", onclick: () => { menu.open = false; toggleDrawer(true, menu.querySelector("summary")); } }, t("How we know this is right")),
      live ? el("button", { class: "link", onclick: () => { menu.open = false; computeLive(live); } }, t("▶ Compute live")) : null,
      el("button", { class: "link", onclick: () => { menu.open = false; toggleTheme(); } }, t("◐ Theme")),
      el("button", { class: "link", onclick: () => { menu.open = false; showHelp(); } }, t("? Help"))));
  const sw = document.querySelector(".lang-switch");  // i18n.js put the switch EN | RU into the player's top bar
  const title = el("span", { class: "dm-title", title: t(D.viz.title) }, t(D.viz.title));
  D.bar = el("div", { class: "topbar dm-top" }, back, el("span", { class: "dm-sep muted" }, "·"), title, D.tabs, el("span", { class: "grow" }),
    how, live, sw, theme, help, menu);
  D.stage = el("div", { class: "dm-screens" });
  D.drawer = el("aside", { class: "dm-drawer", role: "dialog", "aria-modal": "true", "aria-labelledby": "dm-drawer-title", "aria-hidden": "true", inert: "" },
    el("div", { class: "dm-drawer-head" }, el("h2", { id: "dm-drawer-title", tabindex: "-1" }, t("How we know this is right")),
      el("button", { class: "dm-close", title: t("Close"), "aria-label": t("Close"), onclick: () => toggleDrawer(false) }, "✕")),
    D.drawerBody = el("div", { class: "dm-drawer-body" }));
  D.scrim = el("div", { class: "dm-scrim", onclick: () => toggleDrawer(false) });
  fill(box, D.bar, D.stage, D.scrim, D.drawer);
  document.body.classList.add("demo-mode", "ui-" + uiOf());
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && D.drawerOpen) { toggleDrawer(false); return; }
    if (typing(e.target) || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.code === "KeyT" || e.key === "t" || e.key === "T") toggleTheme();
    else if (e.key === "?") showHelp();
    else if (D.drawerOpen || onControl(e.target)) return;  // D7: a control's own keys stay the control's
    else if (D.active && D.active.key) D.active.key(e);
  });
  window.addEventListener("themechange", () => { for (const s of D.built.values()) s.dirty = true; });
}

// a field the viewer types into (no shortcut at all there)
function typing(n) {
  if (!n || !n.tagName) return false;
  if (n.isContentEditable || n.tagName === "TEXTAREA" || n.tagName === "SELECT") return true;
  return n.tagName === "INPUT" && !["range", "checkbox", "radio", "button", "submit", "reset"].includes(n.type);
}
// an interactive control (integrator D7): Space, the arrows and Home are its own there
const CONTROLS = "button, input, select, textarea, a[href], summary, [role=tab], [role=slider], [role=button], [tabindex]:not([tabindex='-1'])";
export function onControl(n) { return !!(n && n.closest && n.closest(CONTROLS)); }
// the tabs' own arrows (the ARIA tabs pattern): ← / → move to the neighbouring tab and open it
function tabKey(e, id) {
  if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
  e.preventDefault();
  const ids = D.screens.map((s) => s.id), k = ids.indexOf(id), n = ids[(k + (e.key === "ArrowRight" ? 1 : ids.length - 1)) % ids.length];
  show(n).then(() => { const b = document.getElementById(`dm-tab-${n}`); if (b) b.focus(); });
}

const uiOf = () => (D.viz.ui === "school" || D.viz.ui === "full" ? D.viz.ui : D.viz.audience === "school" ? "school" : "standard");

// at phone width the view (Explore, Lab work) stays at the top and the time bar (with Lab work's dock) at the bottom:
// the page's scroll padding leaves their room, so that a control scrolled into view (by the focus, by a tap on a
// detent) is not hidden under them (integrator D12)
function stickyPads() {
  const s = D.active, root = document.documentElement;
  const narrow = matchMedia("(max-width: 999px)").matches;
  const top = narrow && s && s.box && s.box.matches(".dm-explore, .dm-lab") ? s.box.querySelector(".dm-stage") : null;
  const bottom = narrow && s && s.box ? s.box.querySelector(".dm-dock") || s.box.querySelector(".dm-bar") : null;
  root.style.setProperty("--dm-sticky-top", `${top ? Math.ceil(top.getBoundingClientRect().height) : 0}px`);
  root.style.setProperty("--dm-sticky-bottom", `${bottom ? Math.ceil(bottom.getBoundingClientRect().height) : 0}px`);
}
const padsObserver = typeof ResizeObserver === "function" ? new ResizeObserver(() => stickyPads()) : null;

async function show(id) {
  const spec = D.screens.find((s) => s.id === id);
  if (!spec) return;
  for (const b of D.tabs.children) {
    const on = b.dataset.screen === id;
    b.classList.toggle("on", on); b.setAttribute("aria-selected", String(on)); b.tabIndex = on ? 0 : -1;
  }
  const u = new URL(location.href);
  u.searchParams.set("screen", id);
  history.replaceState(null, "", u.href);
  for (const s of D.built.values()) { s.box.hidden = true; if (s.hide) s.hide(); }
  let s = D.built.get(id);
  if (!s) {
    const host = el("section", { class: "dm-screen dm-" + spec.kind, "data-screen": id, id: `dm-panel-${id}`, role: "tabpanel", "aria-labelledby": `dm-tab-${id}` });
    D.stage.append(host);
    const mod = D.mods[spec.kind] || (D.mods[spec.kind] = await import(`./${spec.kind}.js`));
    s = { box: host, dirty: true, loading: true };
    D.built.set(id, s);
    try {
      Object.assign(s, await mod.create(host, kit(spec, s), spec));
    } catch (e) {
      console.error(e);
      fill(host, el("div", { class: "page dm-error" }, t("This screen could not be opened: {why}", { why: e.message })));
    }
    s.loading = false;
  }
  s.box.hidden = false;
  D.active = s;
  s.dirty = true;
  if (s.show) s.show();
  if (D.drawerOpen) renderDrawer();
  window.dispatchEvent(new Event("resize"));
  if (padsObserver) { padsObserver.disconnect(); for (const e of s.box.querySelectorAll(".dm-stage, .dm-bar, .dm-dock")) padsObserver.observe(e); }
  stickyPads();
}

function loop(now) {
  const s = D.active;
  if (s && s.tick) { try { s.tick(now); } catch (e) { console.error(e); } }
  if (D.drawerOpen && s && s.drawerKey && s.drawerKey() !== D.drawerKey) renderDrawer();
  requestAnimationFrame(loop);
}

// the drawer is a dialog: inert while closed (out of the tab order), the rest of the page inert while it is open; the
// focus goes to its heading and comes back to the button that opened it (review EX1-screens F10)
function toggleDrawer(on, opener = null) {
  if (on === D.drawerOpen) return;
  D.drawerOpen = on;
  document.body.classList.toggle("dm-drawer-open", on);
  D.drawer.setAttribute("aria-hidden", String(!on));
  D.drawer.inert = !on;
  for (const x of [D.bar, D.stage]) x.inert = on;
  if (on) {
    D.opener = opener || document.activeElement;
    renderDrawer();
    const h = document.getElementById("dm-drawer-title");
    if (h) h.focus();
  } else if (D.opener && D.opener.isConnected) { const o = D.opener; D.opener = null; (o.closest("details:not([open])") ? D.bar.querySelector(".dm-menu summary") || o : o).focus(); }
}
function renderDrawer() {
  const s = D.active;
  D.drawerKey = s && s.drawerKey ? s.drawerKey() : "";
  fill(D.drawerBody, s && s.drawer ? s.drawer() : el("div", { class: "muted" }, t("Nothing computed yet")));
}

async function computeLive(btn) {
  const s = D.active;
  const body = s && s.liveBody ? s.liveBody() : null;
  if (!body) { toast(t("This screen has no set-up to compute live"), "notice", 4000); return; }
  btn.disabled = true;
  try {
    const j = await postJSON(url("api/runs"), { viz: D.viz.id, ...body });
    location.href = withLang(page("run", { id: j.id }));
  } catch (e) { toast(t("Not started: {why}", { why: e.message })); btn.disabled = false; }
}

function showHelp() {
  const sc = (k) => D.screens.some((s) => s.kind === k);
  modal(el("div", {}, el("h3", {}, t(D.viz.title)),
    D.viz.teaser ? el("p", {}, t(D.viz.teaser)) : null,
    sc("watch") ? el("p", {}, el("b", {}, t("Watch")), " — ", t("a recording of a real run with captions: what to look at, step by step. ◀◀ and ▶▶ go to the previous or the next caption.")) : null,
    sc("explore") ? el("p", {}, el("b", {}, t("Explore")), " — ", t("change the controls and launch: every position of a slider is a point the engine computed beforehand, so the picture is the engine's result, not a drawing. The earlier launches stay as faded traces.")) : null,
    sc("lab") ? el("p", {}, el("b", {}, t("Lab work")), " — ", t("a lab experiment: set up, launch, measure with the instruments, fill the table, plot it, fit a line and check it against the law. The worksheet prints the tasks.")) : null,
    el("p", {}, t("“How we know this is right” shows the checks of what is shown against the accepted formulas, the physics of this world, its events and where the data come from.")),
    MODE === "server" ? el("p", {}, t("“▶ Compute live” starts a run of the same set-up on this server, where everything can be changed."))
      : el("p", {}, t("Compute live or change the set-up: run lfphys locally"), " → ", el("a", { href: quickStart(), target: "_blank", rel: "noopener" }, t("how"))),
    el("p", { class: "muted" }, t("Keys: Space — play/pause, ← and → — a frame back/forwards, Home — to the start, T — theme, ? — help.")),
    el("p", { class: "muted" }, t("On a button or a slider these keys are its own: Space presses the button, the arrows move the slider. Tab moves between the controls."))));
}

// --- where a screen's atlases and recordings come from (integrator D11) ----------------------------------------------------
// an atlas of this world: {entry, base (the folder its files are relative to), fromSite} or {why} (not built here, or
// stale): the local one when its key is the one this server would build now (or no expected key is known), else the
// published site's of the same world version and the same key
const notBuilt = () => t("Not built here: run site/record.py --world {world}", { world: D.viz.id });
export function atlasSource(id) {
  const exp = D.expected && D.expected.atlases ? D.expected.atlases[id] : undefined;
  const loc = ((D.index && D.index.atlases) || []).find((a) => a.id === id);
  if (loc && (exp === undefined || loc.key === exp)) return { entry: loc, base: url(`recordings/${D.viz.id}/`), fromSite: false };
  const si = D.siteIndex;
  const rem = si ? (si.atlases || []).find((a) => a.id === id) : null;
  if (rem && exp !== undefined && rem.key === exp && String(rem.version ?? si.version) === String(D.viz.version)) {
    return { entry: rem, base: `${D.site}recordings/${D.viz.id}/`, fromSite: true };
  }
  return { why: notBuilt(), stale: !!loc };
}
// a recording of this world: the local one, else (server) the published site's of the same world version
export function recordingSource(id) {
  const loc = ((D.index && D.index.recordings) || []).find((r) => r.id === id);
  if (loc) return { entry: loc, base: url(`recordings/${D.viz.id}/`), fromSite: false };
  const si = D.siteIndex;
  const rem = si ? (si.recordings || []).find((r) => r.id === id) : null;
  if (rem && String(rem.version ?? si.version) === String(D.viz.version)) return { entry: rem, base: `${D.site}recordings/${D.viz.id}/`, fromSite: true };
  return { why: t("No recording yet: record it locally (site/record.py) or compute live") };
}
// whether a screen has everything it needs here (else the site's index is read)
function localReady(spec) {
  const exp = (id) => (D.expected && D.expected.atlases ? D.expected.atlases[id] : undefined);
  const has = (id) => { const a = ((D.index && D.index.atlases) || []).find((x) => x.id === id); return !!a && (exp(id) === undefined || a.key === exp(id)); };
  if (spec.kind === "watch") return [spec.recording, ...(spec.more || [])].every((r) => ((D.index && D.index.recordings) || []).some((x) => x.id === r));
  if (spec.kind === "explore") return has(spec.atlas);
  return (spec.steps || []).every((st) => has(st.atlas));
}

// --- the kit each screen gets ---------------------------------------------------------------------------------------------
function kit(spec, s) {
  const school = uiOf() === "school";
  return {
    viz: D.viz, world: D.viz.id, index: D.index, ui: uiOf(), school, spec, server: MODE === "server", self: s,
    dirty: () => { s.dirty = true; },
    // a new instance of the world's view for this screen (ctx.screen, ctx.ui; design §2.4); a computed world cannot be
    // changed from it: what a view would send says so
    newView(extra = {}) {
      const needLive = () => toast(MODE === "server" ? t("These are computed points: change the controls, or “▶ Compute live” for a run you can change")
        : t("These are computed points: change the controls; to change anything else, run lfphys locally"), "notice", 4000);
      const ctx = {
        screen: spec.kind, ui: uiOf(), requestRender: () => { s.dirty = true; }, time, num,
        action: needLive, set: needLive, send: (cmd) => { if (cmd !== "speed" && cmd !== "view") needLive(); },
        liveControl: () => el("span"), setScene: () => {}, jumpTo: (tt) => s.jumpTo && s.jumpTo(tt),
        isArchived: () => true, readOnly: () => t("computed points: they cannot be changed here"), atEnd: () => true,
        runMeta: () => null, recordState: () => null, busy: () => null, cancel: () => {},
        frameBlobs: () => (s.frame ? s.frame.blobs : null), speed: () => s.rate || 1, ...extra,
      };
      const v = D.mod.createView(ctx);
      if (!s.view) s.view = v;  // the screen's own view (the first made; later ones draw traces)
      return v;
    },
    howWeKnow: (o) => howWeKnow({ ...o, view: s.view }),
    atlasSource,
    recordingSource,
    transport,
    worksheetHref: () => withLang(page("worksheet", { demo: D.viz.id })),
  };
}

// --- «How we know this is right»: the checks computed by the time shown, the physics, the events, the passport -----------
function checkState(c) {
  if (c.info) return "info";
  let ok = null;
  if (c.ok === true || c.ok === false) ok = c.ok;
  else if (c.ref !== null && c.ref !== undefined && c.rel !== null && c.rel !== undefined) ok = Math.abs(c.rel) <= Math.max(c.tol || 1e-9, 1e-12);
  if (ok === null) return "na";
  return ok ? "ok" : c.expected ? "exp" : "bad";
}
// a check's value: 4 significant digits (review EX1-worlds F17; the relative difference and the tolerance say how close)
const fmtVal = (v, unit) => (v === null || v === undefined ? "—" : typeof v !== "number" ? t(v)
  : (unit && (unit === "s" || (unit.$t === "s" && !unit.a))) ? time(v, 4) : num(v, 4) + (unit ? " " + t(unit) : ""));

// the view's own panels (the live player's contract, view.rightPanels: panel() elements whose contents the view keeps up
// to date in render()) as folds of the drawer; each panel's body is moved once into its fold (u32: «Particle», «Model of
// the slit screen», «Approximations of this segment»; design §6.3)
function viewFolds(view) {
  return ((view && view.rightPanels) || []).map((p) => p._dmFold || (p._dmFold = el("details", { class: "dm-fold dm-view-fold" },
    el("summary", {}, p.firstChild ? p.firstChild.textContent : ""), p.lastChild)));
}

// W: the shown world's record; tt: the time shown; passport: [[label, value], …]; note: what the data are; view: the
// screen's view (its rightPanels fold in after «Physics of this world»); eventTimes: false lists the events without their
// times (Lab work: a landing's time would give away the flight time the lab has the student measure; integrator D10)
function howWeKnow({ W, tt, passport = [], note = null, empty = null, view = null, eventTimes = true }) {
  if (!W) return [el("p", { class: "muted" }, empty || t("Nothing computed yet")), passport.length ? passportBox(passport, note) : null];
  const eps = 1e-12 * Math.abs(tt);
  const checks = [];
  for (const vs of W.checks.values()) {
    let c = null;
    for (const v of vs) { if ((v.t ?? 0) <= tt + eps) c = v; else break; }
    if (c) checks.push([c, checkState(c)]);
  }
  const n = (k) => checks.filter(([, x]) => x === k).length;
  const school = uiOf() === "school";
  const head = checks.length
    ? el("p", { class: "dm-ck-sum " + (n("bad") ? "st-bad" : "st-ok") }, n("bad")
      ? t("✗ {n:d} of {total:d} checks disagree with the laws", { n: n("bad"), total: checks.length })
      : t("✓ {n:d} checks agree with the laws", { n: n("ok") }))
    : el("p", { class: "muted" }, t("No checks up to this moment: they are computed when the run reaches them."));
  const mark = { ok: "✓", bad: "✗", exp: "✗", info: "≈", na: "—" };
  const list = school
    ? el("ul", { class: "dm-ck-list" }, checks.map(([c, k]) => el("li", { class: "st-" + k },
      el("span", { class: "dm-ck-mark" }, mark[k]), " ", el("b", {}, t(c.label)), c.note ? el("div", { class: "muted" }, t(c.note)) : null)))
    : el("table", { class: "dm-ck-table" }, el("tr", {}, el("th", {}, t("check")), el("th", {}, t("computed")), el("th", {}, t("reference")),
      el("th", { title: t("relative difference") }, t("rel.")), el("th", { title: t("tolerance") }, t("tol.")), el("th", {}, "")),
      checks.map(([c, k]) => el("tr", { title: t(c.note) },
        el("td", {}, t(c.label)), el("td", { class: "mono" }, fmtVal(c.value, c.unit)), el("td", { class: "mono" }, fmtVal(c.ref, c.unit)),
        el("td", { class: "mono" }, c.rel === null || c.rel === undefined ? "—" : num(c.rel, 2)),
        el("td", { class: "mono" }, c.rel === null || c.rel === undefined ? "—" : num(Math.max(c.tol || 1e-9, 1e-12), 2)),
        el("td", { class: "st-" + k }, mark[k]))));
  const eng = asOf(W.engineHist, tt) || [];
  const events = W.events.filter((e) => (e.t ?? 0) <= tt + eps);
  return [
    el("section", {}, el("h4", {}, t("Checks: computed ↔ reference")),
      el("p", { class: "help" }, t("Each check compares a quantity computed in this run with the accepted formula (or a second method). ✓ — they agree within the numerical precision.")),
      head, checks.length ? list : null),
    el("details", { class: "dm-fold" }, el("summary", {}, t("Physics of this world")),
      eng.length ? eng.map((d) => el("div", { class: "dm-eng" }, el("b", {}, t(d.title) || d.id),
        d.statement ? el("div", { class: "muted" }, t(d.statement)) : null,
        d.validity ? el("div", { class: "muted" }, t("Where it holds: {validity}", { validity: t(d.validity) })) : null,
        el("div", { class: "mono muted" }, "lfphys." + d.id)))
        : el("div", { class: "muted" }, t("The visualization reported no engine modules."))),
    ...viewFolds(view),
    el("details", { class: "dm-fold" }, el("summary", {}, t("Events: {n:d}", { n: events.length })),
      events.length ? events.map((e) => el("div", { class: "dm-ev" }, eventTimes ? el("span", { class: "mono" }, school ? `${fmt(e.t ?? 0, ".3g")}\u00a0${t("s")}` : time(e.t, 6)) : null,
        eventTimes ? " " : null, t(e.text) || e.kind))
        : el("div", { class: "muted" }, t("No events yet"))),
    passportBox(passport, note),
  ];
}
function passportBox(rows, note) {
  return el("details", { class: "dm-fold", open: true }, el("summary", {}, t("Where these data come from")),
    note ? el("p", {}, note) : null,
    el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v === null || v === undefined ? "—" : String(v))])));
}

// --- the transport bar: ▶/❚❚ (a launch at Explore), ⟲, the timeline over the frames, the time, normal / slow ----------------
// opts: {play(), reset(), scrub(i), rate(r), prev(), next(), launchLabel, slow: bool}. Returns {el, update({playing,
// i, max, label, canPlay, why, launch}), ticks(list of {at (0..1), title, onclick}), setSlowAllowed(ok, why)}
function transport(opts) {
  const play = el("button", { class: "dm-play primary", onclick: () => opts.play() }, "▶");
  const reset = el("button", { class: "dm-reset", title: t("Back to the start (Home)"), "aria-label": t("Back to the start (Home)"), onclick: () => opts.reset() }, "⟲");
  const prev = opts.prev ? el("button", { class: "dm-chap", title: t("The previous caption"), "aria-label": t("The previous caption"), onclick: () => opts.prev() }, "◀◀") : null;
  const next = opts.next ? el("button", { class: "dm-chap", title: t("The next caption"), "aria-label": t("The next caption"), onclick: () => opts.next() }, "▶▶") : null;
  const tl = el("input", { type: "range", class: "dm-timeline", min: 0, max: 0, value: 0, step: 1, title: t("The time shown: every step is a computed frame"),
    "aria-label": t("The time shown: every step is a computed frame") });
  tl.oninput = () => opts.scrub(Number(tl.value));
  const ticks = el("div", { class: "dm-ticks" });
  const tlBox = el("div", { class: "dm-tlbox" }, tl, ticks);
  const label = el("span", { class: "dm-time mono" }, "");
  let rate = 1;
  const seg = el("span", { class: "dm-seg dm-speed", role: "group", "aria-label": t("speed") },
    [[1, t("normal")], [0.25, t("slow")]].map(([r, lab]) => el("button", { "data-rate": String(r), class: r === 1 ? "on" : "", "aria-pressed": String(r === 1),
      onclick: (e) => { if (e.currentTarget.disabled) return; rate = r; mark(); opts.rate(r); } }, lab)));
  const mark = () => { for (const b of seg.children) { const on = Number(b.dataset.rate) === rate; b.classList.toggle("on", on); b.setAttribute("aria-pressed", String(on)); } };
  const bar = el("div", { class: "dm-bar" }, play, reset, prev, next, tlBox, label, el("span", { class: "muted dm-speed-l" }, t("speed:")), seg);
  return {
    el: bar,
    update({ playing, i = 0, max = 0, text = "", title = "", canPlay = true, why = "", launch = false }) {
      const p = playing ? "❚❚" : launch ? (opts.launchLabel || "▶") : "▶";
      if (play.textContent !== p) play.textContent = p;
      play.disabled = !canPlay && !playing;
      const name = playing ? t("Pause (Space)") : launch ? t("Launch (Space)") : t("Play (Space)");
      play.title = !canPlay && why ? why : name;
      if (play.getAttribute("aria-label") !== name) play.setAttribute("aria-label", name);
      if (Number(tl.max) !== max) tl.max = String(max);
      if (Number(tl.value) !== i) tl.value = String(i);
      if (tl.getAttribute("aria-valuetext") !== text) tl.setAttribute("aria-valuetext", text);
      tl.disabled = max <= 0;
      if (label.textContent !== text) label.textContent = text;
      if (title && label.title !== title) label.title = title;
    },
    ticks(list) {
      fill(ticks, list.map((k) => el("button", { class: "dm-tick", style: { left: `calc(${(100 * k.at).toFixed(3)}% - 1px)` }, title: k.title, onclick: k.onclick })));
    },
    setSlowAllowed(ok, why) {
      const b = seg.querySelector('[data-rate="0.25"]');
      b.disabled = !ok; b.title = ok ? "" : why;
      if (!ok && rate !== 1) { rate = 1; mark(); opts.rate(1); }
    },
    rate: () => rate,
  };
}
