// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// S03's view on its Explore screen in a browser (STATUS.md V52 (e), (f)), in the language of LFVIZ_LANG (en by
// default), at every viewport size given (1280x800 and 390x844 by default). What the view drew where comes from the
// canvas's `__layout` (s03_projectile/web/view.js, written at every frame):
//  - «h = … m» at every computed point with a table (every h > 0, every speed, angle and air of the atlas): drawn,
//    inside the view and clear of the launcher (the chute, or the barrel with its width);
//  - the «forces» overlay with the air on: the drag arrow at the top of the path of the default throw is a clear arrow
//    beside the ball (at least 30 px), and at the top of every 45° throw from h ≤ 2 m, every speed, at least 10 px;
//    the longest drag arrow of a throw from the floor (at its launch) is at most twice the weight's (120 px) and, when
//    enlarged, at least 48 px; the legend says the drag's scale: «drag, enlarged ×m: …» when m > 1, else «drag, on the
//    weight's scale: …», and on a phone its rows run neither under the readouts laid over the view's corner nor over the
//    computed path;
//  - no page error; screenshots of the forces at the top of the path.
// Run against a PRIVATE server with S03's atlases built by the code under test (site/record.py --world s03_projectile),
// never the shared one on 8479; the commands are those of u32_double_slit/tests/u32_screens.mjs, with this file:
//   sh -c "cp /v/tests/browser/lfi18n.mjs /v/s03_projectile/tests/s03_screens.mjs /pw/ && node /pw/s03_screens.mjs 8696"
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { LANG, inLang, loadI18n } from "./lfi18n.mjs";

const port = process.argv[2] || "8696";
const SIZES = (process.argv[3] || "1280x800,390x844").split(",").map((s) => s.split("x").map(Number));
const base = `http://127.0.0.1:${port}`;
const SHOTS = process.env.SHOTS || "/pw/shots";
mkdirSync(SHOTS, { recursive: true });
const WORLD = "s03_projectile";
let failed = 0;
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: `${LANG} ${name}`, ok: !!ok, ...info })); };
const settle = (page, ms = 60) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
const { t: tr } = await loadI18n(base);
const X = "(window.__lfExplore || {}).explore";
const layout = (page) => page.evaluate(() => { const c = document.querySelector(".dm-screen:not([hidden]) .dm-stage canvas"); return c && c.__layout ? JSON.parse(JSON.stringify(c.__layout)) : null; });

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
for (const [W, H] of SIZES) {
  const tag = `${W}x${H}`;
  const ctx = await br.newContext({ viewport: { width: W, height: H } });
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 200)); });
  await page.goto(inLang(`${base}/run?demo=${WORLD}&screen=explore`));
  await page.waitForFunction(`${X} && ${X}.point()`, null, { timeout: 30000 });
  const mf = await page.evaluate(`${X}.atlas.manifest`);
  const grid = Object.fromEntries(mf.controls.map((c) => [c.param, c.values]));
  const flat = (v) => mf.controls.reduce((i, c) => i * c.values.length + c.values.indexOf(v[c.param]), 0);
  // a point chosen as a student does, by a tap on each detent (a toggle's button), then shown
  const pick = async (vals) => {
    await page.evaluate(([v, g]) => {
      const E = (window.__lfExplore || {}).explore;
      for (const [p, x] of Object.entries(v)) {
        if (E.values()[p] === x) continue;
        const row = document.querySelector(`.dm-screen:not([hidden]) .dm-ctl[data-param="${p}"]`);
        if (typeof x === "boolean") row.querySelector(`.dm-ctl-seg button[data-value='${JSON.stringify(x)}']`).click();
        else row.querySelectorAll(".dm-detent")[g[p].indexOf(x)].click();
      }
    }, [vals, grid]);
    await page.waitForFunction(([v]) => { const p = (window.__lfExplore || {}).explore.point(); return p && Object.entries(v).every(([k, x]) => p.values[k] === x); }, [vals], { timeout: 20000 });
    await settle(page);
  };
  // --- V52 (e): «h = … m» clear of the launcher at every computed point with a table --------------------------------
  const bad = [];
  let n = 0;
  for (const air of grid.air) for (const h of grid.h_m.filter((x) => x > 0)) for (const v0 of grid.v0) for (const angle_deg of grid.angle_deg) {
    const vals = { air, h_m: h, v0, angle_deg };
    if (mf.points[flat(vals)][2] !== 0) continue;  // refused
    await pick(vals);
    const L = await layout(page);
    n++;
    const a = L && L.hLabel, b = L && L.launcher;
    const over = a && b && a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];
    const inside = a && a[0] >= 0 && a[1] >= 0 && a[2] <= L.W && a[3] <= L.H;
    if (!a || over || !inside) bad.push({ ...vals, label: a, launcher: b, where: L && L.hWhere });
  }
  check(`${tag} explore: «h = … m» drawn inside the view and clear of the launcher at every computed point with a table (V52 (e))`,
    n > 0 && !bad.length, { points: n, bad: bad.slice(0, 5), nbad: bad.length });
  // --- V52 (f): the drag on a scale of its own --------------------------------------------------------------------------
  if (W < 1000) await page.locator(".dm-screen:not([hidden]) .dm-overlays > summary").click().catch(() => {});
  await page.locator('.dm-screen:not([hidden]) input[data-overlay="forces"]').check();
  const scrub = async (k) => { await page.evaluate((j) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(j); s.dispatchEvent(new Event("input")); }, k); await settle(page); };
  const launch = async () => {
    await page.locator(".dm-screen:not([hidden]) .dm-play").click();
    await page.waitForFunction(`${X}.state.cur && ${X}.state.cur.launchedAt !== null && !${X}.state.playing`, null, { timeout: 30000 });
  };
  const apexFrame = () => page.evaluate(`(() => { const F = ${X}.point().W.frames; return F.findIndex((f) => f.meta.vy <= 0); })()`);
  // the legend's text as the view wrote it: «drag, enlarged ×m: …» with this point's m, else «… on the weight's scale: …»
  const legendOk = (L) => !!(L && L.drag && L.dragLegend && L.dragLegend.startsWith((L.drag.m > 1
    ? tr("drag, enlarged ×{m}: {F} N", { m: String(L.drag.m), F: "\u0001" }) : tr("drag, on the weight's scale: {F} N", { F: "\u0001" })).split("\u0001")[0]));
  const def = Object.fromEntries(mf.controls.map((c) => [c.param, c.default]));
  const rows = [];
  for (const h of grid.h_m.filter((x) => x <= 2)) for (const v0 of grid.v0) {
    await pick({ air: true, h_m: h, v0, angle_deg: 45 });
    await launch();
    await scrub(await apexFrame());
    const L = await layout(page);
    const lg = L && L.legend, rb = lg && lg.readouts, lr = lg && lg.rows;
    // clear of the readouts' box (a phone), and then above the computed path too (the scene kept under the rows)
    const clear = !!lr && (!rb || (!(lr[0] < rb[2] && rb[0] < lr[2] && lr[1] < rb[3] && rb[1] < lr[3]) && lr[3] <= lg.pathTop + 1));
    rows.push({ h, v0, px: L && L.drag ? Math.round(L.drag.px) : null, m: L && L.drag ? L.drag.m : null, legend: !!legendOk(L) && clear });
    if (h === def.h_m && v0 === def.v0) {
      check(`${tag} explore: the default throw in air, at the top of its path: the drag arrow at least 30 px, its scale in the legend, clear of the readouts (V52 (f))`,
        L && L.drag && L.drag.px >= 30 && legendOk(L) && clear, { drag: L && L.drag, legend: L && L.dragLegend, at: lg });
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: `${SHOTS}/s03_forces_apex_${LANG}_${tag}.png` });
    }
  }
  check(`${tag} explore: at the top of every 45° throw in air from h ≤ 2 m the drag arrow at least 10 px, and the legend says its scale, clear of the readouts (V52 (f))`,
    rows.every((r) => r.px >= 10 && r.legend), { rows });
  const launchRows = [];
  for (const v0 of grid.v0) {  // from the floor the largest drag is at the launch
    await pick({ air: true, h_m: 0, v0, angle_deg: 45 });
    await launch();
    await scrub(0);
    const L = await layout(page);
    launchRows.push({ v0, px: L && L.drag ? Math.round(L.drag.px) : null, m: L && L.drag ? L.drag.m : null });
  }
  check(`${tag} explore: a throw from the floor in air: its largest drag (at the launch) drawn at most 120 px, at least 48 px when enlarged (V52 (f))`,
    launchRows.every((r) => r.px !== null && r.px <= 120.5 && (r.m === 1 || r.px >= 47.5)), { launchRows });
  check(`${tag}: no page error`, errs.length === 0, { errs });
  await ctx.close();
}
await br.close();
console.log(failed ? `FAILED: ${failed}` : "all passed");
process.exit(failed ? 1 : 0);
