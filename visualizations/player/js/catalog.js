// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Catalogue page: two modes (owner, 2026-10-28) — the demonstrations (prepared visualizations: start a run) and the
// playground (research sandboxes by section of physics: start from a scenario, an empty scene or a scene file) —, and
// the runs (open, keep, delete). There is no stop (owner,
// 2026-10-28): a run computes or is paused; one left without viewers is suspended and resumed when opened and ⏺ pressed;
// runs not touched for the removal period are removed unless kept (★); the period (3 days by default) is set above the
// runs and kept on the server (owner, 2026-10-29).
import { getJSON, postJSON } from "./api.js";
import { el, initTheme, modal, num, paramForm, time, toast, toggleTheme } from "./ui.js";

// a scene file is at most 900 000 characters (the server's limit for a JSON parameter, below the socket's message
// limit: review B6-F20)
async function sceneText(f) {
  const text = await f.text();
  if (text.length > 900000) throw new Error(`файл сцены больше 900 000 символов (${text.length})`);
  return text;
}

initTheme();
document.getElementById("theme").onclick = toggleTheme;
document.getElementById("help").onclick = showHelp;
document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
  if (e.key === "t" || e.key === "T" || e.key === "е" || e.key === "Е") toggleTheme();
  if (e.key === "?") showHelp();
});

let vizList = [];
let lastRuns = "";
let kernelInfo = null;  // the engine's kernels (from /api/devices), for the per-run device choice
let keepDays = 3;  // the removal period, as the server has it
let mode = (() => { try { return localStorage.getItem("lfviz.mode") || "demo"; } catch (e) { return "demo"; } })();
if (location.hash === "#playground") mode = "playground";
// sections of the playground planned later (lfphys/PLAN.md, P15): shown, not startable
const PLANNED = [["Оптика и волны", "источники, щели, линзы, зеркала, решётки, экраны (пакет B9)"],
                 ["Электричество и магнетизм", "заряды, токи, магниты, проводники; поля и излучение (пакет B9)"],
                 ["Относительность", "наблюдатели, часы, стержни, ракеты: что видит каждый (пакет B9)"]];

// "1 день", "3 дня", "5 дней", "21 день"
function days(n) {
  const m10 = n % 10, m100 = n % 100;
  const w = m10 === 1 && m100 !== 11 ? "день" : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? "дня" : "дней";
  return `${n} ${w}`;
}

// the removal period: changed here, saved on the server; a period that would remove runs at once lists them first
async function loadRetention() {
  try { keepDays = (await getJSON("/api/settings/runs")).keep_days; } catch (e) { return; }
  const inp = el("input", { type: "number", min: 1, max: 3650, step: 1, value: keepDays, style: "width:5em",
                            title: "Через сколько дней без действий (просмотр, команда) запуск удаляется вместе с записью" });
  const note = el("span", { class: "muted" });
  inp.onchange = () => saveRetention(inp, note);
  document.getElementById("retention").replaceChildren(
    el("span", { class: "muted" }, "Удалять запуски без действий через"), inp,
    el("span", { class: "muted" }, "дн. (кроме отмеченных ★ и открытых во вкладке)"), note);
}

async function saveRetention(inp, note) {
  const d = Number(inp.value);
  let r;
  try {
    r = await putRetention({ keep_days: d });
    if (r.would_remove) {
      if (!confirm(`При сроке ${days(d)} сразу удалятся вместе с записями запуски (${r.would_remove.length}):\n` +
                   `${r.would_remove.join("\n")}\n\nУдалить их и сохранить срок?`)) { inp.value = keepDays; return; }
      r = await putRetention({ keep_days: d, confirm: r.would_remove });
      if (r.would_remove) { toast("Пока вы подтверждали, список запусков к удалению изменился — повторите"); inp.value = keepDays; return; }
    }
  } catch (e) { toast("Срок хранения: " + e.message); inp.value = keepDays; return; }
  keepDays = r.keep_days;
  note.textContent = r.removed.length ? `сохранено; удалено запусков: ${r.removed.length}` : "сохранено";
  setTimeout(() => { note.textContent = ""; }, 4000);
  lastRuns = ""; loadRuns();
}

// PUT /api/settings/runs; 409 (the period would remove runs) is an answer to show, not an error
async function putRetention(body) {
  const r = await fetch("/api/settings/runs", { method: "PUT", headers: { "Content-Type": "application/json" },
                                                body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (r.ok || r.status === 409) return j;
  throw new Error(j.error || r.statusText);
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
    if (Object.keys(local).length) { errBox.append(el("div", {}, "Не запущено: " + Object.values(local).join("; "))); return; }
  }
  btn.disabled = true;
  try {
    const r = await fetch("/api/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      if (form && j.fields) form.markErrors(j.fields);
      errBox.append(el("div", {}, "Не запущено: " + (j.error || r.statusText)));
      btn.disabled = false;
      return;
    }
    btn.textContent = "⟳ строится мир…";
    const t0 = Date.now();
    while (Date.now() - t0 < 8000) {
      await new Promise((ok) => setTimeout(ok, 400));
      let m;
      try { m = await getJSON(`/api/runs/${encodeURIComponent(j.id)}`); } catch (e) { break; }
      if (m.state === "failed" || m.state === "finished") {
        const why = (m.errors || []).slice(-1)[0] || "мир не создан";
        errBox.append(el("div", {}, why), el("div", { class: "muted" }, "Измените параметры («Параметры…») и запустите снова. Запись отказа — в списке запусков ниже."));
        btn.disabled = false; btn.textContent = "▶ Запустить";
        lastRuns = ""; loadRuns();
        return;
      }
      if ((m.worlds || []).length) break;
    }
    location.href = `/run?id=${encodeURIComponent(j.id)}`;
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
    el("button", { class: mode === "demo" ? "toggle on" : "", onclick: () => set("demo"), title: "Подготовленные опыты: установка, проверки, история" }, "Демонстрации"),
    el("button", { class: mode === "playground" ? "toggle on" : "", onclick: () => set("playground"), title: "Песочница для исследований: сцену собираете вы, всё считается вживую" }, "Плейграунд"));
  document.getElementById("mode-help").textContent = mode === "demo"
    ? "Подготовленные демонстрации: у каждой — своя установка, проверки против общепринятой физики и история опыта."
    : "Песочница по разделам физики: добавляйте объекты, меняйте их параметры на ходу и смотрите, как они движутся и взаимодействуют. Ничего не задано заранее — всё считается законами движка в реальном времени; законы сохранения проверяются вживую.";
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
    if (v.error) { box.append(el("div", { class: "card" }, el("h3", {}, v.id), el("div", { class: "st-bad" }, v.error))); continue; }
    const presets = v.schema.presets;
    const sel = el("select", {}, presets.map((p) => el("option", { value: p.id }, p.label)));
    // what the scenario shows (e.g. a check that fails on purpose: review UX-params P23)
    const pnote = el("div", { class: "help" });
    const showPnote = () => { pnote.textContent = (presets.find((p) => p.id === sel.value) || {}).note || ""; };
    sel.addEventListener("change", showPnote); showPnote();
    const errBox = el("div", { class: "start-err" });
    const seed = el("input", { type: "text", placeholder: "затравка (необяз.)", style: { width: "11em" } });
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
    } }, "Параметры…");
    const dev = el("select", { title: "Только для этого запуска; по умолчанию — настройки на странице «Устройства»" },
      [["", "устройство: по настройкам"], ["auto", "авто"], ["cpu", "CPU"], ["gpu", "GPU 0"]].map(([val, t]) => el("option", { value: val }, t)));
    const prec = el("select", { title: "Точность рисунка в этом запуске; проверки всегда fp64" },
      [["", "точность: по настройкам"], ["fp64", "fp64"], ["fp32", "fp32 (где проверена)"]].map(([val, t]) => el("option", { value: val }, t)));
    const btnRun = el("button", { class: "primary", onclick: async () => {
      const body = { viz: v.id, seed: seed.value.trim() || null };
      if (form) body.params = form.values; else body.preset = sel.value;
      let over = null;
      try { over = await runOverride(dev, prec); } catch (e) { toast(String(e.message || e)); return; }
      if (over) body.backend = over;
      await startRun(body, { btn: btnRun, errBox, form });
    } }, "▶ Запустить");
    box.append(el("div", { class: "card" },
      el("h3", {}, v.title),
      el("div", {}, v.summary),
      el("div", { class: "help", style: { marginTop: "6px" } }, v.purpose),
      el("div", { class: "row" }, el("span", { class: "muted" }, "Сценарий:"), sel), pnote,
      el("div", { class: "row" }, btnRun, btnCustom, seed), errBox,
      el("div", { class: "row" }, el("span", { class: "muted" }, "Для этого запуска:"), dev, prec, el("a", { href: "/settings" }, "⚙ Устройства")),
      custom,
      el("div", { class: "help", style: { marginTop: "6px" } }, `${v.id} · версия ${v.version}`)));
  }
  if (mode === "playground") {
    for (const [title, text] of PLANNED) box.append(el("div", { class: "card planned" }, el("h3", {}, title), el("div", {}, text), el("div", { class: "muted" }, "будет позже")));
  }
}

// a playground section: start from a scenario (a prepared scene, or an empty one), with the section's laws, or from a
// scene file saved earlier (its laws and objects)
function playgroundCard(v) {
  const presets = v.schema.presets;
  const sel = el("select", {}, presets.map((p) => el("option", { value: p.id }, p.label)));
  const pnote = el("div", { class: "help" });
  const showPnote = () => { pnote.textContent = (presets.find((p) => p.id === sel.value) || {}).note || ""; };
  sel.addEventListener("change", showPnote); showPnote();
  const errBox = el("div", { class: "start-err" });
  const custom = el("div", { style: { display: "none", marginTop: "8px" } });
  let form = null;
  const btnLaws = el("button", { title: "Законы мира этого раздела (новый мир — при их изменении)", onclick: () => {
    if (custom.style.display === "none") {
      const values = {};
      for (const p of v.schema.params) values[p.id] = p.default;
      Object.assign(values, (presets.find((p) => p.id === sel.value) || {}).params || {});
      form = paramForm(v.schema, values);
      custom.replaceChildren(form.el);
      custom.style.display = "";
    } else { custom.style.display = "none"; form = null; }
  } }, "Законы…");
  const start = (body, btn) => startRun(body, { btn, errBox, form: body.params && !body.params.scene ? form : null });
  const btnRun = el("button", { class: "primary", onclick: () => start(form ? { viz: v.id, params: form.values } : { viz: v.id, preset: sel.value }, btnRun) }, "▶ Начать");
  const file = el("input", { type: "file", accept: ".lfscene,.json,application/json", style: { display: "none" } });
  file.onchange = async () => {
    const f = file.files[0];
    file.value = "";
    if (!f) return;
    let sc;
    try { sc = JSON.parse(await sceneText(f)); } catch (e) { toast("Файл сцены не прочитан: " + e.message); return; }
    if (!sc || sc.format !== "lfscene") { toast("Это не файл сцены (lfscene)"); return; }
    if (sc.viz && sc.viz !== v.id) { toast(`Это сцена раздела ${sc.viz}, а не ${v.id}`); return; }
    start({ viz: v.id, params: { ...(sc.laws || {}), scene: sc } }, btnLoad);
  };
  const btnLoad = el("button", { title: "Начать с сцены, сохранённой в файл («💾 Сохранить сцену» в плеере)", onclick: () => file.click() }, "📂 Из файла сцены…");
  return el("div", { class: "card" },
    el("h3", {}, v.title),
    el("div", {}, v.summary),
    el("div", { class: "help", style: { marginTop: "6px" } }, v.purpose),
    el("div", { class: "row" }, el("span", { class: "muted" }, "Начать:"), sel), pnote,
    el("div", { class: "row" }, btnRun, btnLaws, btnLoad, file), errBox,
    custom,
    el("div", { class: "help", style: { marginTop: "6px" } }, `${v.id} · версия ${v.version}`));
}

function stateCell(r) {
  const cls = r.state === "running" ? (r.playing ? "live" : "paused") : (r.state === "failed" || r.state === "interrupted") ? "dead" : "";
  const label = { running: r.playing ? "идёт запись" : "пауза", suspended: "приостановлен", finished: "завершён",
                  stopped: "остановлен", failed: r.error ? "мир не создан" : "сбой", interrupted: "оборван", starting: "старт" }[r.state] || r.state;
  const extra = r.error ? el("div", { class: "st-bad start-why", title: r.error }, r.error)  // a refused start: why (P1)
    : r.busy ? el("div", { class: "muted", title: "Мир считает изменение; в плеере его можно отменить" }, "⟳ " + (r.busy.what || "считает"))
    : r.state === "running" && !r.viewers ? el("div", { class: "muted", title: "Без зрителей запуск встаёт на паузу через минуту и освобождает вычислитель через полчаса" }, "без зрителей")
    : r.resume_error ? el("div", { class: "st-bad", title: r.resume_error }, "продолжение не удалось — ⏺ повторит") : null;
  return el("td", {}, el("span", { class: "dot " + cls }), label, extra);
}

async function loadRuns() {
  let runs;
  try { runs = await getJSON("/api/runs"); } catch (e) { return; }
  const key = JSON.stringify(runs);
  if (key === lastRuns) return;  // re-rendering would recreate buttons under the cursor
  lastRuns = key;
  const box = document.getElementById("runs");
  if (!runs.length) { box.replaceChildren(el("div", { class: "muted" }, "Запусков ещё нет: выберите визуализацию и нажмите «▶ Запустить».")); return; }
  const rows = runs.map((r) => el("tr", {},
    stateCell(r),
    el("td", {}, el("a", { href: `/run?id=${encodeURIComponent(r.id)}` }, r.title),
       r.kind === "playground" ? el("span", { class: "badge", title: "Плейграунд: запись держит окно последних минут, пока не включено «● Сохранять запись»" }, r.recording ? " плейграунд · сохраняется" : " плейграунд") : null,
       r.n_worlds > 1 ? el("span", { class: "badge", title: "Новые миры создаются внутри запуска; прежние остаются в записи" }, ` миров: ${r.n_worlds}`) : null,
       r.scene ? el("div", {}, r.scene) : null, el("div", { class: "muted mono" }, r.id),
       r.modifications && r.modifications.length ? el("span", { class: "badge mod", title: r.modifications.map((m) => `${m.label}: ${m.value} (стандарт: ${m.standard})`).join("\n") }, "модиф. физика") : null,
       r.approximations && r.approximations.length ? el("span", { class: "badge mod", title: r.approximations.join("\n") }, "приближение") : null,
       r.devices_override ? el("span", { class: "badge", title: "Устройства и точность заданы для этого запуска" }, "свои устройства") : null),
    el("td", {}, r.preset || "свои параметры", el("div", { class: "muted" }, "затравка " + r.seed)),
    el("td", { class: "mono" }, time(r.sim_t)),
    el("td", {}, r.created ? r.created.replace("T", " ") : "",
       r.last_action ? el("div", { class: "muted", title: `Последнее действие: удаление через ${days(keepDays)} без действий, если не ★` }, "последнее: " + r.last_action.replace("T", " ")) : null),
    el("td", { class: "mono" }, num(r.size / 1e6, 3) + " МБ"),
    el("td", {}, r.viewers ? `${r.viewers} 👁` : ""),
    el("td", {},
      el("button", { title: r.keep ? "Хранится всегда" : `Хранить всегда (не удалять через ${days(keepDays)} без действий и по квоте)`, class: r.keep ? "toggle on" : "",
                     onclick: async () => { await postJSON(`/api/runs/${r.id}/keep`, { keep: !r.keep }); lastRuns = ""; loadRuns(); } }, r.keep ? "★" : "☆"),
      !r.viewers ? el("button", { title: r.state === "running" ? "Удалить запуск (он приостановится) вместе с записью" : "Удалить запись", onclick: async () => {
        if (!confirm(`Удалить запуск ${r.id} вместе с записью?`)) return;
        try { await postJSON(`/api/runs/${r.id}`, undefined, "DELETE"); } catch (e) { toast(e.message); }
        lastRuns = ""; loadRuns(); } }, "✕") : null)));
  box.replaceChildren(el("table", { class: "runs" },
    el("tr", {}, ["Состояние", "Визуализация", "Сценарий", "Время мира", "Создан", "Запись", "", ""].map((h) => el("th", {}, h))), rows));
}

async function loadHealth() {
  try {
    const h = await getJSON("/api/health");
    document.getElementById("health").textContent = `идут ${h.running} из ${h.max_workers} · всего записей ${h.runs}`;
  } catch (e) { document.getElementById("health").textContent = "сервер недоступен"; }
}

function showHelp() {
  modal(el("div", {},
    el("h3", {}, "Как пользоваться"),
    el("p", {}, "Каждая визуализация — отдельная папка в visualizations/ репозитория lfphys. Запуск начинается только по кнопке «▶ Запустить»: сервер создаёт рабочий процесс, который считает физику этого запуска и пишет всё, что посчитал, в запись на сервере."),
    el("p", {}, "Всё, что вы видите в плеере, — результат вычислений текущего запуска: лучи, события прихода света, показания часов, интерференционные картины. Ничего не рисуется «потому что известно»; рядом с вычисленным показан эталон общепринятой физики («Проверки»)."),
    el("p", {}, "В плеере установка (источник, щели, экран, наблюдатель…) меняется сразу, на ходу. Законы физики и начальные условия меняются только явно — кнопкой «Новый мир» внутри того же запуска; мир с изменёнными законами помечен «модиф. физика»."),
    el("p", {}, `Остановки нет: запуск без зрителей через минуту встаёт на паузу, через полчаса освобождает вычислитель («приостановлен»); откройте его и нажмите ⏺ — мир восстановится с сохранённого состояния и запись пойдёт дальше. Запуски, к которым не обращались ${days(keepDays)}, удаляются (срок задаётся над списком запусков и хранится на сервере); ☆ — хранить запись всегда. Удалить (✕) можно запуск, не открытый ни в одной вкладке.`),
    el("p", { class: "muted" }, "Горячие клавиши: T — тема, ? — справка.")));
}

loadViz().catch((e) => toast("Каталог: " + e.message));
loadRetention().then(() => { lastRuns = ""; loadRuns(); });
loadRuns(); loadHealth();
setInterval(() => { loadRuns(); loadHealth(); }, 2000);
