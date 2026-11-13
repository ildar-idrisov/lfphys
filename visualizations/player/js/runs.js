// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The runs page (/runs, server only; moved off the start page on 2026-11-13): the runs (open, keep, delete) and their
// removal period. There is no stop (owner, 2026-10-28): a run computes or is paused; one left without viewers is
// suspended and resumed when opened and ⏺ pressed; runs not touched for the removal period are removed unless kept (★);
// the period (3 days by default) is set above the runs and kept on the server (owner, 2026-10-29).
import { apiGet, getJSON, page, postJSON, url } from "./api.js";
import { fmtField, legacy, parseNum, t } from "./i18n.js";
import { el, initTheme, modal, num, numberInput, time, toast, toggleTheme } from "./ui.js";

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
let keepDays = 3;  // the removal period, as the server has it

// "1 day", "3 days" (the plural forms of the language)
function days(n) { return t("{n:d} days", { n }); }

// the removal period: changed here, saved on the server; a period that would remove runs at once lists them first
async function loadRetention() {
  try { keepDays = (await getJSON(url("api/settings/runs"))).keep_days; } catch (e) { return; }
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
  const r = await fetch(url("api/settings/runs"), { method: "PUT", headers: { "Content-Type": "application/json" },
                                                body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (r.ok || r.status === 409) return j;
  throw new Error(j.error !== undefined ? t(j.error) : r.statusText);
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
  try { runs = await getJSON(url("api/runs")); } catch (e) { return; }
  const key = JSON.stringify(runs);
  if (key === lastRuns) return;  // re-rendering would recreate buttons under the cursor
  lastRuns = key;
  await legacy(runs);  // runs recorded before the translation: their Russian titles in the language in force (F3)
  const box = document.getElementById("runs");
  if (!runs.length) { box.replaceChildren(el("div", { class: "muted" }, t("No runs yet: choose a demonstration on the start page and press “▶ Compute live”."))); return; }
  const rows = runs.map((r) => el("tr", {},
    stateCell(r),
    el("td", {}, el("a", { href: page("run", { id: r.id }) }, t(r.title)),
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
                     onclick: async () => { await postJSON(url(`api/runs/${encodeURIComponent(r.id)}/keep`), { keep: !r.keep }); lastRuns = ""; loadRuns(); } }, r.keep ? "★" : "☆"),
      !r.viewers ? el("button", { title: r.state === "running" ? t("Delete the run (it is suspended first) with its record") : t("Delete the record"), onclick: async () => {
        if (!confirm(t("Delete the run {id} with its record?", { id: r.id }))) return;
        try { await postJSON(url(`api/runs/${encodeURIComponent(r.id)}`), undefined, "DELETE"); } catch (e) { toast(e.message); }
        lastRuns = ""; loadRuns(); } }, "✕") : null)));
  box.replaceChildren(el("table", { class: "runs" },
    el("tr", {}, [t("State"), t("Visualization"), t("Scenario"), t("World time"), t("Created"), t("Record"), "", ""].map((h) => el("th", {}, h))), rows));
}

async function loadHealth() {
  try {
    const h = await apiGet("health");
    document.getElementById("health").textContent = t("{n:d} of {max:d} running · {runs:d} records in all", { n: h.running, max: h.max_workers, runs: h.runs });
  } catch (e) { document.getElementById("health").textContent = t("the server is not available"); }
}

function showHelp() {
  modal(el("div", {},
    el("h3", {}, t("My runs")),
    el("p", {}, t("Each run is computed by a worker process of this server, which writes everything it computed into a record on the server. A run opens in the player with its whole history.")),
    el("p", {}, t("There is no stop: a run without viewers pauses after a minute and frees its worker after half an hour (“suspended”); open it and press ⏺ — the world is restored from its saved state and the record continues. Runs nobody has opened for {days} are removed (the period is set above the list of runs and kept on the server); ☆ keeps a record for good. A run open in no tab can be deleted (✕).", { days: days(keepDays) })),
    el("p", { class: "muted" }, t("Keys: T — theme, ? — help."))));
}

apiGet("viz").then((v) => { vizList = v; lastRuns = ""; loadRuns(); }).catch(() => {});
loadRetention().then(() => { lastRuns = ""; loadRuns(); });
loadRuns(); loadHealth();
setInterval(() => { loadRuns(); loadHealth(); }, 2000);
