// R-P probe: the lab's honesty in the browser (S03, server): a race between two picks; the reading of the ruler vs the
// shown point; the manual stopwatch frozen by a pause; Space on «Measure»; duplicate rows; sizes at 390
import { chromium } from "playwright";
const port = process.argv[2] || "8702", base = `http://127.0.0.1:${port}`;
const LANG = process.env.LFVIZ_LANG || "en";
const SH = process.env.SHOTS || "/pw/shots";
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const settle = (page, ms = 300) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
// delay the point of h = 0.3 m (flat index 2 of lab.heights) by 2.5 s
const man = await (await fetch(`${base}/api/recordings`)).json();
const ent = man.worlds.s03_projectile.atlases.find((a) => a.id === "lab.heights");
const mf = await (await fetch(`${base}/recordings/s03_projectile/${ent.file}`)).json();
const slowFile = mf.points[2][0];
await ctx.route(new RegExp(slowFile.replace(".", "\\.")), async (route) => { await sleep(2500); await route.continue(); });
const page = await ctx.newPage();
const errs = []; page.on("pageerror", (e) => errs.push(e.message));
await page.goto(`${base}/run?demo=s03_projectile&screen=lab&lang=${LANG}`);
await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 30000 });
await page.evaluate(() => { localStorage.clear(); });
const det = (k) => page.locator('.dm-screen:not([hidden]) .dm-ctl[data-param="h_m"] .dm-detent').nth(k);
// 1. the race: h = 0.30 (slow), then at once h = 0.80 (fast)
await det(2).click(); await det(12).click();
await sleep(4000); await settle(page);
const race = await page.evaluate(() => { const s = window.__lfLab.step(); return { slider: s.values.h_m, shown: s.cur.pt.values.h_m }; });
out("race: two picks in a row (the first point slow)", race);
// launch to the end and measure
await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max; s.dispatchEvent(new Event("input")); });
await settle(page, 100);
await page.locator(".dm-measure").click(); await settle(page, 200);
const row = await page.evaluate(() => { const r = window.__lfLab.rows().slice(-1)[0]; return { values: r.values, h: r.cols.h, L: r.cols.L }; });
out("race: the row measured", { row, Lof030: 0.371, Lof080: 0.605 });
await page.screenshot({ path: `${SH}/rp_lab_race_${LANG}.png` });
// 2. the stopwatch: launch, pause near the landing (Space), Stop: the reading equals the world time shown
await det(8).click(); await page.waitForFunction(() => window.__lfLab.step().cur.pt.values.h_m === 0.6);
await page.locator(".dm-play").click();
const T = await page.evaluate(() => { const s = window.__lfLab.step(); return s.cur.pt.W.events.find((e) => e.kind === "landing").t; });
await page.waitForFunction((T) => { const s = window.__lfLab.step(); return s.clock - s.cur.launchedAt >= T; }, T, { timeout: 10000, polling: "raf" });
await page.keyboard.press("Space");  // a pause, by the keyboard
await sleep(1500);
await page.locator(".dm-sw-btn").click(); await settle(page, 100);
const sw = await page.evaluate(() => { const s = window.__lfLab.step(); return { sw: s.sw.t, clock: s.clock - s.cur.launchedAt, paused: window.__lfLab.state.paused }; });
out("stopwatch: paused at the landing, then ⏱ Stop after 1.5 s", { T, ...sw, shown: await page.locator(".dm-sw-read").innerText() });
// 3. Space on the focused «Measure» button
const n0 = await page.evaluate(() => window.__lfLab.rows().length);
await page.locator(".dm-measure").focus();
const p0 = await page.evaluate(() => window.__lfLab.state.playing);
await page.keyboard.press("Space"); await settle(page, 200);
const n1 = await page.evaluate(() => window.__lfLab.rows().length);
out("Space on the focused «Measure»", { rowsBefore: n0, rowsAfter: n1, playingBefore: p0, playingAfter: await page.evaluate(() => window.__lfLab.state.playing) });
// 4. duplicates: «Measure» five times on one point adds five equal rows
await page.locator(".dm-reset").click();
await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max; s.dispatchEvent(new Event("input")); });
await settle(page, 100);
for (let i = 0; i < 5; i++) await page.locator(".dm-measure").click();
const dup = await page.evaluate(() => window.__lfLab.rows().slice(-5).map((r) => `${r.cols.h.v}/${r.cols.L.v}`));
out("five «Measure» on one point", { rows: dup, msg: await page.locator(".dm-msg").innerText() });
// 5. sizes at 390 of ▶, ⟲, Measure, ⏱ Stop, Check
await page.setViewportSize({ width: 390, height: 844 }); await settle(page, 400);
const sz = await page.evaluate(() => Object.fromEntries([".dm-play", ".dm-reset", ".dm-measure", ".dm-sw-btn", ".dm-check-law", ".dm-steps button", ".dm-del", ".dm-chap"].map((q) => { const e = document.querySelector(`.dm-screen:not([hidden]) ${q}`); if (!e) return [q, null]; const r = e.getBoundingClientRect(); return [q, `${Math.round(r.width)}x${Math.round(r.height)}`]; })));
out("390: sizes", sz);
const sw390 = await page.evaluate(() => document.scrollingElement.scrollWidth);
out("390: scrollWidth", { sw390 });
out("page errors", { errs });
await br.close();
