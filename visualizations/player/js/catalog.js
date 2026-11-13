// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Catalogue page: two modes (owner, 2026-10-28) — the demonstrations (prepared visualizations: start a run) and the
// playground (research sandboxes by section of physics: start from a scenario, an empty scene or a scene file) —, and
// the runs (open, keep, delete). There is no stop (owner,
// 2026-10-28): a run computes or is paused; one left without viewers is suspended and resumed when opened and ⏺ pressed;
// runs not touched for the removal period are removed unless kept (★); the period (3 days by default) is set above the
// runs and kept on the server (owner, 2026-10-29).
import { getJSON, postJSON } from "./api.js";
import { fmtField, legacy, parseNum, t, withLang } from "./i18n.js";
import { el, initTheme, modal, num, numberInput, paramForm, time, toast, toggleTheme } from "./ui.js";

// a scene file is at most 900 000 characters (the server's limit for a JSON parameter, below the socket's message
// limit: review B6-F20)
async function sceneText(f) {
  const text = await f.text();
  if (text.length > 900000) throw new Error(t("the scene file is longer than {max:d} characters ({n:d})", { max: 900000, n: text.length }));
  return text;
}

initTheme();
document.getElementById("theme").onclick = toggleTheme;
document.getElementById("help").onclick = showHelp;
document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
  if (e.code === "KeyT" || e.key === "t" || e.key === "T") toggleTheme();  // by the key's place: any keyboard layout
  if (e.key === "?") showHelp();
});

let vizList = [];
let lastRuns = "";
let kernelInfo = null;  // the engine's kernels (from /api/devices), for the per-run device choice
let keepDays = 3;  // the removal period, as the server has it
let mode = (() => { try { return localStorage.getItem("lfviz.mode") || "demo"; } catch (e) { return "demo"; } })();
if (location.hash === "#playground") mode = "playground";
// sections of the playground planned later (lfphys/PLAN.md, P15): shown, not startable
const PLANNED = [[t("Optics and waves"), t("sources, slits, lenses, mirrors, gratings, screens (batch B9)")],
                 [t("Electricity and magnetism"), t("charges, currents, magnets, conductors; fields and radiation (batch B9)")],
                 [t("Relativity"), t("observers, clocks, rods, rockets: what each of them sees (batch B9)")]];

// "1 day", "3 days" (the plural forms of the language)
function days(n) { return t("{n:d} days", { n }); }

// the removal period: changed here, saved on the server; a period that would remove runs at once lists them first
async function loadRetention() {
  try { keepDays = (await getJSON("/api/settings/runs")).keep_days; } catch (e) { return; }
  const inp = numberInput(keepDays, { style: "width:5em",
                            title: t("After how many days without actions (a view, a command) a run is removed with its record") },
                          { int: true, step: 1, min: 1, max: 3650 });
  const note = el("span", { class: "muted" });
  inp.onchange = () => saveRetention(inp, note);
  document.getElementById("retention").replaceChildren(
    el("span", { class: "muted" }, t("Remove runs without actions after")), inp,
    el("span", { class: "muted" }, t("days (except those marked ★ and those open in a tab)")), note);
}

async function saveRetention(inp, note) {
  const pr = parseNum(inp.value);  // a decimal comma or point (review i18n-browser F1)
  const reset = () => { inp.value = fmtField(keepDays, true); };
  if (pr.err || !(pr.value >= 1 && pr.value <= 3650)) { toast(t("The period is a whole number of days from {lo:d} to {hi:d}", { lo: 1, hi: 3650 })); reset(); return; }
  const d = Math.round(pr.value);
  let r;
  try {
    r = await putRetention({ keep_days: d });
    if (r.would_remove) {
      if (!confirm(t("With a period of {days} these runs ({n:d}) are removed at once with their records:", { days: days(d), n: r.would_remove.length }) + "\n" +
                   `${r.would_remove.join("\n")}\n\n` + t("Remove them and save the period?"))) { reset(); return; }
      r = await putRetention({ keep_days: d, confirm: r.would_remove });
      if (r.would_remove) { toast(t("While you confirmed, the list of runs to remove changed — repeat")); reset(); return; }
    }
  } catch (e) { toast(t("Retention period: {why}", { why: e.message })); reset(); return; }
  keepDays = r.keep_days;
  note.textContent = r.removed.length ? t("saved; runs removed: {n:d}", { n: r.removed.length }) : t("saved");
  setTimeout(() => { note.textContent = ""; }, 4000);
  lastRuns = ""; loadRuns();
}

// PUT /api/settings/runs; 409 (the period would remove runs) is an answer to show, not an error
async function putRetention(body) {
  const r = await fetch("/api/settings/runs", { method: "PUT", headers: { "Content-Type": "application/json" },
                                                body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (r.ok || r.status === 409) return j;
  throw new Error(j.error !== undefined ? t(j.error) : r.statusText);
}

// A start: refused parameters are said at their fields and next to the button, in the owner's words (review UX-params
// P2); a world refused when it is built is waited for a few seconds and said here too, on the form where the owner set
// the parameters, instead of an empty run page (P1). A world that takes longer to build opens in the player, which says
// why if it is refused later.
async function startRun(body, { btn, errBox, form }) {
  errBox.replaceChildren();
  if (form) {
    const local = form.errors();
    form.markErrors(local);
    if (Object.keys(local).length) { errBox.append(el("div", {}, t("Not started: {why}", { why: Object.values(local).map((x) => t(x)).join("; ") }))); return; }
  }
  btn.disabled = true;
  try {
    const r = await fetch("/api/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
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
      try { m = await getJSON(`/api/runs/${encodeURIComponent(j.id)}`); } catch (e) { break; }
      if (m.state === "failed" || m.state === "finished") {
        const why = (m.errors || []).slice(-1)[0] || t("the world was not created");
        errBox.append(el("div", {}, t(why)), el("div", { class: "muted" }, t("Change the parameters (“Parameters…”) and start again. The record of the refusal is in the list of runs below.")));
        btn.disabled = false; btn.textContent = t("▶ Start");
        lastRuns = ""; loadRuns();
        return;
      }
      if ((m.worlds || []).length) break;
    }
    location.href = withLang(`/run?id=${encodeURIComponent(j.id)}`);  // a link's language goes along (F7)
  } catch (e) { errBox.append(el("div", {}, String(e.message || e))); btn.disabled = false; }
}

// devices and precision for one run (plan P11: global defaults on the settings page, per-run overrides here); the
// choice applies to the kernels that have a GPU implementation, fp32 only where the kernel allows it
async function runOverride(dev, prec) {
  if (dev.value === "" && prec.value === "") return null;
  if (!kernelInfo) kernelInfo = (await getJSON("/api/devices")).kernels;
  const kernels = {};
  for (const k of kernelInfo.filter((k) => k.gpu)) {
    const ok32 = ((k.precisions || {}).fp32 || {}).allowed;
    kernels[k.name] = { device: dev.value || "auto", precision: prec.value === "fp32" && ok32 ? "fp32" : "fp64" };
  }
  return { kernels };
}

function drawModes() {
  const set = (m) => { mode = m; try { localStorage.setItem("lfviz.mode", m); } catch (e) { /* ignore */ } drawModes(); drawCards(); };
  document.getElementById("modes").replaceChildren(
    el("button", { class: mode === "demo" ? "toggle on" : "", onclick: () => set("demo"), title: t("Prepared experiments: a set-up, checks, a history") }, t("Demonstrations")),
    el("button", { class: mode === "playground" ? "toggle on" : "", onclick: () => set("playground"), title: t("A laboratory for research: you build the scene, everything is computed live") }, t("Laboratories")));
  document.getElementById("mode-help").textContent = mode === "demo"
    ? t("Prepared demonstrations: each has its own set-up, checks against accepted physics and the history of the experiment.")
    : t("A laboratory for each branch of physics: add objects, change their parameters on the go and watch how they move and interact. Nothing is set in advance — everything is computed by the engine's laws in real time; the conservation laws are checked live.");
}

async function loadViz() {
  vizList = await getJSON("/api/viz");
  drawModes();
  drawCards();
}

function drawCards() {
  const box = document.getElementById("cards");
  box.replaceChildren();
  for (const v of vizList.filter((x) => (x.kind || "demo") === mode || (x.error && mode === "demo"))) {
    if (v.kind === "playground") { box.append(playgroundCard(v)); continue; }
    if (v.error) { box.append(el("div", { class: "card" }, el("h3", {}, v.id), el("div", { class: "st-bad" }, t(v.error)))); continue; }
    const presets = v.schema.presets;
    const sel = el("select", {}, presets.map((p) => el("option", { value: p.id }, p.label)));
    // what the scenario shows (e.g. a check that fails on purpose: review UX-params P23)
    const pnote = el("div", { class: "help" });
    const showPnote = () => { pnote.textContent = t((presets.find((p) => p.id === sel.value) || {}).note); };
    sel.addEventListener("change", showPnote); showPnote();
    const errBox = el("div", { class: "start-err" });
    const seed = el("input", { type: "text", placeholder: t("seed (optional)"), style: { width: "11em" } });
    const custom = el("div", { style: { display: "none", marginTop: "8px" } });
    let form = null;
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
    const dev = el("select", { title: t("For this run only; by default the settings of the “Devices” page") },
      [["", t("device: as set")], ["auto", t("auto")], ["cpu", "CPU"], ["gpu", "GPU 0"]].map(([val, s]) => el("option", { value: val }, s)));
    const prec = el("select", { title: t("The drawing's precision in this run; the checks are always fp64") },
      [["", t("precision: as set")], ["fp64", "fp64"], ["fp32", t("fp32 (where verified)")]].map(([val, s]) => el("option", { value: val }, s)));
    const btnRun = el("button", { class: "primary", onclick: async () => {
      const body = { viz: v.id, seed: seed.value.trim() || null };
      if (form) body.params = form.values; else body.preset = sel.value;
      let over = null;
      try { over = await runOverride(dev, prec); } catch (e) { toast(String(e.message || e)); return; }
      if (over) body.backend = over;
      await startRun(body, { btn: btnRun, errBox, form });
    } }, t("▶ Start"));
    box.append(el("div", { class: "card" },
      el("h3", {}, t(v.title)),
      el("div", {}, t(v.summary)),
      el("div", { class: "help", style: { marginTop: "6px" } }, t(v.purpose)),
      el("div", { class: "row" }, el("span", { class: "muted" }, t("Scenario:")), sel), pnote,
      el("div", { class: "row" }, btnRun, btnCustom, seed), errBox,
      el("div", { class: "row" }, el("span", { class: "muted" }, t("For this run:")), dev, prec, el("a", { href: "/settings" }, t("⚙ Devices"))),
      custom,
      el("div", { class: "help", style: { marginTop: "6px" } }, t("{id} · version {version}", { id: v.id, version: String(v.version) }))));
  }
  if (mode === "playground") {
    for (const [title, text] of PLANNED) box.append(el("div", { class: "card planned" }, el("h3", {}, title), el("div", {}, text), el("div", { class: "muted" }, t("coming later"))));
  }
}

// a playground section: start from a scenario (a prepared scene, or an empty one), with the section's laws, or from a
// scene file saved earlier (its laws and objects)
function playgroundCard(v) {
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
  const start = (body, btn) => startRun(body, { btn, errBox, form: body.params && !body.params.scene ? form : null });
  const btnRun = el("button", { class: "primary", onclick: () => start(form ? { viz: v.id, params: form.values } : { viz: v.id, preset: sel.value }, btnRun) }, t("▶ Begin"));
  const file = el("input", { type: "file", accept: ".lfscene,.json,application/json", style: { display: "none" } });
  file.onchange = async () => {
    const f = file.files[0];
    file.value = "";
    if (!f) return;
    let sc;
    try { sc = JSON.parse(await sceneText(f)); } catch (e) { toast(t("The scene file was not read: {why}", { why: e.message })); return; }
    if (!sc || sc.format !== "lfscene") { toast(t("This is not a scene file (lfscene)")); return; }
    if (sc.viz && sc.viz !== v.id) { toast(t("This is a scene of the section {other}, not of {this}", { other: sc.viz, this: v.id })); return; }
    start({ viz: v.id, params: { ...(sc.laws || {}), scene: sc } }, btnLoad);
  };
  const btnLoad = el("button", { title: t("Begin with a scene saved to a file (“💾 Save the scene” in the player)"), onclick: () => file.click() }, t("📂 From a scene file…"));
  return el("div", { class: "card" },
    el("h3", {}, t(v.title)),
    el("div", {}, t(v.summary)),
    el("div", { class: "help", style: { marginTop: "6px" } }, t(v.purpose)),
    el("div", { class: "row" }, el("span", { class: "muted" }, t("Begin:")), sel), pnote,
    el("div", { class: "row" }, btnRun, btnLaws, btnLoad, file), errBox,
    custom,
    el("div", { class: "help", style: { marginTop: "6px" } }, t("{id} · version {version}", { id: v.id, version: String(v.version) })));
}

function stateCell(r) {
  const cls = r.state === "running" ? (r.playing ? "live" : "paused") : (r.state === "failed" || r.state === "interrupted") ? "dead" : "";
  const label = { running: r.playing ? t("recording") : t("paused"), suspended: t("suspended"), finished: t("finished"),
                  stopped: t("stopped"), failed: r.error ? t("world not created") : t("failure"), interrupted: t("cut off"), starting: t("starting") }[r.state] || r.state;
  const extra = r.error ? el("div", { class: "st-bad start-why", title: t(r.error) }, t(r.error))  // a refused start: why (P1)
    : r.busy ? el("div", { class: "muted", title: t("The world is computing a change; it can be cancelled in the player") }, "⟳ " + (r.busy.what ? t(r.busy.what) : t("computing")))
    : r.state === "running" && !r.viewers ? el("div", { class: "muted", title: t("Without viewers a run pauses after a minute and frees its worker after half an hour") }, t("no viewers"))
    : r.resume_error ? el("div", { class: "st-bad", title: t(r.resume_error) }, t("resuming failed — ⏺ tries again")) : null;
  return el("td", {}, el("span", { class: "dot " + cls }), label, extra);
}

// a run's scenario by its name in the world's catalogue entry, not its id (review i18n-browser F12); an unknown id as
// it is
function presetLabel(r) {
  const v = vizList.find((x) => x.id === r.viz);
  const p = v && v.schema && (v.schema.presets || []).find((q) => q.id === r.preset);
  return p ? t(p.label) : String(r.preset);
}

async function loadRuns() {
  let runs;
  try { runs = await getJSON("/api/runs"); } catch (e) { return; }
  const key = JSON.stringify(runs);
  if (key === lastRuns) return;  // re-rendering would recreate buttons under the cursor
  lastRuns = key;
  await legacy(runs);  // runs recorded before the translation: their Russian titles in the language in force (F3)
  const box = document.getElementById("runs");
  if (!runs.length) { box.replaceChildren(el("div", { class: "muted" }, t("No runs yet: choose a visualization and press “▶ Start”."))); return; }
  const rows = runs.map((r) => el("tr", {},
    stateCell(r),
    el("td", {}, el("a", { href: `/run?id=${encodeURIComponent(r.id)}` }, t(r.title)),
       r.kind === "playground" ? el("span", { class: "badge", title: t("Laboratory: the record holds a window of the last minutes until “● Keep the record” is on") }, " " + (r.recording ? t("Laboratory · being kept") : t("Laboratory"))) : null,
       r.n_worlds > 1 ? el("span", { class: "badge", title: t("New worlds are created inside a run; the earlier ones stay in the record") }, " " + t("worlds: {n:d}", { n: r.n_worlds })) : null,
       r.scene ? el("div", {}, t(r.scene)) : null, el("div", { class: "muted mono" }, r.id),
       r.modifications && r.modifications.length ? el("span", { class: "badge mod", title: r.modifications.map((m) => t("{label}: {value} (standard: {standard})", { label: t(m.label), value: typeof m.value === "number" ? num(m.value) : t(m.value), standard: typeof m.standard === "number" ? num(m.standard) : t(m.standard) })).join("\n") }, t("modified physics")) : null,
       r.approximations && r.approximations.length ? el("span", { class: "badge mod", title: r.approximations.map((a) => t(a)).join("\n") }, t("approximation")) : null,
       r.devices_override ? el("span", { class: "badge", title: t("The devices and the precision were set for this run") }, t("own devices")) : null),
    el("td", {}, r.preset ? presetLabel(r) : t("own parameters"), el("div", { class: "muted" }, t("seed {seed}", { seed: String(r.seed) }))),
    el("td", { class: "mono nw" }, time(r.sim_t)),
    el("td", {}, r.created ? r.created.replace("T", " ") : "",
       r.last_action ? el("div", { class: "muted", title: t("The last action: removed after {days} without actions unless ★", { days: days(keepDays) }) }, t("last: {when}", { when: r.last_action.replace("T", " ") })) : null),
    el("td", { class: "mono nw" }, t("{n:.3g} MB", { n: r.size / 1e6 })),
    el("td", {}, r.viewers ? `${r.viewers} 👁` : ""),
    el("td", {},
      el("button", { title: r.keep ? t("Kept for good") : t("Keep for good (do not remove after {days} without actions or by the quota)", { days: days(keepDays) }), class: r.keep ? "toggle on" : "",
                     onclick: async () => { await postJSON(`/api/runs/${r.id}/keep`, { keep: !r.keep }); lastRuns = ""; loadRuns(); } }, r.keep ? "★" : "☆"),
      !r.viewers ? el("button", { title: r.state === "running" ? t("Delete the run (it is suspended first) with its record") : t("Delete the record"), onclick: async () => {
        if (!confirm(t("Delete the run {id} with its record?", { id: r.id }))) return;
        try { await postJSON(`/api/runs/${r.id}`, undefined, "DELETE"); } catch (e) { toast(e.message); }
        lastRuns = ""; loadRuns(); } }, "✕") : null)));
  box.replaceChildren(el("table", { class: "runs" },
    el("tr", {}, [t("State"), t("Visualization"), t("Scenario"), t("World time"), t("Created"), t("Record"), "", ""].map((h) => el("th", {}, h))), rows));
}

async function loadHealth() {
  try {
    const h = await getJSON("/api/health");
    document.getElementById("health").textContent = t("{n:d} of {max:d} running · {runs:d} records in all", { n: h.running, max: h.max_workers, runs: h.runs });
  } catch (e) { document.getElementById("health").textContent = t("the server is not available"); }
}

function showHelp() {
  modal(el("div", {},
    el("h3", {}, t("How to use it")),
    el("p", {}, t("Each visualization is a folder of its own in visualizations/ of the lfphys repository. A run starts only with the “▶ Start” button: the server creates a worker process that computes this run's physics and writes everything it computed into a record on the server.")),
    el("p", {}, t("Everything you see in the player is the result of the current run's computation: rays, arrivals of light, clock readings, interference patterns. Nothing is drawn “because it is known”; next to the computed value the reference of accepted physics is shown (“Checks”).")),
    el("p", {}, t("In the player the set-up (source, slits, screen, observer…) changes at once, on the go. The laws of physics and the initial conditions change only explicitly — with the “▶ Start a new world” button inside the same run; a world with changed laws is marked “modified physics”.")),
    el("p", {}, t("There is no stop: a run without viewers pauses after a minute and frees its worker after half an hour (“suspended”); open it and press ⏺ — the world is restored from its saved state and the record continues. Runs nobody has opened for {days} are removed (the period is set above the list of runs and kept on the server); ☆ keeps a record for good. A run open in no tab can be deleted (✕).", { days: days(keepDays) })),
    el("p", { class: "muted" }, t("Keys: T — theme, ? — help."))));
}

loadViz().catch((e) => toast(t("Catalogue: {why}", { why: e.message })));
loadRetention().then(() => { lastRuns = ""; loadRuns(); });
loadRuns(); loadHealth();
setInterval(() => { loadRuns(); loadHealth(); }, 2000);
