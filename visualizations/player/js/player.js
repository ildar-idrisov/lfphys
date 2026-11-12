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
// and can be looked at with the «Мир» switch in the top bar).
//
// Transport (owner, 2026-10-28): ⏺ records — the world is computed further and its frames are added to the history;
// ⏮ ◀ ▶ ⏭ and the timeline move along the history. Whatever the cursor points at is shown exactly as it was then:
// the view is fed the record's messages up to that time and rebuilt from the record when the cursor goes back
// (syncView). With the cursor at the end, recording is shown live. There is no stop: a run idle without viewers is
// suspended by the server and resumed (rebuilt from its record) when ⏺ is pressed again.
import { connectRun, getJSON, postJSON } from "./api.js";
import { control, el, fill, initTheme, modal, num, panel, paramForm, time, toast, toggleTheme } from "./ui.js";

initTheme();
const $ = (id) => document.getElementById(id);
const runId = new URLSearchParams(location.search).get("id");
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
};

const curWorld = () => S.worlds[S.w];
const latest = () => S.worlds.length - 1;
const archived = () => S.w !== latest();
const liveParams = () => S.viz.schema.params.filter((p) => p.live);

async function main() {
  if (!runId) { document.body.replaceChildren(el("div", { class: "page" }, "Не указан запуск: /run?id=…")); return; }
  try {
    S.meta = await getJSON(`/api/runs/${encodeURIComponent(runId)}`);
    S.viz = await getJSON(`/api/viz/${encodeURIComponent(S.meta.viz)}`);
  } catch (e) { document.body.replaceChildren(el("div", { class: "page" }, "Запуск не найден: " + e.message)); return; }
  document.title = `${S.viz.title} · ${runId}`;
  $("title").textContent = S.viz.title;
  $("runid").textContent = runId;
  $("keep").textContent = S.meta.keep ? "★" : "☆";
  const mod = await import(`/viz/${S.meta.viz}/view.js`);
  const ctx = {
    action: (name, args) => sendAction(name, args),
    send: (cmd, args) => send(cmd, args),
    set: (values) => sendSet(values),
    liveControl: (id, opts) => boundControl(id, opts),
    setScene: (text) => { $("scene").textContent = text || ""; },
    requestRender, time, num,
    jumpTo: (t) => jumpToTime(t),
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
  S.conn = connectRun(runId, { onOpen: reset, onMessage: onMessage, onClose: () => setStatus("dead", "связь оборвалась — переподключение…") });
  requestAnimationFrame(loop);
}

// --- layout ---------------------------------------------------------------------------------------
function layout() {
  S.banner = el("div", { class: "banner", style: { display: "none" } });
  S.liveBox = el("div", {});
  S.actionsBox = el("div", {}, el("div", { class: "muted" }, "ждём запуск…"));
  S.worldBox = el("div", {});
  const left = $("left"), right = $("right");
  const pg = S.viz.kind === "playground";
  left.replaceChildren(S.banner);
  if (liveParams().length) {  // a playground's live laws too (integrator, 2026-11-05)
    left.append(panel(pg ? "Законы мира — меняются сразу" : "Установка — меняется сразу", el("div", {},
      el("div", { class: "help" }, pg ? "Изменение применяется сразу, в текущий момент мира, к уже идущей сцене; остальные законы — в «Новый мир»."
        : "Любое изменение применяется сразу, в текущий момент мира, и начинает новый отрезок опыта. Кнопки «применить» нет."),
      S.liveBox)));
  }
  // «Действия» only when the world has actions at the cursor (review UX-ui U23: an empty panel came first)
  S.actionsPanel = panel("Действия", el("div", {}, el("div", { class: "help" }, "Совершаются в текущий момент мира; следствия распространяются от этого события."), S.actionsBox));
  left.append(
    S.actionsPanel,
    ...(S.view.leftPanels || []),
    panel(liveParams().length ? "Новый мир: законы и начальные условия" : "Новый мир: сценарий, законы, начальные условия", S.worldBox,
      { closed: liveParams().length > 0 || pg }),  // a playground's scene is built in this world: closed (U23)
  );
  S.checksBox = el("div", { class: "checks" });
  S.eventsBox = el("div", { class: "events" });
  S.infoBox = el("div", {});
  S.engineBox = el("div", { class: "engine" });
  S.enginePanel = panel("Физика этого мира", S.engineBox, { closed: true });
  right.replaceChildren(
    panel("Проверки: вычислено ↔ эталон", el("div", {}, el("div", { class: "help" }, "Слева — величина, вычисленная в этом запуске из его событий; справа — замкнутая формула общепринятой физики (или объявленной модификации). ✓ — совпадение в пределах численной точности."), S.checksBox)),
    S.enginePanel,
    ...(S.view.rightPanels || []),
    panel("События", S.eventsBox),
    panel("О запуске", S.infoBox, { closed: true }),
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
    const r = await postJSON(`/api/runs/${runId}/keep`, { keep: !S.meta.keep });
    S.meta.keep = r.keep; $("keep").textContent = r.keep ? "★" : "☆";
  };
}

// --- live parameters: the set-up, applied at once ---------------------------------------------------
function liveValues() {  // the live set-up in force at the time shown (the latest when the cursor is at the end)
  const W = curWorld();
  if (!W) return {};
  if (atEnd()) return { ...(W.header.params || {}), ...W.live };
  const t = currentT();
  let v = {};
  for (const h of W.liveHist) { if (h.t <= t + 1e-12 * Math.abs(t)) v = h.values; else break; }
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
    if (!groups.has(p.group)) groups.set(p.group, []);
    groups.get(p.group).push(p);
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
    S.sent = { cmd, what: SCENE_WHAT[(args || {}).op] || "сцена меняется", since: performance.now() };
    renderBusy();
  }
}
const SCENE_WHAT = { add: "сцена: добавляется объект", remove: "сцена: удаляется объект", set: "сцена: меняется объект",
  edit: "сцена: перемещается объект", duplicate: "сцена: копируется объект", label: "сцена: переименовывается объект",
  clear: "сцена: очищается" };

// what the world computes now: the local pending state, or the worker's own notice with the time it has taken and a
// way out (✕: the command is cancelled, the world goes back to just before it; review UX-ui U9)
let busyTimer = null, busyEls = null;
function renderBusy() {
  const b = S.busy || S.sent, box = $("busy");
  const local = S.pending === "world" ? "создаётся новый мир…" : S.pending === "set" ? "перестраивается установка…"
    : S.pending === "resume" ? "продолжение: мир восстанавливается…" : "";
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
  const text = b ? b.what || "мир считает" : local;
  // the text and the button are kept and updated in place: a click on ✕ must not meet a rebuilt button (cf. U14)
  if (!busyEls) {
    busyEls = { text: el("span", {}), cancel: el("button", { class: "cancel", title: "Отменить: мир вернётся в момент перед этим изменением (оно не применится)", onclick: cancelBusy }, "✕ отменить") };
  }
  if (busyEls.text.parentNode !== box) box.replaceChildren(busyEls.text, busyEls.cancel);
  const t = text + (secs >= 1 ? ` · ${Math.floor(secs)} с` : "…");
  if (busyEls.text.textContent !== t) busyEls.text.textContent = t;
  busyEls.cancel.style.display = S.busy && S.busy.cmd !== "build" && secs >= 1 ? "" : "none";
  box.title = S.busy ? "Мир считает; кадры и другие команды ждут. «✕ отменить» вернёт мир в момент перед этим изменением." : "";
  if (!busyTimer) busyTimer = setInterval(renderBusy, 250);
}
async function cancelBusy() {
  if (!S.busy) return;
  try {
    const r = await fetch(`/api/runs/${encodeURIComponent(runId)}/cancel`, { method: "POST" });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) toast(j.error || r.statusText, "notice", 5000);
  } catch (e) { toast("Отмена: " + e.message); }
}

function editBlock() {
  if (archived()) return "Это мир из записи: ни срезы, ни сцену в нём менять нельзя.";
  if (S.ended) return "Это старая запись: менять нельзя.";
  if (!atEnd()) return "Вы смотрите прошлое опыта: срезы и сцену меняют в конце записи (⏭).";
  if (S.pending === "resume") return "Мир восстанавливается: срезы и сцену — когда запись продолжится.";
  return "";
}

function sendSet(values, ctl) {
  if (S.ended || archived()) { toast("Это запись: изменить уже нельзя", "notice", 3000); refreshLive(); return; }
  if (!atEnd()) { toast("Вы смотрите прошлое опыта: установку можно менять в конце записи (⏭)", "notice", 4000); refreshLive(); return; }
  if (S.pending === "resume") { toast("Мир восстанавливается: установку можно менять, когда запись продолжится", "notice", 4000); refreshLive(); return; }
  send("set", { values });
  if (ctl) ctl.pending(true);
  if (S.pending !== "resume") setPending("set");
}

function sendAction(name, args) {
  if (S.ended || archived()) { toast("Это запись: действия недоступны", "notice", 3000); return; }
  if (!atEnd()) { toast("Вы смотрите прошлое опыта: действия — в конце записи (⏭)", "notice", 4000); return; }
  if (S.pending === "resume") { toast("Мир восстанавливается: действия — когда запись продолжится", "notice", 4000); return; }
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
  if (!actions || !actions.length) { box.append(el("div", { class: "muted" }, "Нет действий")); return; }
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
        el("div", { class: "btnrow" }, arg.options.map((o) => el("button", { disabled: off, title: `${a.label}: ${o.label}`,
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
      el("button", { class: "primary", disabled: off, onclick: () => sendAction(a.name, { ...vals }) }, "▶ " + (a.button || a.label))));
  }
}

// --- a new world inside this run ---------------------------------------------------------------------
function renderWorldPanel() {
  const W = curWorld();
  if (!W) return;
  const params = W.header.params || {};
  // every law of the new world is in the form (review LB1-p02-ux X3: a world of the other dimension needs its own grid
  // and window, which are live laws): those that change also on the go start at their values in this world now and
  // are marked so; one form, so that a law shown only for some values of another (the grid of the space) appears
  const live = curWorld().live || {};
  const values = { ...params, ...live };
  let preset = "";
  const schema = { ...S.viz.schema, params: S.viz.schema.params.map((p) => (p.live ? { ...p, group: `${p.group || "Законы"} — меняются и на ходу (сейчас как в этом мире)` } : p)) };
  const form = paramForm(schema, values, {});
  const presetSel = el("select", {}, el("option", { value: "" }, "— установка как сейчас —"),
    S.viz.schema.presets.map((p) => el("option", { value: p.id }, p.label)));
  const note = el("div", { class: "help" });
  const seed = el("input", { type: "text", placeholder: `затравка (сейчас ${W.header.seed})`, style: { width: "100%" } });
  const playground = !!W.header.playground;
  // a playground's scene carried into the new world (plan P16.1): on by default; a scenario brings its own scene
  const carry = el("input", { type: "checkbox", checked: true });
  const carryRow = playground ? el("label", { class: "ctl pg-carry", title: "Объекты текущей сцены переходят в новый мир. Их состояние (положения, скорости, поле) идёт с ними там, где раздел умеет его перенести; сообщение после переноса скажет, что перенесено с состоянием, что начато заново из параметров, что изменено и что новый мир не принял" },
    carry, " перенести сцену") : null;
  const showNote = () => {
    const pr = S.viz.schema.presets.find((x) => x.id === preset);
    if (carryRow) { carry.disabled = !!preset; carryRow.classList.toggle("muted", !!preset); }
    note.textContent = preset
      ? "Новый мир начнётся из сценария «" + presetSel.selectedOptions[0].textContent + "» с законами из формы ниже."
        + (pr && pr.note ? " " + pr.note : "")  // what the scenario shows, e.g. a check that fails on purpose (P23)
      : playground ? (carry.checked
        ? "Новый мир начнётся с законами из формы ниже, со сценой этого мира в его текущий момент. Сообщение после переноса скажет, что перенесено с состоянием, что начато заново из параметров (если раздел не умеет перенести состояние), что изменено и что новый мир не принял."
        : "Новый мир начнётся с пустой сцены с законами из формы ниже (текущую сцену можно сохранить в «Сцена: файл» и загрузить).")
        : (liveParams().length ? "Установка (источник, щели, наблюдатель…) перейдёт в новый мир как сейчас; меняются законы и начальные условия из формы." : "");
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
    if (S.pending === "resume") { toast("Мир восстанавливается: новый мир — когда запись продолжится", "notice", 4000); return; }
    send("new_world", body);
    if (S.pending !== "resume") setPending("world");
  } }, "▶ Начать новый мир");
  showNote();
  fill(S.worldBox,
    el("div", { class: "help" }, "Законы и начальные условия нельзя изменить внутри идущего мира: история, посчитанная при других законах, — другая история. Новый мир начинается в этом же запуске; прежние остаются в записи (переключатель «Мир» вверху)."),
    el("div", { class: "ctl" }, el("label", {}, "Сценарий"), presetSel), carryRow, note,
    form.el,
    el("div", { class: "ctl" }, el("label", {}, "Затравка случайных чисел"), seed),
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
  for (const n of ((meta.backend || {}).notes || [])) W.events.push({ t: meta.t || 0, kind: "notice", text: "ℹ устройства: " + n });
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
  $("scene").textContent = W.header.title || "";
  renderAtCursor(W);
  renderLive();
  renderWorldPanel();
  renderInfo();
  renderWorldSelect();
  S.banner.style.display = archived() ? "" : "none";
  S.banner.replaceChildren("Вы смотрите мир ", String(W.n), " из записи — менять его нельзя. ",
    el("button", { onclick: () => showWorld(latest()) }, "к текущему миру"));
  S.checksDirty = S.eventsDirty = S.dirty = true;
  updateTransport();
}

// --- the view at the time shown: fed the record's messages up to it; when going back, restored from its nearest key
// frame (a view with snapshot() / restore()) or rebuilt from the record (a view without) --------------------------------
function rebuildView(W, t) {
  const k = S.viewOwner === W && S.view.restore ? keyBefore(W, t) : null;
  const t0 = performance.now();
  if (k) {
    try {
      S.view.restore(k.snap);
      const L = W.viewMsgs;
      for (let i = k.i; i < L.length; i++) L[i].on = false;
      W.prefix = W.nOn = W.scan = k.i; W.maxOn = k.maxOn;
      feedView(W, t);
      DBG.fromKey++; DBG.lastMs = performance.now() - t0; DBG.lastFed = W.prefix - k.i;
      return;
    } catch (e) { console.error("key frame not restored, rebuilding from the record:", e); DBG.keyFailed++; }
  }
  S.view.reset && S.view.reset();
  S.view.onHeader(W.header, W.headerBlobs);
  S.viewOwner = W;
  for (const m of W.viewMsgs) m.on = false;
  W.maxOn = -Infinity; W.scan = 0; W.prefix = 0; W.nOn = 0; W.keys = []; W.keyStride = 1;
  feedView(W, t);
  DBG.full++; DBG.lastMs = performance.now() - t0; DBG.lastFed = W.prefix;
}
// for automated tests of the page: how the view was last brought to the cursor, and a rebuild from the record on demand
const DBG = { fromKey: 0, full: 0, keyFailed: 0, lastMs: 0, lastFed: 0, repeats: 0 };
window.__lfPlayer = {
  dbg: DBG, keys: () => (curWorld() ? curWorld().keys.length : 0), t: () => currentT(), frames: () => S.frames.length,
  goTo: (i) => goTo(i),
  rebuildFromRecord: () => { const W = curWorld(); S.viewOwner = null; rebuildView(W, currentT()); S.dirty = true; },
  redraw: () => { S.dirty = true; },
};
// the latest key frame at or before t that the view's present state contains (it holds the messages in order up to a
// later point; a key frame records how long its data were then)
function keyBefore(W, t) {
  if (W.nOn !== W.prefix) return null;  // the view holds messages out of order: only a rebuild is safe
  const eps = 1e-12 * Math.abs(t);
  for (let j = W.keys.length - 1; j >= 0; j--) {
    const k = W.keys[j];
    if (k.i <= W.prefix && k.maxOn <= t + eps) return k;
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
function feedView(W, t) {
  const L = W.viewMsgs, eps = 1e-12 * Math.abs(t), keyed = !!(S.view.snapshot && S.view.restore);
  let first = -1;
  for (let i = W.scan; i < L.length; i++) {
    const m = L[i];
    if (m.on) continue;
    const tm = m.meta.t ?? 0;
    if (tm <= t + eps) {
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
function syncView(t) {
  const W = curWorld();
  if (!W) return;
  if (W.maxOn > t + 1e-12 * Math.abs(t)) rebuildView(W, t);  // the view holds something from later
  else feedView(W, t);
}

// the latest value of a time-indexed list at or before t
function asOf(list, t) {
  const eps = 1e-12 * Math.abs(t);
  let v = list[0].v;
  for (const h of list) { if (h.t <= t + eps) v = h.v; else break; }
  return v;
}
function renderAtCursor(W) {  // the top bar's approximations, «Физика этого мира» and the actions, as of the cursor
  const t = currentT();
  renderPhysics(W.header.modifications || [], asOf(W.approxHist, t));
  renderEngine(asOf(W.engineHist, t));
  renderActions(asOf(W.actionsHist, t));
}

function renderWorldSelect() {
  const sel = $("world");
  sel.style.display = S.worlds.length > 1 ? "" : "none";
  sel.replaceChildren(...S.worlds.map((W, i) => el("option", { value: i },
    `Мир ${W.n}${i === latest() ? " (текущий)" : ""}: ${(W.header.title || "").replace(/^[^:]*:\s*/, "")}`)));
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
  setStatus("", "загрузка записи…");
}

function onMessage({ meta, blobs }) {
  window.lfInstruments?.message(meta, blobs, { t: currentT, w: () => S.w, n: () => S.worlds.length });  // [LB1 P16.3 instruments] the «Приборы» panel (instruments.js)
  if (meta.type === "header") { newWorld(meta, blobs); if (S.pending === "world") setPending(null); return; }
  if (meta.type === "state") {
    S.playing = meta.playing; S.speed = meta.speed; S.speedRange = meta.speed_range || S.speedRange;
    if (!S.replaying) {
      S.suspended = false; S.ended = false; S.resumeError = null;
      if (S.pending === "resume") setPending(null);
    }
    updateTransport(); renderSpeedTicks(); if (!S.playing) updateRate(null);
    if (meta.reason === "no_viewers" && !S.replaying) toast("Запуск был на паузе: не было зрителей", "notice", 4000);
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
    S.resumeError = meta.resume_error || null;
    S.startError = meta.start_error || null;  // the first world was refused: said in the status and «События» (P1)
    if (!meta.live) {  // nothing computes now: a suspended run goes on when ⏺ is pressed, an old record cannot
      S.playing = false; S.suspended = !!meta.resumable; S.ended = !meta.resumable;
      if (S.worlds.length) showWorld(S.w);
    } else if (meta.rebuilding) setPending("resume");  // opened while another tab's ⏺ rebuilds the world
    if (S.frames.length && S.live) S.idx = S.frames.length - 1;
    S.dirty = true; updateTransport();
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
    S.resumeError = meta.resume_error || null;
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
      S.runNotes.push({ t: meta.t || 0, kind: meta.type, text: (meta.type === "error" ? "" : "ℹ ") + meta.text, detail: meta.detail });
      if (meta.type === "error") { S.startError = meta.text; if (S.pending === "world") setPending(null); }
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
      W.events.push({ t: meta.t, kind: "notice", text: "ℹ " + meta.text });
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
  const t = shown && !follow ? currentT() : 0;
  if (F.length && F[F.length - 1].n % W.stride !== 0) F.pop();
  F.push(f);
  if (F.length > MAX_FRAMES) {
    W.stride *= 2;
    let j = 0;
    for (let i = 0; i < F.length; i++) if (F[i].n % W.stride === 0 || i === F.length - 1) F[j++] = F[i];
    F.length = j;
  }
  if (shown && !follow) S.idx = frameIndexAt(t);
}
function frameIndexAt(t) {  // the last frame at or before t
  const F = S.frames;
  let lo = 0, hi = F.length - 1;
  if (hi < 0) return -1;
  if (t <= F[0].t) return 0;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (F[mid].t <= t) lo = mid; else hi = mid - 1; }
  return lo;
}

const short = (t, n) => (String(t).length > n ? String(t).slice(0, n - 1) + "…" : String(t));
function renderPhysics(mods, approx) {
  const box = $("physics");
  box.replaceChildren(...[mods.length
    ? el("span", { class: "badge mod", title: "Модифицированная физика:\n" + mods.map((m) => `${m.label}: ${m.value} (общепринято: ${m.standard})`).join("\n") },
        "МОДИФ. ФИЗИКА: " + short(`${mods[0].label} = ${mods[0].value}`, 40) + (mods.length > 1 ? ` (+${mods.length - 1})` : ""))
    : el("span", { class: "badge std", title: "Все законы — общепринятые" }, "стандартная физика"),
    // approximations the world itself flags (owner, 2026-10-24: «помечать там, где это приближение»)
    (approx || []).length ? el("span", { class: "badge mod", title: approx.join("\n") },
      " ПРИБЛИЖЕНИЕ: " + (approx[0].length > 48 ? approx[0].slice(0, 46) + "…" : approx[0]) + (approx.length > 1 ? ` (+${approx.length - 1})` : "")) : null]
    .filter(Boolean));
}

// the engine modules this world's physics comes from: the core (established physics) and, outside it, the
// approximations, interpretations, models and alternatives (lfphys/LAYERS.md)
const KIND_RU = { approximation: "приближение", interpretation: "интерпретация", model: "модель", alternative: "альтернатива" };
function renderEngine(list) {
  list = list || [];
  const core = list.filter((d) => d.layer === "core"), th = list.filter((d) => d.layer === "theories");
  const rest = list.filter((d) => d.layer !== "core" && d.layer !== "theories");
  S.enginePanel.querySelector("h4").firstChild.textContent =
    list.length ? `Физика этого мира: ядро ${core.length} · вне ядра ${th.length}` : "Физика этого мира";
  const item = (d) => el("div", { class: "eng " + d.layer + (d.kind === "alternative" ? " alt" : "") },
    el("div", {}, el("b", {}, d.title || d.id), d.layer === "theories" ? el("span", { class: "badge" }, " " + (KIND_RU[d.kind] || d.kind)) : null),
    d.statement ? el("div", { class: "muted" }, d.statement) : null,
    d.validity ? el("div", { class: "muted" }, "Где верно: " + d.validity) : null,
    (d.conflicts || []).map((c) => el("div", { class: "conf" }, "⚠ " + c)),
    el("div", { class: "mono muted" }, "lfphys." + d.id));
  fill(S.engineBox,
    el("div", { class: "help" }, "Откуда физика этого мира: ядро движка lfphys — установленная и подтверждённая физика; вне ядра — широко используемые приближения, интерпретации и модели (у каждой названо, где она расходится с ядром) и альтернативы для опытов «что если»."),
    core.length ? el("h5", {}, "Ядро") : null, core.map(item),
    th.length ? el("h5", {}, "Вне ядра") : null, th.map(item),
    rest.length ? el("h5", {}, "Наборы законов и инструменты") : null, rest.map(item),
    list.length ? null : el("div", { class: "muted" }, "Визуализация не сообщила модули движка."));
}

function renderInfo() {
  const m = S.meta, h = S.header || {};
  // what was drawn and what was checked, per kernel (review B1-4: one record hid the precision of the drawing)
  const used = Object.entries((h.backend || {}).used || {});
  const dv = (u) => `${u.device === "gpu" ? "GPU" : "CPU"}, ${u.precision}`;
  const devText = used.length
    ? used.map(([k, u]) => `${k}: рисунок — ${u.drawn ? dv(u.drawn) : "—"}; проверки — ${u.check ? dv(u.check) : "—"}`).join("; ")
    : "все расчёты этого мира — на CPU (ядер с GPU-реализацией он не вызывал)";
  const over = (m.backend_settings || {}).override;
  const rows = [["Запуск", m.id], ["Визуализация", `${m.viz} (версия ${m.version})`], ["Код", m.code],
    ["Устройства", devText + (over ? " (выбор устройств задан для этого запуска)" : "")],
    ["Мир", `${(curWorld() || {}).n || 1} из ${S.worlds.length}`], ["Затравка", h.seed ?? m.seed],
    ["Создан", m.created], ["Сценарий", h.preset || m.preset || "свои параметры"], ["Python", m.python]];
  fill(S.infoBox,
    h.text ? el("p", {}, h.text) : null,
    el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, String(v ?? ""))])),
    el("p", {}, el("a", { href: `/api/runs/${runId}/stream` }, "Скачать запись (.lfrec)"), " · ", el("a", { href: `/api/runs/${runId}`, target: "_blank" }, "паспорт запуска (JSON)")));
}

// --- render loop ----------------------------------------------------------------------------------
function requestRender() { S.dirty = true; }

function loop() {
  if (S.hist) advanceHistory();
  // while the record is replayed on (re)connection nothing is drawn: every render redraws the whole scene, so the
  // intermediate states of a long record cost seconds (found while processing review C1); history_end draws once
  if (S.dirty && S.header && !S.replaying) {
    S.dirty = false;
    const f = S.frames[S.idx], t = currentT();
    syncView(t);
    if (f) {
      try { S.view.render(f.meta, f.t, f.blobs); } catch (e) { console.error(e); }
      $("time").textContent = "t = " + time(f.t, 9);
    }
    updateTimeline();
    S.eventsDirty = true;
    // what depends on the time shown: the check versions computed by then, the set-up in force, the actions, the
    // approximations and the engine modules in force, the controls' availability
    const W = curWorld(), eps = 1e-12 * Math.abs(t);
    const upTo = (list) => { let n = 0; for (const h of list) { if (h.t <= t + eps) n++; else break; } return n; };
    let nc = 0;
    for (const vs of S.checks.values()) for (const c of vs) { if ((c.t ?? 0) <= t + eps) nc++; else break; }
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
// «ⓘ» (and as the line's tooltip), groups with a summary that fold, the older groups folded away; what the owner opened
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
    const g = c.group || "Прочее";
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g).push(c);
  }
  const order = [...groups.entries()].map(([g, list]) => [g, list, Math.max(...list.map((c) => c._seq || 0))])
    .sort((a, b) => b[2] - a[2]);
  const RECENT = 4;
  const table = (entries, first) => el("table", {}, el("colgroup", {}, el("col", {}), el("col", { class: "c-val" }), el("col", { class: "c-st" })),
    entries.flatMap(([g, list], i) => checkRows(g, list, first && i === 0)));
  const recent = order.slice(0, RECENT), old = order.slice(RECENT);
  const older = old.length ? el("details", { class: "older" }, el("summary", {}, `Прежние группы проверок: ${old.length}`), table(old, false)) : "";
  if (older) { older.open = CK.older; older.addEventListener("toggle", () => { CK.older = older.open; }); }
  const sc = S.checksBox.scrollTop;
  S.checksBox.replaceChildren(
    order.length ? table(recent, true) : el("div", { class: "muted" }, "Пока ничего не посчитано: запустите запись (⏺)."), older);
  S.checksBox.scrollTop = sc;
}

function checkRows(g, list, newest) {
  const rows = [], st = list.slice(-40).map((c) => [c, checkState(c)]);
  const n = (k) => st.filter(([, x]) => x === k).length;
  const sum = [n("ok") ? `${n("ok")} ✓` : "", n("bad") ? `${n("bad")} ✗` : "", n("exp") ? `${n("exp")} ✗ ожид.` : "",
    n("info") ? `${n("info")} ≈` : "", n("na") ? `${n("na")} —` : ""].filter(Boolean).join(" · ");
  // a group is open when the owner opened it, else when it is the newest or has a failure
  const open = CK.groups.has(g) ? CK.groups.get(g) : (newest || n("bad") > 0);
  const head = el("tr", { class: "grp-row", title: open ? "Свернуть группу" : "Развернуть группу" },
    el("td", { class: "grp", colspan: 3 }, el("span", { class: "fold" }, open ? "▾ " : "▸ "), g,
      el("span", { class: "grp-sum" + (n("bad") ? " st-bad" : "") }, sum)));
  head.onclick = () => { CK.groups.set(g, !open); renderChecks(); };
  rows.push(head);
  if (!open) return rows;
  for (const [c, k] of st) {
    const mark = { ok: ["st-ok", "✓", c.note || "совпадение в пределах численной точности"],
      bad: ["st-bad", "✗", c.rel !== null && c.rel !== undefined ? `относительное отличие ${num(c.rel, 3)}, допуск ${num(c.tol || 1e-9, 2)}` : (c.note || "")],
      exp: ["st-exp", "✗", "Ожидаемо: " + c.expected],
      info: ["st-na", "≈", "Сравнение для сведения, не проверка"], na: ["st-na", "—", "Для этой величины нет замкнутого эталона"] }[k];
    const key = (c.group || "") + "|" + c.id;
    const hasNote = !!(c.note || c.expected);
    const info = hasNote ? el("button", { class: "ck-i", title: "Пояснение к проверке", onclick: (e) => {
      e.stopPropagation(); if (CK.open.has(key)) CK.open.delete(key); else CK.open.add(key); renderChecks(); } }, "ⓘ") : null;
    rows.push(el("tr", { title: [c.expected ? "Ожидаемо: " + c.expected : "", c.note || ""].filter(Boolean).join("\n") },
      el("td", { class: "ck-label" }, c.label, info,
        CK.open.has(key) ? el("div", { class: "muted ck-note" }, c.expected ? el("div", { class: "st-exp" }, "Ожидаемо: " + c.expected) : null, c.note || "") : null),
      el("td", { class: "mono ck-val" }, fmtVal(c.value, c.unit), el("div", { class: "muted" }, c.ref === null || c.ref === undefined ? "" : "эталон " + fmtVal(c.ref, c.unit))),
      el("td", { class: "ck-st" }, el("span", { class: mark[0], title: mark[2] }, mark[1]))));
  }
  return rows;
}

function fmtVal(v, unit) {
  if (v === null || v === undefined) return "—";
  if (unit === "с") return time(v, 12);
  return num(v, 12) + (unit ? " " + unit : "");
}

// «События»: rebuilt only when its list changed, rows appended, the «future» marks toggled in place — a row stays under the
// pointer between frames, so a click on it works while the world records (review UX-ui U14). Before any world it lists
// why the run has none (P1). An error's detail (the exception's own text) is folded under «подробности» (P4).
function eventRow(e) {
  const det = e.detail ? el("details", { class: "ev-detail", onclick: (x) => x.stopPropagation() },
    el("summary", {}, "подробности"), el("div", { class: "mono" }, e.detail)) : null;
  return el("div", { class: "ev" + (e.kind === "error" ? " err" : ""), title: "перейти к этому моменту",
    onclick: () => jumpToTime(e.t) }, el("span", { class: "t mono" }, time(e.t, 7)), e.kind === "error" ? "⚠ " : "", e.text || e.kind, det);
}
function renderEvents() {
  const t = currentT(), box = S.eventsBox;
  const list = S.worlds.length ? S.events : S.runNotes;
  const from = Math.max(0, list.length - 400);
  const atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 30;
  const D = S.evDrawn;
  if (!D || D.list !== list || D.from !== from || D.n > list.length) {  // a new list (another world), or trimmed
    if (!list.length) box.replaceChildren(el("div", { class: "muted" }, "Событий пока нет"));
    else box.replaceChildren(...list.slice(from).map(eventRow));
    S.evDrawn = { list, from, n: list.length, fut: -1 };
  } else if (D.n < list.length) {  // new events: appended
    if (D.n === 0) box.replaceChildren();
    box.append(...list.slice(D.n).map(eventRow));
    D.n = list.length; D.fut = -1;
  }
  // the first event after the cursor: rows from it on are marked «future» (toggled only where it changed)
  const eps = 1e-15 * Math.abs(t);
  let fut = list.length;
  for (let i = from; i < list.length; i++) if (list[i].t > t + eps) { fut = i; break; }
  if (S.evDrawn.fut !== fut) {
    const rows = box.children;
    for (let i = 0; i < rows.length; i++) rows[i].classList.toggle("future", from + i >= fut);
    S.evDrawn.fut = fut;
  }
  if (atBottom && D && D.n !== undefined) box.scrollTop = box.scrollHeight;
}

function jumpToTime(t) {
  if (!S.frames.length) return;
  let lo = 0, hi = S.frames.length - 1;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (S.frames[mid].t < t) lo = mid + 1; else hi = mid; }
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
  if (S.startError && (!S.worlds.length || S.ended)) { toast(S.startError + "\nИзмените параметры в каталоге и запустите снова.", "error", 12000); return; }
  if (S.ended) { toast("Это старая запись: продолжить её нельзя — начните новый мир (слева) или новый запуск", "notice", 5000); return; }
  if (archived()) { toast("Это прежний мир из записи: записывать можно только текущий мир", "notice", 4000); return; }
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
    const t = currentT(), ev = S.events.find((e) => e.t > t + 1e-12 * Math.abs(t));
    if (ev && !atEnd()) { jumpToTime(ev.t); return; }
    if (S.ended || archived() || S.pending === "resume") return;
    goTo(S.frames.length - 1);
    send("next_event");
  };
  $("rt").onclick = () => send("speed", { value: 1 });
  $("speed").oninput = () => { $("speedv").textContent = speedLabel(sliderToSpeed(Number($("speed").value))); };
  $("speed").onchange = () => { S.speed = sliderToSpeed(Number($("speed").value)); send("speed", { value: S.speed }); };
  $("timeline").oninput = () => goTo(Number($("timeline").value));
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" && e.target.type !== "range" || e.target.tagName === "SELECT") return;
    // a focused slider (the timeline, the speed) takes its own keys; ← also played the history back (review C1, c08 (b))
    if (e.target.type === "range" && ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", "PageUp", "PageDown"].includes(e.key)) return;
    if (e.key === " ") { e.preventDefault(); toggleRecord(); }
    else if (e.key === "ArrowRight") { e.preventDefault(); playHistory(+1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); playHistory(-1); }
    else if (e.key === "Home") { e.preventDefault(); goTo(0); }
    else if (e.key === "End") { e.preventDefault(); goTo(S.frames.length - 1); }
    else if (e.key === "n" || e.key === "N" || e.key === "т" || e.key === "Т") $("next").click();
    else if (e.key === "t" || e.key === "T" || e.key === "е" || e.key === "Е") toggleTheme();
    else if (e.key === "?") showHelp();
    else if (e.key === "[" || e.key === "х" || e.key === "Х") S.fold("left", !$("app").classList.contains("fold-left"));
    else if (e.key === "]" || e.key === "ъ" || e.key === "Ъ") S.fold("right", !$("app").classList.contains("fold-right"));
  });
  window.addEventListener("themechange", () => { S.dirty = true; });
  window.addEventListener("resize", renderSpeedTicks);
}

function speedLabel(v) { return time(v, 3) + " / с"; }

// the slider's scale: round units of time inside the world's speed range, thinned to fit (review of the owner's
// note 2026-10-28: «расширить ... обозначения с логарифмической шкалой ... от долей секунд до X лет»)
const YEAR = 365.25 * 86400;
const SPEED_TICKS = [[1e-15, "1 фс"], [1e-12, "1 пс"], [1e-9, "1 нс"], [1e-6, "1 мкс"], [1e-3, "1 мс"], [1, "1 с"],
  [60, "1 мин"], [3600, "1 ч"], [86400, "1 сут"], [YEAR, "1 год"], [100 * YEAR, "100 лет"], [1e4 * YEAR, "10⁴ лет"],
  [1e6 * YEAR, "10⁶ лет"], [1e9 * YEAR, "10⁹ лет"]];
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
  let cand = prio.map((v) => SPEED_TICKS.find((t) => Math.abs(t[0] / v - 1) < 1e-9)).filter((t) => t && t[0] >= lo * 0.999 && t[0] <= hi * 1.001);
  if (cand.length < 3) {
    cand = [];
    for (let e = Math.ceil(l0 - 1e-9); e <= Math.floor(l1 + 1e-9); e++) cand.push([10 ** e, e === 0 ? "1 с" : `10${supExp(e)} с`]);
  }
  const kept = [];
  for (const t of cand) { const x = at(t[0]); if (kept.every((k) => Math.abs(k.x - x) >= 34)) kept.push({ x, label: t[1] }); }
  kept.sort((a, b) => a.x - b.x);
  box.replaceChildren(...kept.map((k) => el("span", { style: { left: `${k.x}px` } }, k.label)));
}
// the speed the world actually reaches (measured by the server over the last 1.5 s of play): shown when the
// computation cannot keep up with the chosen speed
function updateRate(meta) {
  const box = $("speedfact");
  const r = meta && meta.speed_actual;
  if (!S.playing || r === null || r === undefined || r >= 0.97 * S.speed) { box.textContent = ""; box.title = ""; return; }
  box.textContent = `факт: ${time(r, 2)} / с`;
  box.title = `Счёт не успевает за выбранной скоростью: мир идёт в ${num(S.speed / Math.max(r, 1e-300), 2)} раза медленнее. ` +
    "Время на часах и в событиях — всегда время мира; уменьшите скорость, чтобы она совпала с фактической.";
}

function updateTransport() {
  const noRec = S.ended || archived(), rebuild = S.pending === "resume";
  $("rec").disabled = noRec || rebuild;
  $("rec").classList.toggle("on", (S.playing || rebuild) && !noRec);
  $("rec").textContent = (S.playing || rebuild) && !noRec ? "⏸ запись" : "⏺";
  $("rec").title = rebuild ? "Мир восстанавливается; запись продолжится сама" : S.playing ? "Пауза записи (Пробел)" : S.suspended
    ? "Продолжить: мир восстановится с сохранённого состояния и пойдёт дальше (Пробел)"
    : "Запись: мир считается дальше, к истории добавляются кадры (Пробел)";
  $("fwd").textContent = S.hist > 0 ? "⏸" : "▶";
  $("back").textContent = S.hist < 0 ? "⏸" : "◀";
  $("fwd").classList.toggle("on", S.hist > 0);
  $("back").classList.toggle("on", S.hist < 0);
  for (const b of ["rt", "speed"]) $(b).disabled = false;
  $("speed").value = speedToSlider(S.speed);
  $("speedv").textContent = speedLabel(S.speed);
  const where = !S.frames.length ? "" : atEnd() ? (S.playing && !archived() ? " · вживую" : " · конец записи") : " · история";
  $("status").title = S.resumeError ? "Продолжение не удалось: " + S.resumeError : S.startError ? S.startError : "";
  if (S.replaying) setStatus("", "загрузка записи…");  // the record's own states are not the run's
  else if (archived()) setStatus("", "мир из записи" + where);
  else if (S.startError && (!S.worlds.length || S.ended)) setStatus("dead", "мир не создан — причина в «Событиях»");  // P1, P3
  else if (S.ended) setStatus("", "старая запись — продолжить нельзя" + where);
  else if (rebuild) setStatus("paused", "мир восстанавливается — запись продолжится сама" + where);
  else if (S.playing) setStatus("live", "запись идёт" + where);
  else if (S.suspended && S.resumeError) setStatus("dead", "продолжение не удалось — ⏺ повторит" + where);
  else if (S.suspended) setStatus("paused", "приостановлен — ⏺ продолжит" + where);
  else setStatus("paused", "пауза" + where);
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
    el("h3", {}, S.viz ? S.viz.title : "Плеер"),
    S.header && S.header.text ? el("p", {}, S.header.text) : null,
    S.view && S.view.help ? S.view.help() : null,
    el("h4", {}, "Плеер"),
    el("p", {}, "⏺ — запись: мир считается дальше и кадры добавляются к истории; ещё раз — пауза. ⏮ и ⏭ — в начало и в конец истории, ◀ и ▶ — проиграть историю назад и вперёд с выбранной скоростью (секунд мира за секунду; «1:1» — реальное время). Если бегунок в конце истории, запись показывается вживую; если в середине — история растёт дальше, а показывается выбранный момент. «|▶» — кадр вперёд (в конце — один шаг расчёта), «⏭ событие» — к следующему событию (за последним — посчитать до него)."),
    el("p", {}, "Всё показанное — на момент бегунка: сцена, траектории, экран, проверки, установка и события. Менять установку и совершать действия можно только в конце истории."),
    el("p", {}, "Остановки нет: если запуск никто не смотрит, он сам встаёт на паузу, а через полчаса освобождает вычислитель; ⏺ продолжит его с сохранённого состояния мира, как одну запись (без него — пересчитав мир по записи от начала). Назад по истории плеер идёт от ближайшего ключевого кадра, а не от начала записи. Запуски, к которым долго не обращались, удаляются (кроме отмеченных ★); срок задаётся в каталоге, по умолчанию 3 дня."),
    el("p", {}, "«Установка — меняется сразу»: всё, что экспериментатор может поменять во время опыта (источник, щели, экран, наблюдатель…). Изменение применяется в момент, когда вы отпускаете ползунок, выбираете пункт списка или нажимаете Enter в поле числа. Если изменение невозможно, поле возвращается к прежнему значению и появляется сообщение."),
    el("p", {}, "«Действия» — разовые события (вспышка, разгон, измерение). Их следствия распространяются от этого момента."),
    el("p", {}, "«Новый мир» — другие законы или начальные условия. Он начинается в этом же запуске; прежние миры остаются в записи, их можно посмотреть переключателем «Мир» вверху."),
    el("p", {}, "Шкала внизу — история текущего мира. Клик по событию в журнале переносит к его моменту."),
    el("p", {}, "Если мир долго считает изменение (сцена, установка, новый мир), вверху видно, что именно и сколько секунд; «✕ отменить» вернёт мир в момент перед этим изменением. ⇤ и ⇥ вверху (клавиши [ и ]) прячут боковые колонки, чтобы картине было больше места."),
    el("p", { class: "muted" }, "Клавиши: Пробел — запись/пауза, ← и → — проиграть историю назад/вперёд, Home и End — в начало и в конец, N — к событию, [ и ] — скрыть колонки, T — тема, ? — справка.")));
}

main();
