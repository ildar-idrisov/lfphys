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
//     sh -c "cp /t/instruments_checks.mjs /pw/ && node /pw/instruments_checks.mjs 8592 /pw/shots"
// Prints one JSON line per check and exits with code 1 when one fails.
import { chromium } from "playwright";
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
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка записи/.test(document.querySelector("#status").textContent || ""), null, { timeout: 60000 });
  await settle(page);

  // 1. the panel: shown, the quantities grouped, the first world-wide ones plotted
  const st = await page.evaluate(() => ({
    shown: !!document.querySelector(".in-panel") && document.querySelector(".in-panel").style.display !== "none",
    groups: [...document.querySelectorAll(".in-panel .in-group > summary")].map((s) => s.textContent),
    names: [...document.querySelectorAll(".in-panel .in-q .in-name")].map((s) => s.textContent),
    plots: [...document.querySelectorAll(".in-panel .in-plot .in-pt")].map((s) => s.textContent),
    state: window.lfInstruments.state() }));
  check("panel listed", st.shown && st.groups.join() === "Мир,Осцилляторы" && st.names.includes("Осциллятор 1: положение, м")
    && st.plots.join("|") === "Полная энергия, Дж|Положение первого осциллятора, м", st);

  // 2. choose a probe's quantity: a third plot, drawn (pixels of the line's colour)
  await page.locator(".in-q", { hasText: "Осциллятор 1: положение" }).locator("input").check();
  await settle(page);
  const drawn = await page.evaluate(() => {
    const cv = [...document.querySelectorAll(".in-plot")].find((p) => p.textContent.startsWith("Осциллятор 1: положение")).querySelector("canvas");
    const d = cv.getContext("2d").getImageData(0, 0, cv.width, cv.height).data;
    const bg = [d[0], d[1], d[2]];
    let n = 0; for (let i = 0; i < d.length; i += 4) if (Math.abs(d[i] - bg[0]) + Math.abs(d[i + 1] - bg[1]) + Math.abs(d[i + 2] - bg[2]) > 60) n++;
    return { n, w: cv.width, h: cv.height };
  });
  check("plot drawn", drawn.n > 200, drawn);

  // 3. the cursor in the middle of the history: the value shown is the record's at that time
  const nf = await page.evaluate(() => window.__lfPlayer.frames());
  await page.evaluate((i) => window.__lfPlayer.goTo(i), Math.round(nf / 2));
  await settle(page);
  const tc = await page.evaluate(() => window.__lfPlayer.t());
  const ser = await get(`/api/runs/${id}/series?ids=o1.x&to=${tc}`);
  const xr = ser.values["o1.x"][ser.values["o1.x"].length - 1];
  const shown = await page.evaluate(() => [...document.querySelectorAll(".in-plot")].find((p) => p.textContent.startsWith("Осциллятор 1: положение")).querySelector(".in-pv").textContent);
  const shownNum = Number(shown.split(" ")[0].replace(/\s/g, "").replace(",", ".").replace("−", "-"));
  check("value at cursor", ser.t[ser.t.length - 1] === tc && Math.abs(shownNum - xr) < 1e-5 * Math.max(1, Math.abs(xr)) && Math.abs(xr - xv(tc, 1, 0, 4)[0]) < 1e-12, { tc, shown, xr });
  await page.locator(".in-panel").screenshot({ path: `${shots}/instruments_panel.png` });

  // 4. the CSV link: the record's values, the header with units
  const csv = await page.evaluate(async () => { const a = document.querySelector(".in-panel .in-csv"); const r = await fetch(a.href); return { href: a.href, text: await r.text() }; });
  const lines = csv.text.trim().split(/\r?\n/);
  check("csv", lines[0] === "\"t, с\",\"Полная энергия, Дж [E]\",\"Положение первого осциллятора, м [x_first]\",\"Осциллятор 1: положение, м [o1.x]\"" && lines.length - 1 === (await get(`/api/runs/${id}/series?ids=E&max_points=50000`)).n_frames, { head: lines[0], rows: lines.length - 1 });

  // 5. a sweep from the panel: the spring constant, the position after 0.7 s
  await page.evaluate(() => { document.querySelector(".in-sweep-box").open = true; });
  await page.waitForSelector(".in-sweep select", { timeout: 20000 });
  await page.selectOption(".in-sweep select >> nth=0", "law:k");
  const form = page.locator(".in-sweep");
  await form.locator("input[placeholder^='например']").fill("1; 4; 9; 16");
  await form.locator(".ctl", { hasText: "Сколько считать" }).locator("input").fill("0,7");
  await form.locator(".ctl", { hasText: "Что измерять" }).locator("select").selectOption("o1.x");
  await form.locator("button", { hasText: "Оценить" }).click();
  await page.waitForFunction(() => /≈|не измерила/.test(document.querySelector(".in-est").textContent), null, { timeout: 30000 });
  const estText = await page.textContent(".in-est");
  check("estimate shown", /^≈ .*предел 10 мин/.test(estText), { estText });
  await form.locator("button", { hasText: "Запустить свип" }).click();
  await page.waitForFunction(() => /готово/.test((document.querySelector(".in-sh") || {}).textContent || ""), null, { timeout: 120000 });
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
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && document.querySelector(".in-panel") && document.querySelector(".in-panel").style.display !== "none", null, { timeout: 60000 });
  await settle(page);
  const col = () => page.evaluate(() => { let e = document.querySelector(".in-panel"); while (e && e !== document.body) { const s = getComputedStyle(e); if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight) return { top: e.scrollTop, h: e.scrollHeight }; e = e.parentElement; } return null; });
  const setCol = (y) => page.evaluate((y) => { let e = document.querySelector(".in-panel"); while (e && e !== document.body) { const s = getComputedStyle(e); if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight) { e.scrollTop = y; return e.scrollTop; } e = e.parentElement; } return null; }, y);
  const group = (name) => `[...document.querySelectorAll(".in-panel details.in-group")].find((d) => d.querySelector("summary").textContent === ${JSON.stringify(name)})`;
  await page.locator(".in-panel").screenshot({ path: `${shots}/lb1_panel_before_ticks.png` });

  // F8 (1): fold «Мир», tick a quantity with the keyboard: the focus stays on it, «Мир» stays folded
  await page.evaluate(`${group("Мир")}.open = false`);
  const boxes = await page.$$(".in-panel .in-group input[type=checkbox]");
  const target = boxes[boxes.length - 2];
  const tid = await target.evaluate((b) => b.closest("label").title);
  await target.focus();
  await page.keyboard.press("Space");
  await settle(page);
  const a1 = await page.evaluate(`({ active: document.activeElement && document.activeElement.closest("label") ? document.activeElement.closest("label").title : document.activeElement.tagName, checked: document.activeElement.checked, worldOpen: ${group("Мир")}.open })`);
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
  await page.fill(".in-sweep input[placeholder^='например']", "1; 2; 3");
  await page.evaluate(() => { document.querySelector(".in-sweep-box").open = false; });
  await settle(page);
  await page.evaluate(() => { document.querySelector(".in-sweep-box").open = true; });
  await settle(page);
  check("F8 the sweep form keeps what was typed", (await page.inputValue(".in-sweep input[placeholder^='например']")) === "1; 2; 3");

  // X9: no unit twice; a law hidden by show_if is not offered (the schema has it, and the label names its unit)
  const viz = await get("/api/viz/p97_osc");
  const pre = viz.schema.params.find((p) => p.id === "damp")?.show_if && viz.schema.params.find((p) => p.id === "alloc_mb").label.endsWith("МБ");
  const opts = await page.$$eval(".in-sweep select:first-of-type option", (os) => os.map((o) => [o.value, o.textContent]));
  check("X9 units once, the hidden law not offered", pre && opts.some(([v, t]) => v === "law:alloc_mb" && t === "Закон: Занять память, МБ")
    && !opts.some(([, t]) => /МБ, МБ|, (\S+), \1$/.test(t)) && !opts.some(([v]) => v === "law:damp") && opts.some(([, t]) => t === "Закон: Жёсткость пружины, Н/м"), { opts: opts.map((o) => o[1]) });

  // F1: «Задано» of the ball's x (a handle): the stored value and where the ball is in the latest frame
  await page.selectOption(".in-sweep select >> nth=0", "obj:o2:x");
  await settle(page);
  const cur = await page.textContent(".in-sweep .in-cur");
  const sx = await get(`/api/runs/${id}/series?ids=o2.x`);
  const xNow = sx.values["o2.x"].at(-1);
  const m = /объект сейчас в (\S+) м/.exec(cur);
  const shownNow = m ? Number(m[1].replace(",", ".").replace("−", "-")) : NaN;
  // (where the ball is depends on when the play stopped: the number is compared with the record's, not with 1)
  check("F1 «Задано» and where the object is now", cur.startsWith("Задано: 1 м — где объект поставили") && Math.abs(shownNow - xNow) < 1e-4 * Math.max(1, Math.abs(xNow)), { cur, xNow });

  // F8 (4), F7, X7: a running sweep — its table and plot updated in place, the column's scroll kept; then what it states
  await page.selectOption(".in-sweep select >> nth=0", "law:k");
  const form = page.locator(".in-sweep");
  check("X7 the duration's default follows the world's speed", (await form.locator(".ctl", { hasText: "Сколько считать" }).textContent()).includes("Сколько считать, с") && (await form.locator(".ctl", { hasText: "Сколько считать" }).locator("input").inputValue()) === "5");
  await form.locator("input[placeholder^='например']").fill(Array.from({ length: 30 }, (_, i) => String(1 + i * 3)).join("; "));
  await form.locator(".ctl", { hasText: "Сколько считать" }).locator("input").fill("300");
  await form.locator(".ctl", { hasText: "Что взять" }).locator("select").selectOption("max");
  await form.locator(".ctl", { hasText: "Что измерять" }).locator("select").selectOption("E");
  const dtText = await page.textContent(".in-sweep .in-dt");
  check("F7 the readings' spacing next to their number", dtText === "201 замеров через 1,5 с", { dtText });
  await form.locator("button", { hasText: "Оценить" }).click();
  await page.waitForFunction(() => /≈|не измерила/.test(document.querySelector(".in-est").textContent), null, { timeout: 30000 });
  await form.locator("button", { hasText: "Запустить свип" }).click();
  await page.waitForFunction(() => document.querySelectorAll(".in-sres .in-tab tbody tr").length >= 2, null, { timeout: 60000 });
  const estAfter = await page.textContent(".in-est"), goOff = await page.isDisabled(".in-sweep button.primary");
  check("X7 after a start the estimate is asked anew", estAfter.startsWith("Сначала «Оценить»") && goOff, { estAfter });
  await setCol(10000);
  const c0 = await col();
  await page.evaluate(() => { window.__t = document.querySelector(".in-sres table"); window.__cv = document.querySelector(".in-sres canvas"); window.__r0 = document.querySelector(".in-sres tbody tr"); window.__n0 = document.querySelectorAll(".in-sres tbody tr").length; });
  await sleep(1600);
  const same = await page.evaluate(() => ({ table: window.__t === document.querySelector(".in-sres table"), canvas: window.__cv === document.querySelector(".in-sres canvas"), row: window.__r0 === document.querySelector(".in-sres tbody tr"), grew: document.querySelectorAll(".in-sres tbody tr").length >= window.__n0, state: document.querySelector(".in-sres .in-sh").textContent }));
  const c1 = await col();
  check("F8 a running sweep is updated in place, the scroll kept", same.table && same.canvas && same.row && same.grew && c0 && c1 && Math.abs(c1.top - c0.top) < 2, { same, c0, c1 });
  await page.waitForFunction(() => /готово/.test(document.querySelector(".in-sres .in-sh").textContent), null, { timeout: 120000 });
  await settle(page);
  const what = await page.textContent(".in-sres .in-what");
  const sw = await get(`/api/runs/${id}/sweeps`);
  const n1 = sw.at(-1).n;
  const csv = (await (await fetch(`${base}/api/runs/${id}/sweeps/${n1}?format=csv`)).text()).split(/\r?\n/);
  check("F7 the result states the sampling and the base moment", /максимум по 201 замеру через 1,5 с; каждое значение — 300 с мира от t = /.test(what), { what });
  check("F7 the table's CSV states them too", csv[0].startsWith("# свип № ") && /от t = .* замеров 201 через 1,5 с/.test(csv[1]) && /^# base_t=/.test(csv[2]) && !csv[3].startsWith("#"), { head: csv.slice(0, 4) });
  await page.locator(".in-panel").screenshot({ path: `${shots}/lb1_panel_after_sweep.png` });

  // F10: «✕ отменить» — one click is enough, what was computed is kept
  await form.locator("input[placeholder^='например']").fill("1; 2; 3");
  await form.locator(".ctl", { hasText: "Сколько считать" }).locator("input").fill("20000");  // ~8 s per value
  await form.locator(".ctl", { hasText: "Что взять" }).locator("select").selectOption("final");
  await form.locator("button", { hasText: "Оценить" }).click();
  await page.waitForFunction(() => !document.querySelector(".in-sweep button.primary").disabled || document.querySelector(".in-est").classList.contains("in-bad"), null, { timeout: 30000 });
  if (await page.isDisabled(".in-sweep button.primary")) throw new Error("F10: the estimate refused the sweep: " + await page.textContent(".in-est"));
  await form.locator("button", { hasText: "Запустить свип" }).click();
  await page.waitForFunction(() => /считается/.test((document.querySelector(".in-sres .in-sh") || {}).textContent || ""), null, { timeout: 60000 });
  await page.click(".in-sres button.cancel");
  const offAtOnce = await page.evaluate(() => document.querySelector(".in-sres button.cancel").disabled);
  await page.waitForFunction(() => /отменён/.test(document.querySelector(".in-sres .in-sh").textContent), null, { timeout: 60000 });
  const s2 = await get(`/api/runs/${id}/sweeps/${(await get(`/api/runs/${id}/sweeps`)).at(-1).n}`);
  check("F10 one click cancels, the button is off at once, the sweep is kept", offAtOnce && s2.state === "cancelled" && await page.isVisible(".in-sres .in-sh button:text('удалить')"), { offAtOnce, state: s2.state });

  // X7: a sweep in which nothing was measured is «не посчитан»
  await form.locator("input[placeholder^='например']").fill("200; 300");
  await form.locator(".ctl", { hasText: "Сколько считать" }).locator("input").fill("1");
  await form.locator("button", { hasText: "Оценить" }).click();
  await page.waitForFunction(() => !document.querySelector(".in-sweep button.primary").disabled, null, { timeout: 30000 });
  await form.locator("button", { hasText: "Запустить свип" }).click();
  await page.waitForFunction(() => /не посчитан/.test((document.querySelector(".in-sres .in-sh") || {}).textContent || ""), null, { timeout: 60000 });
  check("X7 nothing measured is «не посчитан»", /^Не измерено ни одно из 2 значений/.test(await page.textContent(".in-sres .in-msg")));
  check("part 2: no page errors", errs2.length === 0, { errs: errs2.slice(0, 5) });
  await page.close();

  // X7: a slow world's duration in a smaller unit (speed 0.02: 5 wall seconds are 0,1 s → «100 мс»), sent in seconds
  const { id: id2 } = await post("/api/runs", { viz: "p97_osc", preset: "one", seed: 6 });
  for (let i = 0; i < 200 && (await get(`/api/runs/${id2}`)).state !== "running"; i++) await sleep(200);
  await post(`/api/runs/${id2}/command`, { cmd: "speed", args: { value: 0.02 } });
  await sleep(500);
  const p2 = await br.newPage({ viewport: { width: 1280, height: 800 } });
  await p2.goto(`${base}/run?id=${id2}`);
  await p2.waitForFunction(() => window.__lfPlayer && document.querySelector(".in-panel") && document.querySelector(".in-panel").style.display !== "none", null, { timeout: 60000 });
  await p2.evaluate(() => { document.querySelector(".in-sweep-box").open = true; });
  await p2.waitForSelector(".in-sweep select", { timeout: 20000 });
  await settle(p2);
  const f2 = p2.locator(".in-sweep");
  const durCtl = f2.locator(".ctl", { hasText: "Сколько считать" });
  const lab = await durCtl.textContent(), dv = await durCtl.locator("input").inputValue();
  await p2.selectOption(".in-sweep select >> nth=0", "law:k");
  await f2.locator("input[placeholder^='например']").fill("4");
  await f2.locator("button", { hasText: "Оценить" }).click();
  await p2.waitForFunction(() => !document.querySelector(".in-sweep button.primary").disabled, null, { timeout: 30000 });
  await f2.locator("button", { hasText: "Запустить свип" }).click();
  await p2.waitForFunction(() => /готово/.test((document.querySelector(".in-sres .in-sh") || {}).textContent || ""), null, { timeout: 60000 });
  const s3 = await get(`/api/runs/${id2}/sweeps/${(await get(`/api/runs/${id2}/sweeps`)).at(-1).n}`);
  check("X7 a slow world's duration in ms, sent in s", lab.includes("Сколько считать, мс") && dv === "100" && Math.abs(s3.request.duration - 0.1) < 1e-12, { lab, dv, duration: s3.request.duration });
  await p2.close();
} catch (e) { failed++; console.log(JSON.stringify({ failed_part2: e.message, errs: errs2.slice(0, 5) })); }
await br.close();
console.log(failed ? `FAILED: ${failed}` : "all checks passed");
process.exit(failed ? 1 : 0);
