// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// «Приборы» (plan P16.3) in a browser: the panel of the measurables on the fixture world p97_osc (harmonic oscillators
// with closed forms, tests/instruments_worlds, through LFVIZ_EXTRA) — the quantities listed by group, plots drawn, the
// value at the history cursor equal to the record's value at that time, the CSV link giving the record's values, and a
// sweep made from the panel (estimate, start, progress, table, plot) whose numbers equal the closed form x(t0 + T) =
// x0 cos ωT + v0/ω sin ωT for each k. Screenshots of the panel go to the folder given.
//
// Run against a PRIVATE server whose LFVIZ_EXTRA names tests/instruments_worlds (never the shared one on 8479):
//   docker run -d --name lf-lbi-srv --memory=12g -p 8592:8479 -v <engine>:/lf:ro -v <tmp runs>:/lf/visualizations/runs \
//     -e LFPHYS_NO_GPU=1 -e LFVIZ_EXTRA=/lf/visualizations/tests/playgrounds:/lf/visualizations/tests/instruments_worlds \
//     -w /lf/visualizations lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
//   docker run --rm --init --shm-size=2g --network host --memory=4g -v <scratch with node_modules/playwright@1.58.2>:/pw \
//     -v <engine>/visualizations/tests/browser:/t:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     -e LFVIZ_LANG=en|ru sh -c "cp /t/*.mjs /pw/ && node /pw/instruments_checks.mjs 8592 /pw/shots"
// Prints one JSON line per check and exits with code 1 when one fails.
import { chromium } from "playwright";
import { esc, inLang, loadI18n } from "./lfi18n.mjs";
import { mkdirSync } from "node:fs";

const port = process.argv[2] || "8592";
const shots = process.argv[3] || "./shots";
mkdirSync(shots, { recursive: true });
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const settle = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 300)))));
let failed = 0;
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: name, ok: !!ok, ...info })); };
// the texts as the page shows them in the language under test (LFVIZ_LANG)
const { t: tr, fmt } = await loadI18n(base);
const OSC1 = tr({ $t: "{type} {n:d}", a: { type: { $t: "Oscillator" }, n: 1 } });
const POS = `${OSC1}: ${tr("position")}`;
const EG = tr("for example: 1; 2; 4; 8").split(":")[0];
const HOW = tr("How long to compute"), WHAT_M = tr("What to measure"), WHAT_T = tr("What to take"), ESTIMATE = tr("Estimate"), START = tr("▶ Start the sweep");
// a state of the sweep shown in its header (.in-sh / .in-sres .in-sh)
const shState = (page, sel, word) => page.waitForFunction(([sel, w]) => ((document.querySelector(sel) || {}).textContent || "").includes(w), [sel, word], { timeout: 120000 });
const estimated = (page) => page.waitForFunction(() => !document.querySelector(".in-sweep button.primary").disabled || document.querySelector(".in-est").classList.contains("in-bad"), null, { timeout: 30000 });

// the exact motion of the fixture: x'' = -(k/m) x
const xv = (t, x0, v0, k, m = 1) => { const w = Math.sqrt(k / m); return [x0 * Math.cos(w * t) + v0 / w * Math.sin(w * t), -x0 * w * Math.sin(w * t) + v0 * Math.cos(w * t)]; };

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-accelerated-2d-canvas"] });
const errs = [];
try {
  const { id } = await post("/api/runs", { viz: "p97_osc", preset: "one", seed: 3 });
  for (let i = 0; i < 200 && (await get(`/api/runs/${id}`)).state !== "running"; i++) await sleep(200);
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  await sleep(3000);
  await post(`/api/runs/${id}/command`, { cmd: "pause" });
  await sleep(1000);
  const page = await br.newPage({ viewport: { width: 1600, height: 1100 } });
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`console: ${m.text()}`.slice(0, 300)); });
  await page.goto(inLang(`${base}/run?id=${id}`));
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !window.__lfPlayer.replaying(), null, { timeout: 60000 });
  await settle(page);

  // 1. the panel: shown, the quantities grouped, the first world-wide ones plotted
  const st = await page.evaluate(() => ({
    shown: !!document.querySelector(".in-panel") && document.querySelector(".in-panel").style.display !== "none",
    groups: [...document.querySelectorAll(".in-panel .in-group > summary")].map((s) => s.textContent),
    names: [...document.querySelectorAll(".in-panel .in-q .in-name")].map((s) => s.textContent),
    plots: [...document.querySelectorAll(".in-panel .in-plot .in-pt")].map((s) => s.textContent),
    state: window.lfInstruments.state() }));
  check("panel listed", st.shown && st.groups.join() === [tr("World"), tr("Oscillators")].join() && st.names.includes(`${POS}, ${tr("m")}`)
    && st.plots.join("|") === `${tr("Total energy")}, ${tr("J")}|${tr("Position of the first oscillator")}, ${tr("m")}`, st);

  // 2. choose a probe's quantity: a third plot, drawn (pixels of the line's colour)
  await page.locator(".in-q", { hasText: POS }).locator("input").check();
  await settle(page);
  const drawn = await page.evaluate((POS) => {
    const cv = [...document.querySelectorAll(".in-plot")].find((p) => p.textContent.startsWith(POS)).querySelector("canvas");
    const d = cv.getContext("2d").getImageData(0, 0, cv.width, cv.height).data;
    const bg = [d[0], d[1], d[2]];
    let n = 0; for (let i = 0; i < d.length; i += 4) if (Math.abs(d[i] - bg[0]) + Math.abs(d[i + 1] - bg[1]) + Math.abs(d[i + 2] - bg[2]) > 60) n++;
    return { n, w: cv.width, h: cv.height };
  }, POS);
  check("plot drawn", drawn.n > 200, drawn);

  // 3. the cursor in the middle of the history: the value shown is the record's at that time
  const nf = await page.evaluate(() => window.__lfPlayer.frames());
  await page.evaluate((i) => window.__lfPlayer.goTo(i), Math.round(nf / 2));
  await settle(page);
  const tc = await page.evaluate(() => window.__lfPlayer.t());
  const ser = await get(`/api/runs/${id}/series?ids=o1.x&to=${tc}`);
  const xr = ser.values["o1.x"][ser.values["o1.x"].length - 1];
  const shown = await page.evaluate((POS) => [...document.querySelectorAll(".in-plot")].find((p) => p.textContent.startsWith(POS)).querySelector(".in-pv").textContent, POS);
  const shownNum = Number(shown.split(" ")[0].replace(/[\s\u202f]/g, "").replace(",", ".").replace("−", "-"));
  check("value at cursor", ser.t[ser.t.length - 1] === tc && Math.abs(shownNum - xr) < 1e-5 * Math.max(1, Math.abs(xr)) && Math.abs(xr - xv(tc, 1, 0, 4)[0]) < 1e-12, { tc, shown, xr });
  await page.locator(".in-panel").screenshot({ path: `${shots}/instruments_panel.png` });

  // 4. the CSV link: the record's values, the header with units
  const csv = await page.evaluate(async () => { const a = document.querySelector(".in-panel .in-csv"); const r = await fetch(a.href); return { href: a.href, text: await r.text() }; });
  const lines = csv.text.trim().split(/\r?\n/);
  const head = [`t, ${tr("s")}`, `${tr("Total energy")}, ${tr("J")} [E]`, `${tr("Position of the first oscillator")}, ${tr("m")} [x_first]`, `${POS}, ${tr("m")} [o1.x]`].map((x) => `"${x}"`).join(",");
  check("csv", lines[0] === head && lines.length - 1 === (await get(`/api/runs/${id}/series?ids=E&max_points=50000`)).n_frames, { head: lines[0], rows: lines.length - 1 });

  // 5. a sweep from the panel: the spring constant, the position after 0.7 s
  await page.evaluate(() => { document.querySelector(".in-sweep-box").open = true; });
  await page.waitForSelector(".in-sweep select", { timeout: 20000 });
  await page.selectOption(".in-sweep select >> nth=0", "law:k");
  const form = page.locator(".in-sweep");
  await form.locator(`input[placeholder^='${EG}']`).fill("1; 4; 9; 16");
  await form.locator(".ctl", { hasText: HOW }).locator("input").fill("0,7");
  await form.locator(".ctl", { hasText: WHAT_M }).locator("select").selectOption("o1.x");
  await form.locator("button", { hasText: ESTIMATE }).click();
  await estimated(page);
  const estText = await page.textContent(".in-est");
  check("estimate shown", estText.startsWith("≈") && estText.includes(tr("{m:d} min", { m: 10 })), { estText });
  await form.locator("button", { hasText: START }).click();
  await shState(page, ".in-sh", tr("done"));
  await settle(page);
  const sw = await get(`/api/runs/${id}/sweeps`);
  const s = await get(`/api/runs/${id}/sweeps/${sw[sw.length - 1].n}`);
  const [x0, v0] = xv(s.base.t, 1, 0, 4);
  const errsK = s.results.map((r) => Math.abs(r.measured - xv(0.7, x0, v0, r.value)[0]));
  const rows = await page.evaluate(() => [...document.querySelectorAll(".in-tab tr")].slice(1).map((tr) => [...tr.children].map((td) => td.textContent)));
  check("sweep from the panel", s.state === "done" && rows.length === 4 && Math.max(...errsK) < 1e-10 && rows[0][0] === "1", { errsK, rows, base: s.base });
  const sweepDrawn = await page.evaluate(() => { const cv = document.querySelector(".in-scv"); const d = cv.getContext("2d").getImageData(0, 0, cv.width, cv.height).data; let n = 0; for (let i = 0; i < d.length; i += 4) if (d[i] !== d[0] || d[i + 1] !== d[1]) n++; return n; });
  check("sweep plot drawn", sweepDrawn > 300, { sweepDrawn });
  await page.evaluate(() => document.querySelectorAll(".toast").forEach((t) => t.remove()));
  await page.locator(".in-sweep").screenshot({ path: `${shots}/instruments_sweep.png` });
  // the dark theme
  await page.keyboard.press("t");
  await settle(page);
  await page.locator(".in-sres").screenshot({ path: `${shots}/instruments_sweep_dark.png` });
  await page.screenshot({ path: `${shots}/instruments_page.png` });
  check("no page errors", errs.length === 0, { errs: errs.slice(0, 5) });
  await page.close();
} catch (e) { failed++; console.log(JSON.stringify({ failed: e.message, errs: errs.slice(0, 5) })); }

// --- part 2: the LB1 reviews ----------------------------------------------------------------------------------------
const errs2 = [];
try {
  const { id } = await post("/api/runs", { viz: "p97_osc", preset: "ball", seed: 5 });
  for (let i = 0; i < 200 && (await get(`/api/runs/${id}`)).state !== "running"; i++) await sleep(200);
  for (let i = 0; i < 8; i++) { await post(`/api/runs/${id}/command`, { cmd: "scene", args: { op: "add", type: "osc", values: { x: 0.1 * i, v: 0.2 } } }); await sleep(150); }
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  await sleep(3000);
  await post(`/api/runs/${id}/command`, { cmd: "pause" });
  await sleep(1000);
  const page = await br.newPage({ viewport: { width: 1280, height: 800 } });
  page.on("pageerror", (e) => errs2.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs2.push(`console: ${m.text()}`.slice(0, 300)); });
  await page.goto(inLang(`${base}/run?id=${id}`));
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && document.querySelector(".in-panel") && document.querySelector(".in-panel").style.display !== "none", null, { timeout: 60000 });
  await settle(page);
  const col = () => page.evaluate(() => { let e = document.querySelector(".in-panel"); while (e && e !== document.body) { const s = getComputedStyle(e); if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight) return { top: e.scrollTop, h: e.scrollHeight }; e = e.parentElement; } return null; });
  const setCol = (y) => page.evaluate((y) => { let e = document.querySelector(".in-panel"); while (e && e !== document.body) { const s = getComputedStyle(e); if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight) { e.scrollTop = y; return e.scrollTop; } e = e.parentElement; } return null; }, y);
  const group = (name) => `[...document.querySelectorAll(".in-panel details.in-group")].find((d) => d.querySelector("summary").textContent === ${JSON.stringify(name)})`;
  await page.locator(".in-panel").screenshot({ path: `${shots}/lb1_panel_before_ticks.png` });

  // F8 (1): fold "World", tick a quantity with the keyboard: the focus stays on it, "World" stays folded
  await page.evaluate(`${group(tr("World"))}.open = false`);
  const boxes = await page.$$(".in-panel .in-group input[type=checkbox]");
  const target = boxes[boxes.length - 2];
  const tid = await target.evaluate((b) => b.closest("label").title);
  await target.focus();
  await page.keyboard.press("Space");
  await settle(page);
  const a1 = await page.evaluate(`({ active: document.activeElement && document.activeElement.closest("label") ? document.activeElement.closest("label").title : document.activeElement.tagName, checked: document.activeElement.checked, worldOpen: ${group(tr("World"))}.open })`);
  check("F8 a ticked quantity keeps the focus", a1.active === tid && a1.checked === true, { tid, ...a1 });
  check("F8 a folded group stays folded", a1.worldOpen === false, a1);
  // F8 (2): the column's scroll when a quantity is ticked with the mouse (the list is not rebuilt). The click is the
  // element's own (Playwright's click would first scroll the box into view)
  await setCol(10000);
  const s0 = await col();
  await page.evaluate(() => { window.__rows = [...document.querySelectorAll(".in-panel .in-q")]; [...document.querySelectorAll(".in-panel .in-group input[type=checkbox]")].at(-3).click(); });
  await settle(page);
  const s1 = await col();
  const sameRows = await page.evaluate(() => { const now = [...document.querySelectorAll(".in-panel .in-q")]; return now.length === window.__rows.length && now.every((r, i) => r === window.__rows[i]); });
  check("F8 ticking keeps the column's scroll and the rows", s0 && s1 && Math.abs(s1.top - s0.top) < 2 && sameRows, { s0, s1, sameRows });
  // F8 (3): the sweep form keeps what was typed when folded and opened again
  await page.evaluate(() => { document.querySelector(".in-sweep-box").open = true; });
  await page.waitForSelector(".in-sweep select", { timeout: 20000 });
  await settle(page);
  await page.fill(`.in-sweep input[placeholder^='${EG}']`, "1; 2; 3");
  await page.evaluate(() => { document.querySelector(".in-sweep-box").open = false; });
  await settle(page);
  await page.evaluate(() => { document.querySelector(".in-sweep-box").open = true; });
  await settle(page);
  check("F8 the sweep form keeps what was typed", (await page.inputValue(`.in-sweep input[placeholder^='${EG}']`)) === "1; 2; 3");

  // X9: no unit twice; a law hidden by show_if is not offered (the schema has it, and the label names its unit)
  const viz = await get("/api/viz/p97_osc");
  const pre = viz.schema.params.find((p) => p.id === "damp")?.show_if && tr(viz.schema.params.find((p) => p.id === "alloc_mb").label).endsWith(tr("MB"));
  const opts = await page.$$eval(".in-sweep select:first-of-type option", (os) => os.map((o) => [o.value, o.textContent]));
  const twice = new RegExp(`${esc(tr("MB"))}, ${esc(tr("MB"))}|, (\\S+), \\1$`);
  check("X9 units once, the hidden law not offered", pre && opts.some(([v, x]) => v === "law:alloc_mb" && x === tr("Law: {label}", { label: tr("Hold memory, MB") }))
    && !opts.some(([, x]) => twice.test(x)) && !opts.some(([v]) => v === "law:damp") && opts.some(([, x]) => x === tr("Law: {label}", { label: `${tr("Spring stiffness")}, ${tr("N/m")}` })), { opts: opts.map((o) => o[1]) });

  // F1: "Set" of the ball's x (a handle): the stored value and where the ball is in the latest frame
  await page.selectOption(".in-sweep select >> nth=0", "obj:o2:x");
  await settle(page);
  const cur = await page.textContent(".in-sweep .in-cur");
  const sx = await get(`/api/runs/${id}/series?ids=o2.x`);
  const xNow = sx.values["o2.x"].at(-1);
  const F1 = "Set: {v} — where the object was put; the object is now at {at} (the last frame). Each value puts it there at the moment of the sweep, including one equal to the set value";
  const f1 = tr(F1, { v: `${fmt(1, ".6g")} ${tr("m")}`, at: "\u0002" });
  const m = new RegExp(esc(f1.split("\u0002")[0]) + `(\\S+) ${esc(tr("m"))}`).exec(cur);
  const shownNow = m ? Number(m[1].replace(",", ".").replace("−", "-")) : NaN;
  // (where the ball is depends on when the play stopped: the number is compared with the record's, not with 1)
  check("F1 \"Set\" and where the object is now", !!m && Math.abs(shownNow - xNow) < 1e-4 * Math.max(1, Math.abs(xNow)), { cur, xNow });

  // F8 (4), F7, X7: a running sweep — its table and plot updated in place, the column's scroll kept; then what it states
  await page.selectOption(".in-sweep select >> nth=0", "law:k");
  const form = page.locator(".in-sweep");
  check("X7 the duration's default follows the world's speed", (await form.locator(".ctl", { hasText: HOW }).textContent()).includes(tr("How long to compute, {unit}", { unit: tr("s") })) && (await form.locator(".ctl", { hasText: HOW }).locator("input").inputValue()) === "5");
  await form.locator(`input[placeholder^='${EG}']`).fill(Array.from({ length: 30 }, (_, i) => String(1 + i * 3)).join("; "));
  await form.locator(".ctl", { hasText: HOW }).locator("input").fill("300");
  await form.locator(".ctl", { hasText: WHAT_T }).locator("select").selectOption("max");
  await form.locator(".ctl", { hasText: WHAT_M }).locator("select").selectOption("E");
  const dtText = await page.textContent(".in-sweep .in-dt");
  const dt15 = `${fmt(1.5, ".6g")} ${tr("s")}`;
  check("F7 the readings' spacing next to their number", dtText === tr("{n:d} readings {dt} apart", { n: 201, dt: dt15 }), { dtText });
  await form.locator("button", { hasText: ESTIMATE }).click();
  await estimated(page);
  await form.locator("button", { hasText: START }).click();
  await page.waitForFunction(() => document.querySelectorAll(".in-sres .in-tab tbody tr").length >= 2, null, { timeout: 60000 });
  const estAfter = await page.textContent(".in-est"), goOff = await page.isDisabled(".in-sweep button.primary");
  check("X7 after a start the estimate is asked anew", estAfter === tr("First “Estimate”: the cost of computing from this world's step time.") && goOff, { estAfter });
  await setCol(10000);
  const c0 = await col();
  await page.evaluate(() => { window.__t = document.querySelector(".in-sres table"); window.__cv = document.querySelector(".in-sres canvas"); window.__r0 = document.querySelector(".in-sres tbody tr"); window.__n0 = document.querySelectorAll(".in-sres tbody tr").length; });
  await sleep(1600);
  const same = await page.evaluate(() => ({ table: window.__t === document.querySelector(".in-sres table"), canvas: window.__cv === document.querySelector(".in-sres canvas"), row: window.__r0 === document.querySelector(".in-sres tbody tr"), grew: document.querySelectorAll(".in-sres tbody tr").length >= window.__n0, state: document.querySelector(".in-sres .in-sh").textContent }));
  const c1 = await col();
  check("F8 a running sweep is updated in place, the scroll kept", same.table && same.canvas && same.row && same.grew && c0 && c1 && Math.abs(c1.top - c0.top) < 2, { same, c0, c1 });
  await shState(page, ".in-sres .in-sh", tr("done"));
  await settle(page);
  const what = await page.textContent(".in-sres .in-what");
  const sw = await get(`/api/runs/${id}/sweeps`);
  const n1 = sw.at(-1).n;
  const csv = (await (await fetch(`${base}/api/runs/${id}/sweeps/${n1}?format=csv`)).text()).split(/\r?\n/);
  const statTxt = tr({ $t: "the maximum over {n:d} readings {dt} apart", a: { n: 201, dt: { $t: "{x:.6g} s", a: { x: 1.5 } } } });
  const eachTxt = tr("{target} → {measure}, {stat}; each value — {duration} of the world from t = {t}", { target: "", measure: "\u0001", stat: statTxt, duration: `${fmt(300, ".6g")} ${tr("s")}`, t: "\u0002" }).split("\u0001")[1].split("\u0002")[0];
  check("F7 the result states the sampling and the base moment", what.includes(eachTxt), { what, eachTxt });
  check("F7 the table's CSV states them too", csv[0].startsWith("# sweep no. ") && /from t = .* 201 readings, 1\.5 s apart/.test(csv[1]) && /^# base_t=/.test(csv[2]) && !csv[3].startsWith("#"), { head: csv.slice(0, 4) });
  await page.locator(".in-panel").screenshot({ path: `${shots}/lb1_panel_after_sweep.png` });

  // F10: "✕ cancel" — one click is enough, what was computed is kept
  await form.locator(`input[placeholder^='${EG}']`).fill("1; 2; 3");
  await form.locator(".ctl", { hasText: HOW }).locator("input").fill("20000");  // ~8 s per value
  await form.locator(".ctl", { hasText: WHAT_T }).locator("select").selectOption("final");
  await form.locator("button", { hasText: ESTIMATE }).click();
  await page.waitForFunction(() => !document.querySelector(".in-sweep button.primary").disabled || document.querySelector(".in-est").classList.contains("in-bad"), null, { timeout: 30000 });
  if (await page.isDisabled(".in-sweep button.primary")) throw new Error("F10: the estimate refused the sweep: " + await page.textContent(".in-est"));
  await form.locator("button", { hasText: START }).click();
  await shState(page, ".in-sres .in-sh", tr("running"));
  await page.click(".in-sres button.cancel");
  const offAtOnce = await page.evaluate(() => document.querySelector(".in-sres button.cancel").disabled);
  await shState(page, ".in-sres .in-sh", tr("cancelled"));
  const s2 = await get(`/api/runs/${id}/sweeps/${(await get(`/api/runs/${id}/sweeps`)).at(-1).n}`);
  check("F10 one click cancels, the button is off at once, the sweep is kept", offAtOnce && s2.state === "cancelled" && await page.isVisible(`.in-sres .in-sh button:text('${tr("remove")}')`), { offAtOnce, state: s2.state });

  // X7: a sweep in which nothing was measured is "not computed"
  await form.locator(`input[placeholder^='${EG}']`).fill("200; 300");
  await form.locator(".ctl", { hasText: HOW }).locator("input").fill("1");
  await form.locator("button", { hasText: ESTIMATE }).click();
  await page.waitForFunction(() => !document.querySelector(".in-sweep button.primary").disabled, null, { timeout: 30000 });
  await form.locator("button", { hasText: START }).click();
  await shState(page, ".in-sres .in-sh", tr("not computed"));
  const none2 = tr("None of the {n:d} values was measured — the reasons per value are in the table", { n: 2 }).split(" — ")[0];
  check("X7 nothing measured is \"not computed\"", (await page.textContent(".in-sres .in-msg")).startsWith(none2));
  check("part 2: no page errors", errs2.length === 0, { errs: errs2.slice(0, 5) });
  await page.close();

  // X7: a slow world's duration in a smaller unit (speed 0.02: 5 wall seconds are 0.1 s → "100 ms"), sent in seconds
  const { id: id2 } = await post("/api/runs", { viz: "p97_osc", preset: "one", seed: 6 });
  for (let i = 0; i < 200 && (await get(`/api/runs/${id2}`)).state !== "running"; i++) await sleep(200);
  await post(`/api/runs/${id2}/command`, { cmd: "speed", args: { value: 0.02 } });
  await sleep(500);
  const p2 = await br.newPage({ viewport: { width: 1280, height: 800 } });
  await p2.goto(inLang(`${base}/run?id=${id2}`));
  await p2.waitForFunction(() => window.__lfPlayer && document.querySelector(".in-panel") && document.querySelector(".in-panel").style.display !== "none", null, { timeout: 60000 });
  await p2.evaluate(() => { document.querySelector(".in-sweep-box").open = true; });
  await p2.waitForSelector(".in-sweep select", { timeout: 20000 });
  await settle(p2);
  const f2 = p2.locator(".in-sweep");
  const durCtl = f2.locator(".ctl", { hasText: HOW });
  const lab = await durCtl.textContent(), dv = await durCtl.locator("input").inputValue();
  await p2.selectOption(".in-sweep select >> nth=0", "law:k");
  await f2.locator(`input[placeholder^='${EG}']`).fill("4");
  await f2.locator("button", { hasText: ESTIMATE }).click();
  await p2.waitForFunction(() => !document.querySelector(".in-sweep button.primary").disabled, null, { timeout: 30000 });
  await f2.locator("button", { hasText: START }).click();
  await shState(p2, ".in-sres .in-sh", tr("done"));
  const s3 = await get(`/api/runs/${id2}/sweeps/${(await get(`/api/runs/${id2}/sweeps`)).at(-1).n}`);
  check("X7 a slow world's duration in ms, sent in s", lab.includes(tr("How long to compute, {unit}", { unit: tr("ms") })) && dv === "100" && Math.abs(s3.request.duration - 0.1) < 1e-12, { lab, dv, duration: s3.request.duration });
  await p2.close();
} catch (e) { failed++; console.log(JSON.stringify({ failed_part2: e.message, errs: errs2.slice(0, 5) })); }
await br.close();
console.log(failed ? `FAILED: ${failed}` : "all checks passed");
process.exit(failed ? 1 : 0);
