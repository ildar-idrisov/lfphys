// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Run page: one player for every visualization. It owns the transport, the history (timeline), the worlds of the
// run, the live set-up, the actions, the checks and the event log; the visualization's own module
// (/viz/<id>/view.js) draws the scene. Everything shown comes from the run's record: the server replays it on
// (re)connection.
//
// A run holds one or more worlds. Live parameters (the set-up an experimenter can change while the world runs)
// apply at once, at the current moment of the world, without an "apply" button. Laws and initial conditions are
// fixed for a world; changing them starts a new world inside the same run (the previous worlds stay in the record
// and can be looked at with the world switch in the top bar).
//
// Transport (owner, 2026-10-28): ⏺ records — the world is computed further and its frames are added to the history;
// ⏮ ◀ ▶ ⏭ and the timeline move along the history. Whatever the cursor points at is shown exactly as it was then:
// the view is fed the record's messages up to that time and rebuilt from the record when the cursor goes back
// (syncView). With the cursor at the end, recording is shown live. There is no stop: a run idle without viewers is
// suspended by the server and resumed (rebuilt from its record) when ⏺ is pressed again.
//
// A saved recording (/run?rec=<world>/<rec>: the public site and the server's recordings; DESIGN of the start page §1.7,
// §4.5) is played by the same player: openRecording hands it the file's messages as a record that has ended. S.recording
// is then set: ⏺, «Keep», «⚙» and «Cancel» are absent, ▶ plays the recording, the set-up, the actions and the world's
// laws are a read-only summary, and everything that would change the world (slice planes too) says «a recording: this
// needs a live run». On the server «▶ Compute this scenario live» starts a run of that world and scenario. The run's
// passport comes from the recording's index entry.
import { MODE, apiGet, connectRun, getJSON, openRecording, page, postJSON, url } from "./api.js";
import { lang, legacy, t, withLang } from "./i18n.js";
import { control, el, fill, initTheme, modal, num, panel, paramForm, time, toast, toggleTheme } from "./ui.js";

initTheme();
const $ = (id) => document.getElementById(id);
const runId = new URLSearchParams(location.search).get("id");
const recParam = new URLSearchParams(location.search).get("rec");  // a saved recording: "<world>/<rec>"
const SITE = "https://ildar-idrisov.github.io/lfphys/";  // the public site, when the server does not say (GET /api/recordings)
const MAX_FRAMES = 20000;  // beyond it the stride of the frames kept doubles: the history stays uniform at any length
// a key frame of the view every KEY_EVERY messages fed in order (owner, 2026-10-29: «для воспроизведения назад давай
// как в видео добавлять ключевые кадры»): going back restores the view from the nearest one before the cursor and
// feeds only the messages after it, so a step back does not replay the record from its start
const KEY_EVERY = Number(new URLSearchParams(location.search).get("key_every")) || 100;  // ?key_every=: tests only
const MAX_KEYS = 256;  // beyond it every other key frame is dropped: their memory stays bounded at any length
const RESUMING = ["play", "step", "next_event", "set", "action", "view", "new_world"];  // resume a suspended run

const S = {
  meta: null, viz: null, view: null, conn: null,
  worlds: [], w: -1,               // all worlds of the run; the one shown
  header: null, frames: [], events: [], checks: new Map(),   // of the shown world
  idx: -1, live: true, playing: false, speed: 1, speedRange: [1e-12, 1e18],
  hist: 0, histT: 0, histWall: 0,  // playing the history: direction (+1, -1, 0), the time shown, the wall clock
  ended: false, suspended: false,  // ended: a record only (cannot go on); suspended: resumed by ⏺
  resumeError: null,               // why the last resume failed (⏺ tries again)
  replaying: true, dirty: false, checksDirty: false, eventsDirty: false, shownKey: "", editKey: "",
  histStride: 1,                   // the server's stride of the frames it replays on (re)connection
  pending: null,                   // "set" | "world" | "resume" while the run has not answered yet
  busy: null,                      // what the worker is computing now ({cmd, what, since}: its "busy" notice; U9)
  sent: null,                      // a scene command sent and not yet taken up by the worker ({what, since})
  runNotes: [],                    // errors and notices before any world (a refused start: review UX-params P1)
  startError: null,                // why the run has no world (its first world was refused)
  seq: 0,                          // arrival order of checks (the newest groups are shown first)
  liveCtl: {}, bound: {},          // live parameter controls (panel) and copies placed by the view
  actCtl: [],                      // controls of live actions (refreshed on "actions")
  recording: null,                 // a saved recording: {world, index, entry, src, site} (null: a run on the server)
};

const curWorld = () => S.worlds[S.w];
const latest = () => S.worlds.length - 1;
const archived = () => S.w !== latest();
const liveParams = () => S.viz.schema.params.filter((p) => p.live);

async function main() {
  if (!runId && !recParam) { document.body.replaceChildren(el("div", { class: "page" }, t("No run given: /run?id=…"))); return; }
  if (recParam) {
    try { await loadRecording(recParam); } catch (e) { recordingRefused(e); return; }
  } else {
    try {
      S.meta = await getJSON(url(`api/runs/${encodeURIComponent(runId)}`));
      S.viz = await getJSON(url(`api/viz/${encodeURIComponent(S.meta.viz)}`));
      // a record made before the translation (its texts are Russian strings): its labels in the language in force, and
      // a note that its sentences with numbers stay as recorded (review i18n-browser F3)
      S.legacy = await legacy(S.meta);
    } catch (e) { document.body.replaceChildren(el("div", { class: "page" }, t("Run not found: {why}", { why: e.message }))); return; }
  }
  document.title = `${t(S.viz.title)} · ${S.recording ? t("recording") : runId}`;
  $("title").textContent = $("title").title = t(S.viz.title);  // the full name in the tooltip when it is cut
  $("runid").textContent = S.recording ? S.meta.id : runId;
  $("keep").textContent = S.meta.keep ? "★" : "☆";
  if (S.recording) recordingChrome();
  if (S.legacy) toast(t("Recorded before the interface was translated (12 November 2026): its sentences with numbers are shown as they were recorded"), "notice", 12000);
  const mod = await import(`/viz/${S.meta.viz}/view.js`);  // the import map points /viz/ at the site's copy
  const ctx = {
    action: (name, args) => sendAction(name, args),
    send: (cmd, args) => send(cmd, args),
    set: (values) => sendSet(values),
    liveControl: (id, opts) => boundControl(id, opts),
    setScene: (text) => { $("scene").textContent = $("scene").title = t(text); },
    requestRender, time, num,
    jumpTo: (tt) => jumpToTime(tt),
    isArchived: () => archived(),  // a world from the record: views must not send view commands for it
    // why the view may not change what the run computes now (slice planes), or "": only at the end of the history of
    // the current world (review C1-7); the event "editablechange" says when it changed
    readOnly: () => editBlock(),
    atEnd: () => atEnd(),  // the cursor at the end of the history of the current world
    runMeta: () => S.meta,  // the run's passport as loaded (a playground: its record's window)
    recordState: () => S.recState || null,  // the record's window as the server sent it on (re)connection
    // what the world is computing now (a scene change, a new world …), or null: views disable their controls meanwhile
    // (review UX-ui U9); the event "busychange" says when it changed
    busy: () => (S.busy || S.sent ? { ...(S.busy || S.sent) } : null),
    frameBlobs: () => { const f = S.frames[S.idx]; return f ? f.blobs : null; },  // the arrays of the frame shown
    cancel: () => cancelBusy(),
    // the playback rate the speed control shows (world time per wall second; also while paused): a throw's velocity
    // in the playground is the hand's motion over it (plan P16.2)
    speed: () => S.speed,
  };
  S.view = mod.createView(ctx);
  layout();
  bindTransport();
  if (S.recording) {
    S.conn = openRecording(S.recording.src, {
      onOpen: reset, onMessage,
      onProgress: (got, total) => setStatus("", total ? t("loading the recording… {got:.2g} of {total:.2g} MB", { got: got / 1e6, total: total / 1e6 })
        : t("loading the recording… {got:.2g} MB", { got: got / 1e6 })),
      onError: (e) => { setStatus("dead", t("the recording could not be read: {why}", { why: e.message })); toast(t("The recording could not be read: {why}", { why: e.message })); },
    }, { frameStride: S.recording.entry.frame_stride || 1 });
  } else S.conn = connectRun(runId, { onOpen: reset, onMessage: onMessage, onClose: () => setStatus("dead", t("connection lost — reconnecting…")) });
  requestAnimationFrame(loop);
}

// --- a saved recording ----------------------------------------------------------------------------------------------
// The world (an old id resolves: the server's /api/viz/<old>, the site's aliases.json), its index (here; on a server with
// no local copy, the public site's — only when it was recorded from the same version of the world), the entry, and the
// passport made from it.
async function loadRecording(spec) {
  const [w0, recId] = String(spec).split("/");
  if (!w0 || !recId) throw new Error(t("a recording is named <world>/<recording>"));
  let world = w0;
  if (MODE === "static") {
    try { world = (await getJSON(url("aliases.json")))[w0] || w0; } catch (e) { /* no alias table: the id as it is */ }
  }
  S.viz = await apiGet(`viz/${encodeURIComponent(world)}`);
  world = S.viz.id;
  let all = null;
  try { all = await apiGet("recordings"); } catch (e) { all = null; }
  try { S.audiences = (await apiGet("audiences")).audiences || []; } catch (e) { S.audiences = []; }  // the back link's label
  const site = (all && all.site) || SITE;
  let index = all && all.worlds ? all.worlds[world] : null;
  let entry = index ? (index.recordings || []).find((r) => r.id === recId) : null;
  let base = url(`recordings/${world}/`), fromSite = false;
  if (!entry && MODE === "server") {  // the public site's recording, made by the same version of the world (§4.6)
    let remote = null;
    try { remote = await getJSON(`${site}recordings/${encodeURIComponent(world)}/index.json`); } catch (e) { remote = null; }
    const e2 = remote ? (remote.recordings || []).find((r) => r.id === recId) : null;
    if (e2 && String(remote.version) === String(S.viz.version)) { index = remote; entry = e2; base = `${site}recordings/${world}/`; fromSite = true; }
    else if (e2) throw Object.assign(new Error(t("No recording for this version: record it locally or compute live")), { version: true });
  }
  if (!entry) throw Object.assign(new Error(t("No recording for this version: record it locally or compute live")), { missing: true });
  const spec0 = (S.viz.recordings || []).find((r) => r.id === recId) || {};
  S.recording = { world, id: recId, index, entry, site, fromSite, src: base + entry.file };
  // the run's passport, from the index entry (what «About the run» shows)
  S.meta = { id: `${world}/${recId}`, viz: world, version: index.version, code: index.code_hash, created: index.made,
             seed: entry.seed ?? spec0.seed ?? 1, preset: entry.preset, keep: false, python: "", recording: entry };
}

// the recording cannot be played: why, with the way to compute it live (server) and back to the start page
function recordingRefused(e) {
  const v = S.viz, [w0, recId] = String(recParam).split("/");
  const preset = ((v && v.recordings) || []).find((r) => r.id === recId)?.preset;
  document.body.replaceChildren(el("div", { class: "page" },
    el("p", {}, el("a", { href: withLang(page("")) }, t("← Start page"))),
    el("h2", {}, v ? t(v.title) : w0),
    el("p", {}, e.message),
    MODE === "server" && v && preset ? el("p", {}, computeLiveButton(v.id, preset, 1)) : null));
}

// «▶ Compute this scenario live» (server): a run of the recording's world and scenario, then its page
function computeLiveButton(viz, preset, seed) {
  const b = el("button", { class: "primary", title: t("Start a run of this world and scenario on this server: the set-up can then be changed") }, t("▶ Compute this scenario live"));
  b.onclick = async () => {
    b.disabled = true;
    try {
      const j = await postJSON(url("api/runs"), { viz, preset, seed });
      location.href = withLang(page("run", { id: j.id }));
    } catch (e) { toast(t("Not started: {why}", { why: e.message })); b.disabled = false; }
  };
  return b;
}

// the top bar of a recording: its badge; no ⏺, no «Keep», no «⚙»; back to the card on its audience page
function recordingChrome() {
  const R = S.recording, ix = R.index || {};
  const date = String(ix.made || "").slice(0, 10);
  const code = String(ix.code_hash || "").slice(0, 8);
  // the code the recording was made with against the code this server runs (design §4.6): the same world version can
  // still differ in its code (the engine, the framework, the world's files)
  const here = MODE === "server" ? String(S.viz.code_hash || "") : "";
  const other = !!(here && ix.code_hash && here !== String(ix.code_hash));
  const badge = el("span", { class: "badge rec-badge" + (other ? " rec-other-code" : ""), id: "recbadge",
    title: [t("A recording of a real run, made by the recorder from the world's code: it plays without computing. Scenario: {label}", { label: t(R.entry.label) }),
      other ? t("Recorded with code {rec}; this server runs {here}", { rec: String(ix.code_hash), here }) : "",
      R.fromSite ? t("Played from the public site: this server has no local copy (the same version of the world).") : ""].filter(Boolean).join("\n") },
    t("RECORDING · {date} · code {code}", { date, code }), other ? " ≠" : "");
  $("status").before(badge);
  for (const id of ["rec", "keep"]) $(id).style.display = "none";
  const gear = document.querySelector('.topbar a[data-page="settings"]');
  if (gear) gear.remove();
  const back = document.querySelector('.topbar a[data-page=""]');
  const a = (S.audiences || []).find((x) => x.id === S.viz.audience);  // registry.AUDIENCES (apiGet("audiences"))
  if (back && a) {
    back.setAttribute("href", page("") + `#${a.id === "playground" ? "labs" : a.id}/${S.viz.id}`);
    back.textContent = "← " + t(a.label);
  }
  $("app").classList.add("recording");
}

// --- layout ---------------------------------------------------------------------------------------
function layout() {
  S.banner = el("div", { class: "banner", style: { display: "none" } });
  S.liveBox = el("div", {});
  S.actionsBox = el("div", {}, el("div", { class: "muted" }, t("waiting for the run…")));
  S.worldBox = el("div", {});
  const left = $("left"), right = $("right");
  const pg = S.viz.kind === "playground";
  left.replaceChildren(S.banner);
  if (S.recording) {  // what this is, and (server) the way to a live run of the same scenario
    left.append(el("div", { class: "rec-note" },
      el("div", {}, t("A recording: the set-up, the actions and the world's laws are shown as recorded and cannot be changed. Change them in a live run.")),
      MODE === "server" ? el("div", { style: { marginTop: "6px" } }, computeLiveButton(S.viz.id, S.recording.entry.preset, S.meta.seed)) : null));
  }
  if (liveParams().length) {  // a playground's live laws too (integrator, 2026-11-05)
    left.append(panel(S.recording ? (pg ? t("Laws of the world (as recorded)") : t("Set-up (as recorded)"))
      : pg ? t("Laws of the world — change at once") : t("Set-up — changes at once"), el("div", {},
      S.recording ? null : el("div", { class: "help" }, pg ? t("A change applies at once, at the world's current moment, to the scene already running; the other laws change with “▶ Start a new world”.")
        : t("Any change applies at once, at the world's current moment, and starts a new stretch of the experiment. There is no “apply” button.")),
      S.liveBox)));
  }
  // "Actions" only when the world has actions at the cursor (review UX-ui U23: an empty panel came first)
  S.actionsPanel = panel(t("Actions"), el("div", {}, el("div", { class: "help" }, t("Done at the world's current moment; the consequences spread from that event.")), S.actionsBox));
  left.append(
    S.actionsPanel,
    ...(S.view.leftPanels || []),
    panel(S.recording ? t("Laws and initial conditions (as recorded)")
      : liveParams().length ? t("New world: laws and initial conditions") : t("New world: scenario, laws, initial conditions"), S.worldBox,
      { closed: liveParams().length > 0 || pg || !!S.recording }),  // a playground's scene is built in this world: closed (U23)
  );
  S.checksBox = el("div", { class: "checks" });
  S.eventsBox = el("div", { class: "events" });
  S.infoBox = el("div", {});
  S.engineBox = el("div", { class: "engine" });
  S.enginePanel = panel(t("Physics of this world"), S.engineBox, { closed: true });
  right.replaceChildren(
    panel(t("Checks: computed ↔ reference"), el("div", {}, el("div", { class: "help" }, t("On the left, the quantity computed in this run from its events; on the right, the closed-form expression of accepted physics (or of the declared modification). ✓ — agreement within the numerical precision.")), S.checksBox)),
    S.enginePanel,
    ...(S.view.rightPanels || []),
    panel(t("Events"), S.eventsBox),
    panel(S.recording ? t("About the recording") : t("About the run"), S.infoBox, { closed: true }),
  );
  $("center").replaceChildren(S.view.center);
  $("theme").onclick = toggleTheme;
  $("help").onclick = showHelp;
  // the side columns fold away, the centre takes the room (review UX-ui U20); kept per browser
  const fold = (side, on) => {
    $("app").classList.toggle("fold-" + side, on);
    try { localStorage.setItem("lfviz.fold-" + side, on ? "1" : ""); } catch (e) { /* private mode */ }
    window.dispatchEvent(new Event("resize"));
  };
  for (const side of ["left", "right"]) {
    let on = false;
    try { on = localStorage.getItem("lfviz.fold-" + side) === "1"; } catch (e) { /* ignore */ }
    if (on) $("app").classList.add("fold-" + side);
    $("fold-" + side).onclick = () => fold(side, !$("app").classList.contains("fold-" + side));
  }
  S.fold = fold;
  $("world").onchange = () => showWorld(Number($("world").value));
  $("keep").onclick = async () => {
    if (S.recording) return;
    const r = await postJSON(url(`api/runs/${encodeURIComponent(runId)}/keep`), { keep: !S.meta.keep });
    S.meta.keep = r.keep; $("keep").textContent = r.keep ? "★" : "☆";
  };
}

// --- live parameters: the set-up, applied at once ---------------------------------------------------
function liveValues() {  // the live set-up in force at the time shown (the latest when the cursor is at the end)
  const W = curWorld();
  if (!W) return {};
  if (atEnd()) return { ...(W.header.params || {}), ...W.live };
  const tt = currentT();
  let v = {};
  for (const h of W.liveHist) { if (h.t <= tt + 1e-12 * Math.abs(tt)) v = h.values; else break; }
  return { ...(W.header.params || {}), ...v };
}
const atEnd = () => S.idx >= S.frames.length - 1;

function shownLive(p, vals) {
  if (!p.show_if) return true;
  return Object.entries(p.show_if).every(([k, allowed]) => allowed.includes(vals[k]));
}

function renderLive() {
  S.liveCtl = {};
  const W = curWorld();
  if (!W || !liveParams().length) { S.liveBox.replaceChildren(); return; }
  const vals = liveValues();
  const groups = new Map();
  for (const p of liveParams()) {
    const g = t(p.group);  // a text: grouped by its rendering
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g).push(p);
  }
  const blocks = [];
  for (const [g, list] of groups) {
    const rows = list.map((p) => {
      const c = control(p, vals[p.id], (v) => sendSet({ [p.id]: v }, c));
      c.p = p;
      S.liveCtl[p.id] = c;
      return c.el;
    });
    const box = el("details", { class: "lgroup", open: true }, el("summary", {}, g), rows);
    blocks.push(box);
  }
  S.liveBox.replaceChildren(...blocks);
  refreshLive();
}

function refreshLive() {
  const vals = liveValues();
  const off = !!editBlock();  // the past cannot be changed: the set-up changes at the record's end
  for (const [id, c] of Object.entries(S.liveCtl)) {
    c.set(vals[id]);
    if (c.refreshOptions) c.refreshOptions(vals);  // options that apply to the world's values (P17)
    c.el.style.display = shownLive(c.p, vals) ? "" : "none";
    c.disable(off);
    c.pending(false);
  }
  for (const d of S.liveBox.querySelectorAll("details.lgroup")) {
    d.style.display = [...d.querySelectorAll(".ctl")].some((r) => r.style.display !== "none") ? "" : "none";
  }
  for (const [id, list] of Object.entries(S.bound)) {
    const p = S.viz.schema.params.find((q) => q.id === id);
    for (const c of list) { c.set(vals[id]); c.pending(false); c.disable(off); c.el.style.display = p && shownLive(p, vals) ? "" : "none"; }
  }
}

// a copy of a live control placed by the view in its own toolbar (kept in sync with the panel)
function boundControl(id, { label = null } = {}) {
  const p = S.viz.schema.params.find((q) => q.id === id && q.live);
  if (!p) return el("span");
  const c = control(p, liveValues()[id] ?? p.default, (v) => sendSet({ [id]: v }, c), { compact: true, label });
  (S.bound[id] = S.bound[id] || []).push(c);
  return c.el;
}

// every command goes through here: one that computes or changes the world resumes a suspended run (the server rebuilds
// its world from the record first)
function send(cmd, args) {
  if (S.suspended && RESUMING.includes(cmd) && S.pending !== "resume") setPending("resume");
  S.conn.send(cmd, args);
  if (cmd === "scene" && (args || {}).op !== "export") {  // shown at once; the worker's "busy" notice follows (U9)
    S.sent = { cmd, what: SCENE_WHAT()[(args || {}).op] || t("scene: an object is being changed"), since: performance.now() };
    renderBusy();
  }
}
const SCENE_WHAT = () => ({ add: t("scene: an object is being added"), remove: t("scene: an object is being removed"),
  set: t("scene: an object is being changed"), edit: t("scene: an object is being moved"),
  duplicate: t("scene: an object is being copied"), label: t("scene: an object is being renamed"), clear: t("scene: being cleared") });

// what the world computes now: the local pending state, or the worker's own notice with the time it has taken and a
// way out (✕: the command is cancelled, the world goes back to just before it; review UX-ui U9)
let busyTimer = null, busyEls = null;
function renderBusy() {
  const b = S.busy || S.sent, box = $("busy");
  const local = S.pending === "world" ? t("a new world is being created…") : S.pending === "set" ? t("the set-up is being rebuilt…")
    : S.pending === "resume" ? t("resuming: the world is being restored…") : "";
  const state = b ? "b:" + (b.cmd || "") : local ? "l:" + S.pending : "";
  if (state !== S.busyState) { S.busyState = state; window.dispatchEvent(new Event("busychange")); }  // views: only on a change
  if (!b && !local) { box.style.display = "none"; clearInterval(busyTimer); busyTimer = null; return; }
  const secs = b ? (performance.now() - b.since) / 1000 : 0;
  if (b && !local && secs < 0.3 && !S.busyShown) {  // a quick command: no flicker
    if (!busyTimer) busyTimer = setInterval(renderBusy, 250);
    return;
  }
  S.busyShown = true;
  box.style.display = "";
  const text = b ? t(b.what) || t("the world is computing") : local;
  // the text and the button are kept and updated in place: a click on ✕ must not meet a rebuilt button (cf. U14)
  if (!busyEls) {
    busyEls = { text: el("span", {}), cancel: el("button", { class: "cancel", title: t("Cancel: the world goes back to the moment before this change (it is not applied)"), onclick: cancelBusy }, t("✕ cancel")) };
  }
  if (busyEls.text.parentNode !== box) box.replaceChildren(busyEls.text, busyEls.cancel);
  const shown = text + (secs >= 1 ? " · " + t("{t:d} s", { t: Math.floor(secs) }) : "…");
  if (busyEls.text.textContent !== shown) busyEls.text.textContent = shown;
  busyEls.cancel.style.display = S.busy && S.busy.cmd !== "build" && secs >= 1 ? "" : "none";
  box.title = S.busy ? t("The world is computing; frames and other commands wait. “✕ cancel” takes the world back to the moment before this change.") : "";
  if (!busyTimer) busyTimer = setInterval(renderBusy, 250);
}
async function cancelBusy() {
  if (!S.busy) return;
  try {
    const r = await fetch(url(`api/runs/${encodeURIComponent(runId)}/cancel`), { method: "POST" });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) toast(j.error || r.statusText, "notice", 5000);
  } catch (e) { toast(t("Cancel: {why}", { why: e.message })); }
}

function editBlock() {
  if (S.recording) return t("a recording: this needs a live run");
  if (archived()) return t("This is a world from the record: neither its slices nor its scene can be changed.");
  if (S.ended) return t("This is an old record: it cannot be changed.");
  if (!atEnd()) return t("You are looking at the experiment's past: slices and the scene are changed at the end of the record (⏭).");
  if (S.pending === "resume") return t("The world is being restored: slices and the scene can be changed when the record resumes.");
  return "";
}

function sendSet(values, ctl) {
  if (S.recording) { toast(t("a recording: this needs a live run"), "notice", 3000); refreshLive(); return; }
  if (S.ended || archived()) { toast(t("This is a record: it cannot be changed any more"), "notice", 3000); refreshLive(); return; }
  if (!atEnd()) { toast(t("You are looking at the experiment's past: the set-up can be changed at the end of the record (⏭)"), "notice", 4000); refreshLive(); return; }
  if (S.pending === "resume") { toast(t("The world is being restored: the set-up can be changed when the record resumes"), "notice", 4000); refreshLive(); return; }
  send("set", { values });
  if (ctl) ctl.pending(true);
  if (S.pending !== "resume") setPending("set");
}

function sendAction(name, args) {
  if (S.recording) { toast(t("a recording: this needs a live run"), "notice", 3000); return; }
  if (S.ended || archived()) { toast(t("This is a record: actions are not available"), "notice", 3000); return; }
  if (!atEnd()) { toast(t("You are looking at the experiment's past: actions at the end of the record (⏭)"), "notice", 4000); return; }
  if (S.pending === "resume") { toast(t("The world is being restored: actions are available when the record resumes"), "notice", 4000); return; }
  send("action", { name, args });
}

function setPending(kind) {
  S.pending = kind;
  if (!kind) S.busyShown = false;
  renderBusy();
  updateTransport();
}

// --- actions: one-off events --------------------------------------------------------------------------
function renderActions(actions) {
  const box = S.actionsBox;
  S.actCtl = [];
  box.replaceChildren();
  const off = !!editBlock();
  if (S.actionsPanel) S.actionsPanel.style.display = actions && actions.length ? "" : "none";
  if (!actions || !actions.length) { box.append(el("div", { class: "muted" }, t("No actions"))); return; }
  for (const a of actions) {
    const help = a.help ? el("div", { class: "help" }, a.help) : null;
    // live action: an argument selects the object (key), the others apply at once (e.g. the speed of an observer)
    if (a.mode === "live" && a.key) {
      const keyArg = a.args.find((x) => x.id === a.key);
      const others = a.args.filter((x) => x.id !== a.key);
      let cur = keyArg.default ?? (keyArg.options[0] && keyArg.options[0].value);
      const vals = {};
      const ctls = [];
      const load = () => {
        const c0 = (a.current && a.current[cur]) || {};
        for (const x of others) { vals[x.id] = c0[x.id] ?? x.default ?? 0; }
        for (const c of ctls) c.set(vals[c.arg.id]);
      };
      const keySel = el("select", { disabled: off }, keyArg.options.map((o) => el("option", { value: o.value }, o.label)));
      keySel.value = cur;
      keySel.onchange = () => { cur = keySel.value; load(); };
      for (const x of others) {
        const c = control(x, x.default ?? 0, (v) => {
          vals[x.id] = v;
          sendAction(a.name, { ...vals, [a.key]: cur });
        });
        c.arg = x; c.disable(off);
        ctls.push(c);
      }
      load();
      box.append(el("div", { class: "action" }, el("div", { class: "name" }, a.label), help,
        el("div", { class: "ctl" }, el("label", {}, keyArg.label), keySel), ctls.map((c) => c.el)));
      continue;
    }
    // one select argument: a button per option (one click)
    if (a.args.length === 1 && a.args[0].type === "select" && a.args[0].options.length <= 8) {
      const arg = a.args[0];
      box.append(el("div", { class: "action" }, el("div", { class: "name" }, a.label), help,
        el("div", { class: "btnrow" }, arg.options.map((o) => el("button", { disabled: off, title: t("{label}: {option}", { label: a.label, option: o.label }),
          onclick: () => sendAction(a.name, { [arg.id]: o.value }) }, o.label)))));
      continue;
    }
    if (!a.args.length) {
      box.append(el("div", { class: "action" }, el("button", { disabled: off, title: a.help || "", onclick: () => sendAction(a.name, {}) }, a.label)));
      continue;
    }
    // several arguments of one event: fields, then one button
    const vals = {};
    const fields = a.args.map((arg) => {
      vals[arg.id] = arg.default ?? (arg.options && arg.options[0] && arg.options[0].value) ?? 0;
      const c = control(arg, vals[arg.id], (v) => { vals[arg.id] = v; });
      c.disable(off);
      return c.el;
    });
    box.append(el("div", { class: "action" }, el("div", { class: "name" }, a.label), help, fields,
      el("button", { class: "primary", disabled: off, onclick: () => sendAction(a.name, { ...vals }) }, "▶ " + t(a.button || a.label))));
  }
}

// --- a new world inside this run ---------------------------------------------------------------------
function renderWorldPanel() {
  const W = curWorld();
  if (!W) return;
  const params = W.header.params || {};
  if (S.recording) {  // the world's laws as recorded: a summary, nothing to start here
    const pr = S.viz.schema.presets.find((x) => x.id === W.header.preset);
    fill(S.worldBox,
      el("div", { class: "help" }, t("The laws and the initial conditions of this world, as recorded. A new world needs a live run.")),
      el("div", { class: "kv" }, el("span", {}, t("Scenario")), el("span", {}, pr ? t(pr.label) : (W.header.preset || t("own parameters"))),
        el("span", {}, t("Random seed")), el("span", { class: "mono" }, String(W.header.seed ?? S.meta.seed))),
      paramForm(S.viz.schema, { ...params, ...(W.live || {}) }, { readOnly: true }).el);
    return;
  }
  // every law of the new world is in the form (review LB1-p02-ux X3: a world of the other dimension needs its own grid
  // and window, which are live laws): those that change also on the go start at their values in this world now and
  // are marked so; one form, so that a law shown only for some values of another (the grid of the space) appears
  const live = curWorld().live || {};
  const values = { ...params, ...live };
  let preset = "";
  const schema = { ...S.viz.schema, params: S.viz.schema.params.map((p) => (p.live ? { ...p, group: t("{group} — also change on the go (now as in this world)", { group: p.group ? t(p.group) : t("Laws") }) } : p)) };
  const form = paramForm(schema, values, {});
  const presetSel = el("select", {}, el("option", { value: "" }, t("— the set-up as now —")),
    S.viz.schema.presets.map((p) => el("option", { value: p.id }, p.label)));
  const note = el("div", { class: "help" });
  const seed = el("input", { type: "text", placeholder: t("seed (now {seed})", { seed: String(W.header.seed) }), style: { width: "100%" } });
  const playground = !!W.header.playground;
  // a playground's scene carried into the new world (plan P16.1): on by default; a scenario brings its own scene
  const carry = el("input", { type: "checkbox", checked: true });
  const carryRow = playground ? el("label", { class: "ctl pg-carry", title: t("The objects of the current scene go into the new world. Their state (positions, velocities, a field) goes with them where the section can carry it; the message after the carry-over says what went with its state, what started afresh from its parameters, what was changed and what the new world refused") },
    carry, " " + t("carry the scene over")) : null;
  const showNote = () => {
    const pr = S.viz.schema.presets.find((x) => x.id === preset);
    if (carryRow) { carry.disabled = !!preset; carryRow.classList.toggle("muted", !!preset); }
    note.textContent = preset
      ? t("The new world starts from the scenario “{name}” with the laws set in the form below.", { name: presetSel.selectedOptions[0].textContent })
        + (pr && pr.note ? " " + t(pr.note) : "")  // what the scenario shows, e.g. a check that fails on purpose (P23)
      : playground ? (carry.checked
        ? t("The new world starts with the laws set in the form below and with this world's scene at its current moment. The message after the carry-over says what went with its state, what started afresh from its parameters (where the section cannot carry the state), what was changed and what the new world refused.")
        : t("The new world starts from an empty scene with the laws set in the form below (the current scene can be saved in “Scene: file” and loaded)."))
        : (liveParams().length ? t("The set-up (source, slits, observer…) goes into the new world as it is now; the laws and initial conditions set in the form change.") : "");
  };
  carry.onchange = showNote;
  presetSel.onchange = () => {
    preset = presetSel.value;
    const base = {};
    for (const p of S.viz.schema.params) base[p.id] = p.default;
    const pr = S.viz.schema.presets.find((x) => x.id === preset);
    form.setValues(pr ? { ...base, ...pr.params } : { ...params, ...(curWorld().live || {}) });
    showNote();
  };
  const go = el("button", { class: "primary", disabled: S.ended, onclick: () => {
    const laws = {};
    for (const p of S.viz.schema.params) if (!p.hidden && p.id in form.values) laws[p.id] = form.values[p.id];
    const body = preset ? { preset, params: laws } : { params: { ...params, ...curWorld().live, ...laws } };
    // a playground's initial scene parameter is not sent: the world's scene is the one built by hand (review B6-F18);
    // with «перенести сцену» the worker carries that scene over itself, from the world's state at this moment (P16.1)
    if (playground && !preset) delete body.params.scene;
    if (playground && !preset && carry.checked) body.carry = true;
    const sd = seed.value.trim();
    if (sd) body.seed = Number(sd);
    if (S.pending === "resume") { toast(t("The world is being restored: a new world can be started when the record resumes"), "notice", 4000); return; }
    send("new_world", body);
    if (S.pending !== "resume") setPending("world");
  } }, t("▶ Start a new world"));
  showNote();
  fill(S.worldBox,
    el("div", { class: "help" }, t("Laws and initial conditions cannot be changed inside a running world: a history computed under other laws is another history. A new world starts in this same run; the earlier ones stay in the record (the world switch at the top).")),
    el("div", { class: "ctl" }, el("label", {}, t("Scenario")), presetSel), carryRow, note,
    form.el,
    el("div", { class: "ctl" }, el("label", {}, t("Random seed")), seed),
    el("div", { style: { marginTop: "8px" } }, go));
}

// --- worlds ---------------------------------------------------------------------------------------------
function newWorld(meta, blobs) {
  const t0 = meta.t || 0;
  const W = { n: meta.world || S.worlds.length + 1, header: meta, headerBlobs: blobs, live: { ...(meta.live || {}) },
              liveHist: [{ t: t0, values: { ...(meta.live || {}) } }],
              // what later messages change, as of each time (the header itself is never changed: review C1-18)
              approxHist: [{ t: t0, v: meta.approximations || [] }], engineHist: [{ t: t0, v: meta.engine || [] }],
              actionsHist: [{ t: t0, v: meta.actions || [] }],
              frames: [], nArrived: 0, stride: S.histStride,  // frames kept: those whose arrival number is on the stride
              events: [], checks: new Map(), viewMsgs: [], maxOn: -Infinity, scan: 0,
              prefix: 0, nOn: 0, keys: [], keyStride: 1,  // messages [0, prefix) all fed; nOn fed in all; key frames
              lastSet: new Map() };  // the latest message of each set-like (type, id) in the record (repeats: U1)
  // settings of devices that the engine adjusted for this run (e.g. a GPU asked for but not available)
  for (const n of ((meta.backend || {}).notes || [])) W.events.push({ t: meta.t || 0, kind: "notice", text: { $t: "ℹ devices: {note}", a: { note: n } } });
  const follow = S.w === latest() || S.w < 0;
  S.worlds.push(W);
  renderWorldSelect();
  if (follow) showWorld(latest());
}

function showWorld(i) {
  S.w = i;
  const W = curWorld();
  // a 3-D world without slice planes and without a field drawn on a brightness scale: its toolbar has no slice tools
  // (review UX-ui U21; the rules are in run.html)
  const s3 = W.header.scene3d;
  const noPlanes = !!s3 && !((s3.planes || {}).max > 0);
  const noField = !!s3 && !(s3.layers || []).some((L) => L.kind === "volume" || L.kind === "vectors") &&
    !(s3.objects || []).some((o) => o.kind === "target" || o.kind === "panel");
  $("app").classList.toggle("no-slices", noPlanes);
  $("app").classList.toggle("no-field", noPlanes && noField);
  S.header = W.header; S.frames = W.frames; S.events = W.events; S.checks = W.checks;
  S.idx = S.frames.length - 1; S.live = true; S.hist = 0;
  rebuildView(W, currentT());
  if (archived()) updateRate(null);  // the measured speed belongs to the live world (review B4-11)
  $("scene").textContent = $("scene").title = t(W.header.title);
  renderAtCursor(W);
  renderLive();
  renderWorldPanel();
  renderInfo();
  renderWorldSelect();
  S.banner.style.display = archived() ? "" : "none";
  S.banner.replaceChildren(t("You are looking at world {n:d} from the record — it cannot be changed. ", { n: W.n }),
    el("button", { onclick: () => showWorld(latest()) }, t("to the current world")));
  S.checksDirty = S.eventsDirty = S.dirty = true;
  updateTransport();
}

// --- the view at the time shown: fed the record's messages up to it; when going back, restored from its nearest key
// frame (a view with snapshot() / restore()) or rebuilt from the record (a view without) --------------------------------
function rebuildView(W, tt) {
  const k = S.viewOwner === W && S.view.restore ? keyBefore(W, tt) : null;
  const t0 = performance.now();
  if (k) {
    try {
      S.view.restore(k.snap);
      const L = W.viewMsgs;
      for (let i = k.i; i < L.length; i++) L[i].on = false;
      W.prefix = W.nOn = W.scan = k.i; W.maxOn = k.maxOn;
      feedView(W, tt);
      DBG.fromKey++; DBG.lastMs = performance.now() - t0; DBG.lastFed = W.prefix - k.i;
      return;
    } catch (e) { console.error("key frame not restored, rebuilding from the record:", e); DBG.keyFailed++; }
  }
  S.view.reset && S.view.reset();
  S.view.onHeader(W.header, W.headerBlobs);
  S.viewOwner = W;
  for (const m of W.viewMsgs) m.on = false;
  W.maxOn = -Infinity; W.scan = 0; W.prefix = 0; W.nOn = 0; W.keys = []; W.keyStride = 1;
  feedView(W, tt);
  DBG.full++; DBG.lastMs = performance.now() - t0; DBG.lastFed = W.prefix;
}
// for automated tests of the page: how the view was last brought to the cursor, and a rebuild from the record on demand
const DBG = { fromKey: 0, full: 0, keyFailed: 0, lastMs: 0, lastFed: 0, repeats: 0 };
window.__lfPlayer = {
  dbg: DBG, keys: () => (curWorld() ? curWorld().keys.length : 0), t: () => currentT(), frames: () => S.frames.length,
  goTo: (i) => goTo(i),
  rebuildFromRecord: () => { const W = curWorld(); S.viewOwner = null; rebuildView(W, currentT()); S.dirty = true; },
  redraw: () => { S.dirty = true; },
  replaying: () => S.replaying,  // the record is still being loaded (language-neutral, for the tests)
};
// the latest key frame at or before t that the view's present state contains (it holds the messages in order up to a
// later point; a key frame records how long its data were then)
function keyBefore(W, tt) {
  if (W.nOn !== W.prefix) return null;  // the view holds messages out of order: only a rebuild is safe
  const eps = 1e-12 * Math.abs(tt);
  for (let j = W.keys.length - 1; j >= 0; j--) {
    const k = W.keys[j];
    if (k.i <= W.prefix && k.maxOn <= tt + eps) return k;
  }
  return null;
}
// one key frame per step of KEY_EVERY × keyStride messages; beyond MAX_KEYS the step doubles and the key frames on the
// coarser grid are kept: uniform over the whole record at any length (review CK-3: dropping every other key frame
// while new ones came at the full rate left the start of a long session without any)
function takeKey(W) {
  const step = KEY_EVERY * W.keyStride, last = W.keys.length ? W.keys[W.keys.length - 1] : null;
  if (Math.floor(W.prefix / step) <= (last ? Math.floor(last.i / step) : 0)) return;
  try { W.keys.push({ i: W.prefix, maxOn: W.maxOn, snap: S.view.snapshot() }); } catch (e) { console.error(e); return; }
  if (W.keys.length > MAX_KEYS) {
    W.keyStride *= 2;
    const s2 = KEY_EVERY * W.keyStride, seen = new Set();
    W.keys = W.keys.filter((k) => { const b = Math.floor(k.i / s2); if (seen.has(b)) return false; seen.add(b); return true; });
  }
}
function feedView(W, tt) {
  const L = W.viewMsgs, eps = 1e-12 * Math.abs(tt), keyed = !!(S.view.snapshot && S.view.restore);
  let first = -1;
  for (let i = W.scan; i < L.length; i++) {
    const m = L[i];
    if (m.on) continue;
    const tm = m.meta.t ?? 0;
    if (tm <= tt + eps) {
      m.on = true; W.maxOn = Math.max(W.maxOn, tm); W.nOn++;
      try { S.view.onMessage(m.meta, m.blobs); } catch (e) { console.error(e); }
      if (i === W.prefix) {
        W.prefix++;
        while (W.prefix < L.length && L[W.prefix].on) W.prefix++;
        if (keyed && W.nOn === W.prefix) takeKey(W);
      }
    } else if (first < 0) first = i;
  }
  W.scan = first < 0 ? L.length : first;
}
function syncView(tt) {
  const W = curWorld();
  if (!W) return;
  if (W.maxOn > tt + 1e-12 * Math.abs(tt)) rebuildView(W, tt);  // the view holds something from later
  else feedView(W, tt);
}

// the latest value of a time-indexed list at or before t
function asOf(list, tt) {
  const eps = 1e-12 * Math.abs(tt);
  let v = list[0].v;
  for (const h of list) { if (h.t <= tt + eps) v = h.v; else break; }
  return v;
}
function renderAtCursor(W) {  // the top bar's approximations, "Physics of this world" and the actions, as of the cursor
  const tt = currentT();
  renderPhysics(W.header.modifications || [], asOf(W.approxHist, tt));
  renderEngine(asOf(W.engineHist, tt));
  renderActions(asOf(W.actionsHist, tt));
}

function renderWorldSelect() {
  const sel = $("world");
  sel.style.display = S.worlds.length > 1 ? "" : "none";
  sel.replaceChildren(...S.worlds.map((W, i) => el("option", { value: i },
    t(i === latest() ? "World {n:d} (current): {title}" : "World {n:d}: {title}", { n: W.n, title: t(W.header.short_title || W.header.title) }))));  // never cut a rendering (F14)
  sel.value = String(Math.max(0, S.w));
}

// --- messages -------------------------------------------------------------------------------------
function reset() {
  S.worlds = []; S.w = -1; S.frames = []; S.idx = -1; S.events = []; S.checks = new Map(); S.header = null;
  S.ended = false; S.suspended = false; S.resumeError = null; S.replaying = true; S.hist = 0; S.live = true;
  S.histStride = 1; S.runNotes = []; S.startError = null; S.busy = null; S.sent = null; S.busyShown = false;
  S.lastSet = new Map(); S.evDrawn = null;
  S.view.reset && S.view.reset();
  S.viewOwner = null;
  setPending(null);
  S.checksDirty = S.eventsDirty = true;
  setStatus("", t("loading the record…"));
}

function onMessage({ meta, blobs }) {
  window.lfInstruments?.message(meta, blobs, { t: currentT, w: () => S.w, n: () => S.worlds.length });  // [LB1 P16.3 instruments] the "Instruments" panel (instruments.js)
  if (meta.type === "header") { newWorld(meta, blobs); if (S.pending === "world") setPending(null); return; }
  if (meta.type === "state") {
    S.playing = meta.playing; S.speed = meta.speed; S.speedRange = meta.speed_range || S.speedRange;
    if (!S.replaying) {
      S.suspended = false; S.ended = false; S.resumeError = null;
      if (S.pending === "resume") setPending(null);
    }
    updateTransport(); renderSpeedTicks(); if (!S.playing) updateRate(null);
    if (meta.reason === "no_viewers" && !S.replaying) toast(t("The run was paused: there were no viewers"), "notice", 4000);
    return;
  }
  if (meta.type === "history_start") {
    S.histStride = Math.max(1, meta.frame_stride || 1);
    if (meta.buffer) S.recState = meta.buffer;  // a playground's record window now (the run's, not the world's: B6-F11)
    return;
  }
  if (meta.type === "history_end") {
    S.replaying = false;
    S.histStride = 1;
    S.resumeError = meta.resume_error ? t(meta.resume_error) : null;
    S.startError = meta.start_error ? t(meta.start_error) : null;  // the first world was refused: said in the status and "Events" (P1)
    if (!meta.live) {  // nothing computes now: a suspended run goes on when ⏺ is pressed, an old record cannot
      S.playing = false; S.suspended = !!meta.resumable; S.ended = !meta.resumable;
      if (S.worlds.length) showWorld(S.w);
    } else if (meta.rebuilding) setPending("resume");  // opened while another tab's ⏺ rebuilds the world
    if (S.frames.length && S.live) S.idx = S.frames.length - 1;
    S.dirty = true; updateTransport();
    if (S.recording && S.frames.length > 1) { goTo(0); playHistory(+1); }  // a recording plays from its start
    return;
  }
  if (meta.type === "end") {  // a worker finished (suspended, or the end of an old record): the history goes on
    if (!S.replaying) { S.playing = false; updateTransport(); }
    return;
  }
  if (meta.type === "busy") {  // what the worker computes now (not recorded; review UX-ui U9)
    // a run the server resumes by itself (after a cancel): rebuilding, not «приостановлен»
    if (meta.on && meta.cmd === "build" && !S.replaying && (S.suspended || S.ended) && S.worlds.length) {
      S.suspended = false; S.ended = false; S.pending = "resume";
    }
    if (meta.on) S.busy = { cmd: meta.cmd, what: meta.what, since: performance.now() - 1000 * (meta.elapsed || 0) };
    else { S.busy = null; S.sent = null; S.busyShown = false; }
    renderBusy(); updateTransport();
    return;
  }
  if (meta.type === "closed") {
    S.playing = false; S.suspended = meta.state === "suspended"; S.ended = !S.suspended;
    S.resumeError = meta.resume_error ? t(meta.resume_error) : null;
    S.busy = null; S.sent = null; S.busyShown = false;
    if (!S.worlds.length) S.startError = S.startError || (S.runNotes.find((n) => n.kind === "error") || {}).text || null;
    if (S.pending) setPending(null);  // nothing computes any more: nothing is pending (review C1-8)
    else renderBusy();
    updateTransport();
    if (S.worlds.length) { renderAtCursor(curWorld()); refreshLive(); renderWorldPanel(); }
    return;
  }
  // the record's log of world-changing commands and the places of the world's saved states (for resuming), not shown
  if (meta.type === "command" || meta.type === "checkpoint" || meta.type === "resumed" || meta.type === "record_segment") return;
  const W = S.worlds[latest()];
  if (!W) {  // before any world: a refused start says why here (review UX-params P1: it was dropped)
    if (meta.type === "error" || meta.type === "notice") {
      S.runNotes.push({ t: meta.t || 0, kind: meta.type, text: (meta.type === "error" ? "" : "ℹ ") + t(meta.text), detail: meta.detail });
      if (meta.type === "error") { S.startError = t(meta.text); if (S.pending === "world") setPending(null); }
      if (!S.replaying) toast(meta.text, meta.type === "error" ? "error" : "notice", meta.type === "error" ? 15000 : 6000);
      S.eventsDirty = true; updateTransport();
    }
    return;
  }
  const shown = S.w === latest();
  switch (meta.type) {
    case "frame":
      addFrame(W, { t: meta.t, meta, blobs }, shown);
      if (shown) { if (S.live && !S.hist) S.idx = W.frames.length - 1; S.dirty = true; }
      if (shown && !S.replaying) updateRate(meta);
      break;
    case "event":
      W.events.push(meta); W.viewMsgs.push({ meta, blobs });
      if (shown) { S.eventsDirty = true; S.dirty = true; }
      // an event the world asks to show at once (e.g. a body just added merged into another; review UX-ui U4)
      if (meta.notify && !S.replaying) toast(meta.text, "notice", 8000);
      if (meta.kind === "scene" && S.sent && !S.busy) { S.sent = null; renderBusy(); }
      break;
    case "check": {  // every version is kept: the panel shows, per check, the latest one computed by the cursor's time
      meta._seq = ++S.seq;
      const vs = W.checks.get(meta.id);
      if (vs) vs.push(meta); else W.checks.set(meta.id, [meta]);
      if (shown) S.checksDirty = true;
      break;
    }
    case "live":  // the live values in force (also after a refused change: the controls roll back)
      W.live = { ...W.live, ...(meta.values || {}) };
      W.liveHist.push({ t: meta.t || 0, values: { ...W.live } });
      if (meta.engine) W.engineHist.push({ t: meta.t || 0, v: meta.engine });
      if (shown) { refreshLive(); if (meta.engine) renderAtCursor(W); }
      if (S.pending === "set") setPending(null);
      break;
    case "error":
      // a refusal or a failure arrived live: the page's own pending changes hear of it (a playground's drag: its ghost
      // snaps back, plan P16.2)
      if (!S.replaying) window.dispatchEvent(new CustomEvent("lferror", { detail: meta }));
      if (meta.server) {  // the server refused a command (not part of the record): say why, roll the controls back
        toast(meta.text);
        if (S.pending) setPending(null);
        if (shown) refreshLive();
        break;
      }
      W.events.push({ t: meta.t, kind: "error", text: meta.text, detail: meta.detail });
      if (shown) S.eventsDirty = true;
      if (!S.replaying) toast(meta.text);  // the owner's text (lfviz.errors); the detail only folded in «События»
      if (S.pending === "world") setPending(null);
      if (S.sent && !S.busy) { S.sent = null; renderBusy(); }
      break;
    case "notice":
      W.events.push({ t: meta.t, kind: "notice", text: "ℹ " + t(meta.text), detail: meta.detail });
      if (shown) S.eventsDirty = true;
      if (!S.replaying) toast(meta.text, "notice", 6000);
      break;
    case "actions":  // the simulation updated its actions (e.g. the current speed of each observer)
      W.actionsHist.push({ t: meta.t || 0, v: meta.actions });
      if (shown) S.dirty = true;
      break;
    default:
      if (meta.repeat && sameAsHeld(W, meta, blobs)) { DBG.repeats++; break; }  // an unchanged repeat changes nothing (U1)
      if (meta.repeat || SET_TYPES.has(meta.type)) W.lastSet.set(meta.type + ":" + (meta.id ?? ""), { meta, blobs });
      // a message may carry the world's approximations in force (e.g. a 3-D world's slices changed): top bar
      if (Array.isArray(meta.approximations)) {
        W.approxHist.push({ t: meta.t || 0, v: meta.approximations });
        if (shown) S.dirty = true;
      }
      W.viewMsgs.push({ meta, blobs });
      if (shown) S.dirty = true;
  }
}

// A playground repeats the latest set-like messages at every segment start (lfviz.playground: a segment must be drawable
// on its own) with `repeat: true`. A repeat equal to the message of the same (type, id) this world's record already holds
// is not given to the view: it would change nothing but re-apply the same box, mesh, scene … (review UX-ui U1: an
// unchanged box re-sent every minute put the camera back to its first view). A viewer whose record starts at that
// segment has no earlier one and gets it.
const SET_TYPES = new Set(["box", "mesh", "lines", "marks", "shapes", "actions", "approx", "arrow", "volume", "target", "scene"]);
function sameAsHeld(W, meta, blobs) {
  const prev = W.lastSet.get(meta.type + ":" + (meta.id ?? ""));
  if (!prev) return false;
  const strip = (m) => { const o = { ...m }; delete o.t; delete o.repeat; delete o.blobs; return JSON.stringify(o); };
  if (strip(prev.meta) !== strip(meta)) return false;
  const ka = Object.keys(prev.blobs || {}), kb = Object.keys(blobs || {});
  if (ka.length !== kb.length) return false;
  for (const k of kb) {
    const a = prev.blobs[k], b = blobs[k];
    if (!a || a.byteLength !== b.byteLength) return false;
    const x = new Uint8Array(a.buffer, a.byteOffset, a.byteLength), y = new Uint8Array(b.buffer, b.byteOffset, b.byteLength);
    for (let i = 0; i < x.length; i++) if (x[i] !== y[i]) return false;
  }
  return true;
}

// The frames kept are those whose arrival number is a multiple of the world's stride, and the latest one (the end of
// the history until the next frame arrives); beyond MAX_FRAMES the stride doubles. The density is the same over the
// whole history at any length (review C1-12: halving all frames again and again left the start of a long session
// almost empty). Frames replayed on (re)connection count as the server's stride each. The cursor keeps its time.
function addFrame(W, f, shown) {
  f.n = W.nArrived;
  W.nArrived += S.replaying ? S.histStride : 1;
  const F = W.frames, follow = !shown || (S.live && !S.hist);
  const tt = shown && !follow ? currentT() : 0;
  if (F.length && F[F.length - 1].n % W.stride !== 0) F.pop();
  F.push(f);
  if (F.length > MAX_FRAMES) {
    W.stride *= 2;
    let j = 0;
    for (let i = 0; i < F.length; i++) if (F[i].n % W.stride === 0 || i === F.length - 1) F[j++] = F[i];
    F.length = j;
  }
  if (shown && !follow) S.idx = frameIndexAt(tt);
}
function frameIndexAt(tt) {  // the last frame at or before tt
  const F = S.frames;
  let lo = 0, hi = F.length - 1;
  if (hi < 0) return -1;
  if (tt <= F[0].t) return 0;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (F[mid].t <= tt) lo = mid; else hi = mid - 1; }
  return lo;
}

const short = (s, n) => (String(s).length > n ? String(s).slice(0, n - 1) + "…" : String(s));
function renderPhysics(mods, approx) {
  const box = $("physics");
  const val = (v) => (typeof v === "number" ? num(v) : t(v));  // a modified law's value: a number or an option's label
  approx = (approx || []).map((a) => t(a));
  box.replaceChildren(...[mods.length
    ? el("span", { class: "badge mod", title: t("Modified physics:") + "\n" + mods.map((m) => t("{label}: {value} (accepted: {standard})", { label: t(m.label), value: val(m.value), standard: val(m.standard) })).join("\n") },
        t("MODIFIED PHYSICS:") + " " + short(`${t(mods[0].label)} = ${val(mods[0].value)}`, 40) + (mods.length > 1 ? ` (+${mods.length - 1})` : ""))
    : el("span", { class: "badge std", title: t("All laws are the accepted ones") }, t("standard physics")),
    // approximations the world itself flags (owner, 2026-10-24: «помечать там, где это приближение»)
    approx.length ? el("span", { class: "badge mod", title: approx.join("\n") },
      t("APPROXIMATION:") + " " + (approx[0].length > 48 ? approx[0].slice(0, 46) + "…" : approx[0]) + (approx.length > 1 ? ` (+${approx.length - 1})` : "")) : null]
    .filter(Boolean));
}

// the engine modules this world's physics comes from: the core (established physics) and, outside it, the
// approximations, interpretations, models and alternatives (lfphys/LAYERS.md)
const KIND = () => ({ approximation: t("approximation"), interpretation: t("interpretation"), model: t("model"), alternative: t("alternative") });
function renderEngine(list) {
  list = list || [];
  const core = list.filter((d) => d.layer === "core"), th = list.filter((d) => d.layer === "theories");
  const rest = list.filter((d) => d.layer !== "core" && d.layer !== "theories");
  S.enginePanel.querySelector("h4").firstChild.textContent =
    list.length ? t("Physics of this world: core {core:d} · outside the core {other:d}", { core: core.length, other: th.length }) : t("Physics of this world");
  const item = (d) => el("div", { class: "eng " + d.layer + (d.kind === "alternative" ? " alt" : "") },
    el("div", {}, el("b", {}, t(d.title) || d.id), d.layer === "theories" ? el("span", { class: "badge" }, " " + (KIND()[d.kind] || t(d.kind))) : null),
    d.statement ? el("div", { class: "muted" }, t(d.statement)) : null,
    d.validity ? el("div", { class: "muted" }, t("Where it holds: {validity}", { validity: t(d.validity) })) : null,
    (d.conflicts || []).map((c) => el("div", { class: "conf" }, "⚠ " + t(c))),
    el("div", { class: "mono muted" }, "lfphys." + d.id));
  fill(S.engineBox,
    el("div", { class: "help" }, t("Where the physics of this world comes from: the core of the lfphys engine is established and confirmed physics; outside the core are widely used approximations, interpretations and models (each names where it departs from the core) and alternatives for “what if” experiments.")),
    core.length ? el("h5", {}, t("Core")) : null, core.map(item),
    th.length ? el("h5", {}, t("Outside the core")) : null, th.map(item),
    rest.length ? el("h5", {}, t("Sets of laws and tools")) : null, rest.map(item),
    list.length ? null : el("div", { class: "muted" }, t("The visualization reported no engine modules.")));
}

function renderInfo() {
  const m = S.meta, h = S.header || {};
  // what was drawn and what was checked, per kernel (review B1-4: one record hid the precision of the drawing)
  const used = Object.entries((h.backend || {}).used || {});
  const dv = (u) => `${u.device === "gpu" ? "GPU" : "CPU"}, ${u.precision}`;
  const devText = used.length
    ? used.map(([k, u]) => t("{kernel}: drawing — {drawn}; checks — {check}", { kernel: k, drawn: u.drawn ? dv(u.drawn) : "—", check: u.check ? dv(u.check) : "—" })).join("; ")
    : t("all computations of this world are on the CPU (it called no kernels with a GPU implementation)");
  const over = (m.backend_settings || {}).override;
  if (S.recording) { renderRecInfo(); return; }
  const rows = [[t("Run"), m.id], [t("Visualization"), t("{id} (version {version})", { id: m.viz, version: String(m.version) })], [t("Code"), m.code],
    [t("Devices"), devText + (over ? " " + t("(the choice of devices was set for this run)") : "")],
    [t("World"), t("{n:d} of {total:d}", { n: (curWorld() || {}).n || 1, total: S.worlds.length })], [t("Seed"), h.seed ?? m.seed],
    [t("Created"), m.created], [t("Scenario"), h.preset || m.preset || t("own parameters")], ["Python", m.python]];
  fill(S.infoBox,
    h.text ? el("p", {}, h.text) : null,
    el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, String(v ?? ""))])),
    el("p", {}, el("a", { href: url(`api/runs/${encodeURIComponent(runId)}/stream`) }, t("Download the record (.lfrec)")), " · ", el("a", { href: url(`api/runs/${encodeURIComponent(runId)}`), target: "_blank" }, t("the run's metadata (JSON)"))));
}
// «About the recording»: its passport from the index entry
function renderRecInfo() {
  const R = S.recording, ix = R.index || {}, e = R.entry, h = S.header || {};
  const rows = [[t("Recording"), S.meta.id], [t("Visualization"), t("{id} (version {version})", { id: R.world, version: String(ix.version) })],
    [t("Code"), ix.code_hash],
    ...(MODE === "server" && S.viz.code_hash && S.viz.code_hash !== ix.code_hash ? [[t("This server's code"), S.viz.code_hash]] : []),
    [t("Recorded"), String(ix.made || "").replace("T", " ")], [t("Recorder"), ix.recorder],
    [t("Scenario"), t(e.label)], [t("Seed"), h.seed ?? S.meta.seed],
    [t("Played"), t("{s:g} s at {fps:g} frames per second", { s: e.seconds, fps: e.fps })],
    [t("Frames"), e.frame_stride > 1 ? t("{n:d} kept of {total:d} (one in {k:d})", { n: e.frames, total: e.frames_recorded ?? e.frames * e.frame_stride, k: e.frame_stride }) : String(e.frames)],
    [t("Size"), t("{n:.3g} MB", { n: (e.bytes_gz || 0) / 1e6 })],
    [t("World"), t("{n:d} of {total:d}", { n: (curWorld() || {}).n || 1, total: S.worlds.length })]];
  fill(S.infoBox,
    h.text ? el("p", {}, t(h.text)) : null,
    el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, String(v ?? ""))])),
    el("p", {}, el("a", { href: R.src, download: "" }, t("Download the recording (.lfrec.gz)")),
      R.fromSite ? el("span", { class: "muted" }, " · " + t("from the public site")) : null));
}

// --- render loop ----------------------------------------------------------------------------------
function requestRender() { S.dirty = true; }

function loop() {
  if (S.hist) advanceHistory();
  // while the record is replayed on (re)connection nothing is drawn: every render redraws the whole scene, so the
  // intermediate states of a long record cost seconds (found while processing review C1); history_end draws once
  if (S.dirty && S.header && !S.replaying) {
    S.dirty = false;
    const f = S.frames[S.idx], tt = currentT();
    syncView(tt);
    if (f) {
      try { S.view.render(f.meta, f.t, f.blobs); } catch (e) { console.error(e); }
      $("time").textContent = "t = " + time(f.t, 9);
    }
    updateTimeline();
    S.eventsDirty = true;
    // what depends on the time shown: the check versions computed by then, the set-up in force, the actions, the
    // approximations and the engine modules in force, the controls' availability
    const W = curWorld(), eps = 1e-12 * Math.abs(tt);
    const upTo = (list) => { let n = 0; for (const h of list) { if (h.t <= tt + eps) n++; else break; } return n; };
    let nc = 0;
    for (const vs of S.checks.values()) for (const c of vs) { if ((c.t ?? 0) <= tt + eps) nc++; else break; }
    const key = W ? `${nc}|${upTo(W.liveHist)}|${upTo(W.actionsHist)}|${upTo(W.approxHist)}|${upTo(W.engineHist)}|${atEnd() ? 1 : 0}` : "";
    if (key !== S.shownKey) {
      S.shownKey = key; S.checksDirty = true; refreshLive();
      if (W) renderAtCursor(W);
      updateTransport();
    }
  }
  if (S.checksDirty && !S.replaying) { S.checksDirty = false; renderChecks(); }
  if (S.eventsDirty && !S.replaying) { S.eventsDirty = false; renderEvents(); }
  requestAnimationFrame(loop);
}

function currentT() { const f = S.frames[S.idx]; return f ? f.t : 0; }

// The checks: one line per check — label, value with its reference under it, ✓ / ✗ in a fixed column — the note behind
// "ⓘ" (and as the line's tooltip), groups with a summary that fold, the older groups folded away; what the owner opened
// stays open across the renders that new checks cause (review UX-ui U16, U17). A check that fails on purpose (a «what
// if» preset, a preset outside its approximation) carries `expected`: drawn as an expected ✗ with the reason (P23).
const CK = { open: new Set(), groups: new Map(), older: false };
function checkState(c) {
  if (c.info) return "info";
  let ok = null;
  if (c.ok === true || c.ok === false) ok = c.ok;
  else if (c.ref !== null && c.ref !== undefined && c.rel !== null && c.rel !== undefined) ok = Math.abs(c.rel) <= Math.max(c.tol || 1e-9, 1e-12);
  if (ok === null) return "na";
  return ok ? "ok" : c.expected ? "exp" : "bad";
}
function renderChecks() {
  // groups ordered by their latest check: the current segment first; older groups folded away; only the checks
  // computed by the time shown
  const groups = new Map(), tNow = currentT(), eps = 1e-12 * Math.abs(tNow);
  for (const vs of S.checks.values()) {
    let lo = 0, hi = vs.length - 1;  // the latest version at or before the cursor (versions come in time order)
    if ((vs[0].t ?? 0) > tNow + eps) continue;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if ((vs[mid].t ?? 0) <= tNow + eps) lo = mid; else hi = mid - 1; }
    const c = vs[lo];
    const g = c.group ? t(c.group) : t("Other");  // a text: grouped by its rendering
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g).push(c);
  }
  const order = [...groups.entries()].map(([g, list]) => [g, list, Math.max(...list.map((c) => c._seq || 0))])
    .sort((a, b) => b[2] - a[2]);
  const RECENT = 4;
  const table = (entries, first) => el("table", {}, el("colgroup", {}, el("col", {}), el("col", { class: "c-val" }), el("col", { class: "c-st" })),
    entries.flatMap(([g, list], i) => checkRows(g, list, first && i === 0)));
  const recent = order.slice(0, RECENT), old = order.slice(RECENT);
  const older = old.length ? el("details", { class: "older" }, el("summary", {}, t("Earlier groups of checks: {n:d}", { n: old.length })), table(old, false)) : "";
  if (older) { older.open = CK.older; older.addEventListener("toggle", () => { CK.older = older.open; }); }
  const sc = S.checksBox.scrollTop;
  S.checksBox.replaceChildren(
    order.length ? table(recent, true) : el("div", { class: "muted" }, S.recording ? t("No checks up to this moment of the recording.") : t("Nothing computed yet: start the recording (⏺).")), older);
  S.checksBox.scrollTop = sc;
}

function checkRows(g, list, newest) {
  const rows = [], st = list.slice(-40).map((c) => [c, checkState(c)]);
  const n = (k) => st.filter(([, x]) => x === k).length;
  const sum = [n("ok") ? `${n("ok")} ✓` : "", n("bad") ? `${n("bad")} ✗` : "", n("exp") ? `${n("exp")} ✗ ` + t("expected") : "",
    n("info") ? `${n("info")} ≈` : "", n("na") ? `${n("na")} —` : ""].filter(Boolean).join(" · ");
  // a group is open when the owner opened it, else when it is the newest or has a failure
  const open = CK.groups.has(g) ? CK.groups.get(g) : (newest || n("bad") > 0);
  const head = el("tr", { class: "grp-row", title: open ? t("Collapse the group") : t("Unfold the group") },
    el("td", { class: "grp", colspan: 3 }, el("span", { class: "fold" }, open ? "▾ " : "▸ "), g,
      el("span", { class: "grp-sum" + (n("bad") ? " st-bad" : "") }, sum)));
  head.onclick = () => { CK.groups.set(g, !open); renderChecks(); };
  rows.push(head);
  if (!open) return rows;
  for (const [c, k] of st) {
    const note = t(c.note), expected = c.expected ? t("Expected: {why}", { why: c.expected }) : "";
    const mark = { ok: ["st-ok", "✓", note || t("agreement within the numerical precision")],
      bad: ["st-bad", "✗", c.rel !== null && c.rel !== undefined ? t("relative difference {rel:.3g}, tolerance {tol:.2g}", { rel: c.rel, tol: c.tol || 1e-9 }) : note],
      exp: ["st-exp", "✗", expected],
      info: ["st-na", "≈", t("A comparison for information, not a check")], na: ["st-na", "—", t("This quantity has no closed-form reference")] }[k];
    const key = t(c.group) + "|" + c.id;
    const hasNote = !!(c.note || c.expected);
    const info = hasNote ? el("button", { class: "ck-i", title: t("About the check"), onclick: (e) => {
      e.stopPropagation(); if (CK.open.has(key)) CK.open.delete(key); else CK.open.add(key); renderChecks(); } }, "ⓘ") : null;
    rows.push(el("tr", { title: [expected, note].filter(Boolean).join("\n") },
      el("td", { class: "ck-label" }, t(c.label), info,
        CK.open.has(key) ? el("div", { class: "muted ck-note" }, c.expected ? el("div", { class: "st-exp" }, expected) : null, note) : null),
      el("td", { class: "mono ck-val" }, fmtVal(c.value, c.unit), el("div", { class: "muted" }, c.ref === null || c.ref === undefined ? "" : t("reference {value}", { value: fmtVal(c.ref, c.unit) }))),
      el("td", { class: "ck-st" }, el("span", { class: mark[0], title: mark[2] }, mark[1]))));
  }
  return rows;
}

// a unit of seconds: a T "s", the plain "s", or "с" of the records before the i18n
const SECONDS = new Set(["s", "\u0441"]);  // i18n-ok: «с» of the records made before the translation
function fmtVal(v, unit) {
  if (v === null || v === undefined) return "—";
  if (typeof v !== "number") return t(v);
  if ((unit && unit.$t === "s" && !unit.a) || SECONDS.has(unit)) return time(v, 12);
  return num(v, 12) + (unit ? " " + t(unit) : "");
}

// "Events": rebuilt only when its list changed, rows appended, the "future" marks toggled in place — a row stays under the
// pointer between frames, so a click on it works while the world records (review UX-ui U14). Before any world it lists
// why the run has none (P1). An error's detail (the exception's own text) is folded under "details" (P4).
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);  // a text shown on its own starts with a capital
function eventRow(e) {
  const det = e.detail ? el("details", { class: "ev-detail", onclick: (x) => x.stopPropagation() },
    el("summary", {}, t("details")), el("div", { class: "mono" }, e.detail)) : null;
  return el("div", { class: "ev" + (e.kind === "error" ? " err" : ""), title: t("go to this moment"),
    onclick: () => jumpToTime(e.t) }, el("span", { class: "t mono" }, time(e.t, 7)), e.kind === "error" ? "⚠ " : "", cap(t(e.text)) || e.kind, det);
}
function renderEvents() {
  const tt = currentT(), box = S.eventsBox;
  const list = S.worlds.length ? S.events : S.runNotes;
  const from = Math.max(0, list.length - 400);
  const atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 30;
  const D = S.evDrawn;
  if (!D || D.list !== list || D.from !== from || D.n > list.length) {  // a new list (another world), or trimmed
    if (!list.length) box.replaceChildren(el("div", { class: "muted" }, t("No events yet")));
    else box.replaceChildren(...list.slice(from).map(eventRow));
    S.evDrawn = { list, from, n: list.length, fut: -1 };
  } else if (D.n < list.length) {  // new events: appended
    if (D.n === 0) box.replaceChildren();
    box.append(...list.slice(D.n).map(eventRow));
    D.n = list.length; D.fut = -1;
  }
  // the first event after the cursor: rows from it on are marked "future" (toggled only where it changed)
  const eps = 1e-15 * Math.abs(tt);
  let fut = list.length;
  for (let i = from; i < list.length; i++) if (list[i].t > tt + eps) { fut = i; break; }
  if (S.evDrawn.fut !== fut) {
    const rows = box.children;
    for (let i = 0; i < rows.length; i++) rows[i].classList.toggle("future", from + i >= fut);
    S.evDrawn.fut = fut;
  }
  if (atBottom && D && D.n !== undefined) box.scrollTop = box.scrollHeight;
}

function jumpToTime(tt) {
  if (!S.frames.length) return;
  let lo = 0, hi = S.frames.length - 1;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (S.frames[mid].t < tt) lo = mid + 1; else hi = mid; }
  goTo(lo);
}
function goTo(i) {  // move the cursor (stops the history's playback); at the end it follows a recording
  S.hist = 0;
  S.idx = Math.max(0, Math.min(i, S.frames.length - 1));
  S.live = atEnd();
  S.dirty = true; updateTransport();
}

// --- playing the history: the cursor moves through the recorded frames at the chosen speed ----------------------
function playHistory(dir) {
  if (!S.frames.length) return;
  if (S.hist === dir) { S.hist = 0; updateTransport(); return; }  // the same button again: pause
  if (dir > 0 && atEnd()) { S.hist = 0; S.live = true; updateTransport(); return; }  // nothing ahead in the record
  if (dir < 0 && S.idx <= 0) return;
  S.hist = dir; S.live = false; S.histT = currentT(); S.histWall = performance.now();
  updateTransport();
}
function advanceHistory() {
  const now = performance.now(), dt = Math.min(0.25, (now - S.histWall) / 1000);
  S.histWall = now;
  if (!S.frames.length) { S.hist = 0; return; }
  S.histT += S.hist * S.speed * dt;
  const last = S.frames.length - 1;
  if (S.hist > 0 && S.histT >= S.frames[last].t) { S.idx = last; S.hist = 0; S.live = true; updateTransport(); }
  else if (S.hist < 0 && S.histT <= S.frames[0].t) { S.idx = 0; S.hist = 0; updateTransport(); }
  else S.idx = frameIndexAt(S.histT);
  S.dirty = true;
}

// ⏺: compute further (recording); again: pause. With the cursor at the end, the recording is shown live; elsewhere
// the cursor stays and the history grows behind it. A suspended run is resumed by the server (rebuilt by replay).
function toggleRecord() {
  if (S.startError && (!S.worlds.length || S.ended)) { toast(S.startError + "\n" + t("Change the parameters in the catalogue and start again."), "error", 12000); return; }
  if (S.ended) { toast(t("This is an old record: it cannot be resumed — start a new world (on the left) or a new run"), "notice", 5000); return; }
  if (archived()) { toast(t("This is an earlier world from the record: only the current world can be recorded"), "notice", 4000); return; }
  if (S.pending === "resume") return;  // the world is being rebuilt: the recording starts by itself
  if (S.playing) { send("pause"); return; }
  if (atEnd() || !S.frames.length) { S.live = true; S.hist = 0; }
  send("play");
}

// --- transport ------------------------------------------------------------------------------------
function speedToSlider(v) {
  const [lo, hi] = S.speedRange;
  return Math.round(1000 * (Math.log10(v) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo)));
}
function sliderToSpeed(x) {
  const [lo, hi] = S.speedRange;
  const e = Math.log10(lo) + (x / 1000) * (Math.log10(hi) - Math.log10(lo));
  const v = 10 ** e;
  const p = 10 ** Math.floor(Math.log10(v));
  return Math.round(v / p * 10) / 10 * p;  // two significant digits
}

function bindTransport() {
  $("rec").onclick = toggleRecord;
  $("tostart").onclick = () => goTo(0);
  $("toend").onclick = () => goTo(S.frames.length - 1);
  $("back").onclick = () => playHistory(-1);
  $("fwd").onclick = () => playHistory(+1);
  $("step").onclick = () => {  // a frame forward in the history; at its end, compute one step
    if (!atEnd()) { goTo(S.idx + 1); return; }
    if (S.ended || archived() || S.pending === "resume") return;
    send("step");
  };
  $("next").onclick = () => {  // the next recorded event; past the last one, compute up to the next event
    const tt = currentT(), ev = S.events.find((e) => e.t > tt + 1e-12 * Math.abs(tt));
    if (ev && !atEnd()) { jumpToTime(ev.t); return; }
    if (S.ended || archived() || S.pending === "resume") return;
    goTo(S.frames.length - 1);
    send("next_event");
  };
  // a recording's speed is the player's own (nothing computes): changed here only
  $("rt").onclick = () => { if (S.recording) { S.speed = 1; S.histT = currentT(); updateTransport(); } else send("speed", { value: 1 }); };
  $("speed").oninput = () => { $("speedv").textContent = speedLabel(sliderToSpeed(Number($("speed").value))); };
  $("speed").onchange = () => { S.speed = sliderToSpeed(Number($("speed").value)); if (S.recording) updateTransport(); else send("speed", { value: S.speed }); };
  $("timeline").oninput = () => goTo(Number($("timeline").value));
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" && e.target.type !== "range" || e.target.tagName === "SELECT") return;
    // a focused slider (the timeline, the speed) takes its own keys; ← also played the history back (review C1, c08 (b))
    if (e.target.type === "range" && ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", "PageUp", "PageDown"].includes(e.key)) return;
    if (e.key === " ") { e.preventDefault(); if (S.recording) playHistory(+1); else toggleRecord(); }
    else if (e.key === "ArrowRight") { e.preventDefault(); playHistory(+1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); playHistory(-1); }
    else if (e.key === "Home") { e.preventDefault(); goTo(0); }
    else if (e.key === "End") { e.preventDefault(); goTo(S.frames.length - 1); }
    // by the key's place (e.code), so that the keys work in any keyboard layout (the Russian one too)
    else if (e.code === "KeyN" || e.key === "n" || e.key === "N") $("next").click();
    else if (e.code === "KeyT" || e.key === "t" || e.key === "T") toggleTheme();
    else if (e.key === "?") showHelp();
    else if (e.code === "BracketLeft" || e.key === "[") S.fold("left", !$("app").classList.contains("fold-left"));
    else if (e.code === "BracketRight" || e.key === "]") S.fold("right", !$("app").classList.contains("fold-right"));
  });
  window.addEventListener("themechange", () => { S.dirty = true; });
  window.addEventListener("resize", renderSpeedTicks);
}

function speedLabel(v) { return time(v, 3) + " / " + t("s"); }

// the slider's scale: round units of time inside the world's speed range, thinned to fit (review of the owner's
// note 2026-10-28: «расширить ... обозначения с логарифмической шкалой ... от долей секунд до X лет»)
const YEAR = 365.25 * 86400;
const SPEED_TICKS = [[1e-15, t("1 fs")], [1e-12, t("1 ps")], [1e-9, t("1 ns")], [1e-6, t("1 µs")], [1e-3, t("1 ms")], [1, t("1 s")],
  [60, t("1 min")], [3600, t("1 h")], [86400, t("1 day")], [YEAR, t("1 yr")], [100 * YEAR, t("100 yr")], [1e4 * YEAR, t("10⁴ yr")],
  [1e6 * YEAR, t("10⁶ yr")], [1e9 * YEAR, t("10⁹ yr")]];
function supExp(n) { return String(n).replace(/-/g, "⁻").replace(/\d/g, (d) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[d]); }
function renderSpeedTicks() {
  const box = $("speedticks"), W = box.clientWidth;
  if (!W) return;
  const [lo, hi] = S.speedRange, thumb = 8, l0 = Math.log10(lo), l1 = Math.log10(hi);
  const at = (v) => thumb + (Math.log10(v) - l0) / (l1 - l0) * (W - 2 * thumb);
  // round units first (1 s, 1 year, 1 ms, 1 day ... by priority), each kept if it clears the ones kept by 34 px; a
  // narrow range with fewer than three of them is marked by powers of ten of a second instead
  const prio = [1, 365.25 * 86400, 1e-3, 86400, 1e-6, 3600, 1e-9, 60, 100 * 365.25 * 86400, 1e-12, 1e4 * 365.25 * 86400,
                1e6 * 365.25 * 86400, 1e-15, 1e9 * 365.25 * 86400];
  let cand = prio.map((v) => SPEED_TICKS.find((tt) => Math.abs(tt[0] / v - 1) < 1e-9)).filter((tt) => tt && tt[0] >= lo * 0.999 && tt[0] <= hi * 1.001);
  if (cand.length < 3) {
    cand = [];
    for (let e = Math.ceil(l0 - 1e-9); e <= Math.floor(l1 + 1e-9); e++) cand.push([10 ** e, e === 0 ? t("1 s") : `10${supExp(e)} ${t("s")}`]);
  }
  const kept = [];
  for (const tt of cand) { const x = at(tt[0]); if (kept.every((k) => Math.abs(k.x - x) >= 34)) kept.push({ x, label: tt[1] }); }
  kept.sort((a, b) => a.x - b.x);
  box.replaceChildren(...kept.map((k) => el("span", { style: { left: `${k.x}px` } }, k.label)));
}
// the speed the world actually reaches (measured by the server over the last 1.5 s of play): shown when the
// computation cannot keep up with the chosen speed
function updateRate(meta) {
  const box = $("speedfact");
  const r = meta && meta.speed_actual;
  if (!S.playing || r === null || r === undefined || r >= 0.97 * S.speed) { box.textContent = ""; box.title = ""; return; }
  box.textContent = t("actual: {speed}", { speed: `${time(r, 2)} / ${t("s")}` });
  box.title = t("The computation cannot keep up with the chosen speed: the world runs {k:.2g} times slower. The time on the clock and in the events is always the world's time; lower the speed to match the actual one.", { k: S.speed / Math.max(r, 1e-300) });
}

function updateTransport() {
  const noRec = S.ended || archived(), rebuild = S.pending === "resume";
  $("rec").disabled = noRec || rebuild;
  $("rec").classList.toggle("on", (S.playing || rebuild) && !noRec);
  $("rec").textContent = (S.playing || rebuild) && !noRec ? t("⏸ recording") : "⏺";
  $("rec").title = rebuild ? t("The world is being restored; the recording resumes by itself") : S.playing ? t("Pause the recording (Space)") : S.suspended
    ? t("Resume: the world is restored from its saved state and continues (Space)")
    : t("Record: the world is computed further, frames are added to the history (Space)");
  $("fwd").textContent = S.hist > 0 ? "⏸" : "▶";
  $("back").textContent = S.hist < 0 ? "⏸" : "◀";
  $("fwd").classList.toggle("on", S.hist > 0);
  $("back").classList.toggle("on", S.hist < 0);
  for (const b of ["rt", "speed"]) $(b).disabled = false;
  $("speed").value = speedToSlider(S.speed);
  $("speedv").textContent = speedLabel(S.speed);
  const where = !S.frames.length ? "" : " · " + (atEnd() ? (S.playing && !archived() ? t("live") : t("end of the record")) : t("history"));
  $("status").title = S.resumeError ? t("Resuming failed: {why}", { why: S.resumeError }) : S.startError ? S.startError : "";
  if (S.replaying) { if (!S.recording) setStatus("", t("loading the record…")); }  // the record's own states are not the run's
  else if (S.recording) setStatus(S.hist ? "live" : "paused", S.hist ? t("playing the recording") : atEnd() ? t("a recording · at its end") : t("a recording · paused"));
  else if (archived()) setStatus("", t("a world from the record") + where);
  else if (S.startError && (!S.worlds.length || S.ended)) setStatus("dead", t("world not created — the reason is in “Events”"));  // P1, P3
  else if (S.ended) setStatus("", t("an old record — it cannot be resumed") + where);
  else if (rebuild) setStatus("paused", t("the world is being restored — the recording resumes by itself") + where);
  else if (S.playing) setStatus("live", t("recording") + where);
  else if (S.suspended && S.resumeError) setStatus("dead", t("resuming failed — ⏺ tries again") + where);
  else if (S.suspended) setStatus("paused", t("suspended — ⏺ resumes") + where);
  else setStatus("paused", t("paused") + where);
  const ek = editBlock();  // the views' editable state (slice planes) follows the cursor and the run's state
  if (ek !== S.editKey) {
    S.editKey = ek;
    window.dispatchEvent(new Event("editablechange"));
    if (curWorld()) { refreshLive(); renderAtCursor(curWorld()); }
  }
}

function updateTimeline() {
  const tl = $("timeline");
  tl.max = Math.max(0, S.frames.length - 1);
  tl.value = Math.max(0, S.idx);
}

function setStatus(cls, text) { $("status").replaceChildren(el("span", { class: "dot " + cls }), text); }

function showHelp() {
  modal(el("div", {},
    el("h3", {}, S.viz ? t(S.viz.title) : t("Player")),
    S.header && S.header.text ? el("p", {}, t(S.header.text)) : null,
    S.view && S.view.help ? S.view.help() : null,
    el("h4", {}, t("Player")),
    el("p", {}, t("⏺ records: the world is computed further and its frames are added to the history; press again to pause. ⏮ and ⏭ go to the start and the end of the history, ◀ and ▶ play the history backwards and forwards at the chosen speed (world seconds per second; “1:1” is real time). With the slider at the end of the history the recording is shown live; in the middle the history grows on while the chosen moment is shown. “|▶” is a frame forward (at the end, one step of computation), “⏭ event” goes to the next event (past the last one, it computes up to it).")),
    el("p", {}, t("Everything shown is as of the slider's moment: the scene, the trajectories, the screen, the checks, the set-up and the events. The set-up can be changed and actions done only at the end of the history.")),
    el("p", {}, t("There is no stop: a run nobody watches pauses by itself and after half an hour frees its worker; ⏺ continues it from the world's saved state as one record (without one, by recomputing the world along the record from its start). Going back through the history, the player starts from the nearest key frame, not from the start of the record. Runs nobody has opened for a long time are removed (except those marked ★); the period is set in the catalogue, 3 days by default.")),
    el("p", {}, t("“Set-up — changes at once”: everything an experimenter can change during the experiment (the source, the slits, the screen, the observer…). A change applies when you release the slider, choose an item of a list or press Enter in a number field. If a change is not possible, the field goes back to its previous value and a message appears.")),
    el("p", {}, t("“Actions” are one-off events (a flash, an acceleration, a measurement). Their consequences spread from that moment.")),
    el("p", {}, t("“▶ Start a new world” starts a world with other laws or initial conditions in this same run; the earlier worlds stay in the record and can be viewed with the world switch at the top.")),
    el("p", {}, t("The scale at the bottom is the current world's history. A click on an event in the log takes you to its moment.")),
    el("p", {}, t("If the world takes long to compute a change (the scene, the set-up, a new world), the top bar shows what it is and for how many seconds; “✕ cancel” takes the world back to the moment before that change. ⇤ and ⇥ at the top (keys [ and ]) hide the side columns to give the picture more room.")),
    el("p", { class: "muted" }, t("Keys: Space — record/pause, ← and → — play the history backwards/forwards, Home and End — to the start and the end, N — to the next event, [ and ] — hide the columns, T — theme, ? — help."))));
}

main();
