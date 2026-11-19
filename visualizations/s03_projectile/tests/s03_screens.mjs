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
// EX2 (design explore_EX2_2026-11-18 §1.3, §7, §10), from the same `__layout`:
//  - Watch: at every caption (and at the end of the flight it describes) the caption, laid over the stage on a wide
//    screen, covers neither the scene's box (the computed paths, the floor), nor a landing's mark or label, nor the
//    earlier throws' marks;
//  - Lab work draws what Explore draws (nothing hidden): in part 1 with the air on, «h = … m», the landing's mark and
//    its label, and the Magnus force of the rolling ball under «forces» at the launch;
//  - at 390 px the view, the step's control and «Measure» on the screen together;
//  - on every screen no horizontal scroll and no text out of its box (the canvas's labels inside the canvas; the
//    controls' and the readouts' texts inside their boxes).
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
const overlap = (a, b) => !!(a && b && a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3]);
// no horizontal scroll; no text out of its box: the canvas's labels (its layout's marks) inside the canvas, and the
// screen's controls, readouts, buttons and captions not wider than their boxes
async function noOverflow(page, tag) {
  const r = await page.evaluate(() => {
    const scr = document.querySelector(".dm-screen:not([hidden])");
    const c = scr && scr.querySelector(".dm-stage canvas"), L = c && c.__layout;
    const out = L ? (L.marks || []).filter((m) => m.box && (m.box[0] < -1 || m.box[1] < -1 || m.box[2] > L.W + 1 || m.box[3] > L.H + 1)).map((m) => m.kind) : [];
    const sel = ".dm-ctl label, .dm-ctl-value, .dm-readouts > *, button, .dm-caption, .dm-time, .dm-msg, summary";
    // (the sliders' detents are ticks whose numbers stand under them by design: not text boxes)
    const wide = [...scr.querySelectorAll(sel)].filter((e) => !e.classList.contains("dm-detent") && e.offsetParent !== null && getComputedStyle(e).overflowX !== "auto"
      && e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0).map((e) => (e.className || e.tagName) + ": " + e.textContent.slice(0, 40));
    return { sw: document.documentElement.scrollWidth, W: innerWidth, out, wide };
  });
  check(`${tag}: no horizontal scroll`, r.sw <= r.W, { scrollWidth: r.sw, width: r.W });
  check(`${tag}: no text out of its box (the canvas's labels, the controls, the readouts)`, !r.out.length && !r.wide.length, r);
}
// Watch: a caption never covers what it describes (D8): at each caption's frame and at the last frame before the next
async function watchCaptions(W, H, tag) {
  const ctx = await br.newContext({ viewport: { width: W, height: H } });
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  await page.goto(inLang(`${base}/run?demo=${WORLD}&screen=watch`));
  await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 30000 });
  // (a scrub of the time bar pauses the story: watch.js go)
  const caps = await page.evaluate(() => window.__lfWatch.state.story.captions.map((c) => c.step));
  const nSteps = await page.evaluate(() => window.__lfWatch.state.story.steps.length);
  const bad = [];
  const at = async (k) => {
    await page.evaluate((j) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(j); s.dispatchEvent(new Event("input")); }, k);
    await settle(page, 80);
    const r = await page.evaluate(() => {
      const scr = document.querySelector(".dm-screen:not([hidden])"), c = scr.querySelector(".dm-stage canvas"), cap = scr.querySelector(".dm-caption");
      const a = c.getBoundingClientRect(), b = cap.getBoundingClientRect();
      return { L: c.__layout ? JSON.parse(JSON.stringify(c.__layout)) : null, cap: [b.left - a.left, b.top - a.top, b.right - a.left, b.bottom - a.top], over: getComputedStyle(cap).position === "absolute" };
    });
    if (!r.L) { bad.push({ k, why: "no layout" }); return; }
    const hit = [["scene", r.L.scene], ...(r.L.marks || []).map((m) => [m.kind, m.box])].filter(([, box]) => overlap(r.cap, box)).map(([kind]) => kind);
    if (hit.length) bad.push({ k, hit, cap: r.cap, scene: r.L.scene });
  };
  for (const [j, k] of caps.entries()) {
    await at(k);
    await at(Math.max(k, (j + 1 < caps.length ? caps[j + 1] : nSteps) - 1));
  }
  check(`${tag} watch: a caption never covers what it describes (the scene, the landings, the earlier throws)`, !bad.length, { bad: bad.slice(0, 4) });
  await noOverflow(page, `${tag} watch`);
  check(`${tag} watch: no page error`, errs.length === 0, { errs });
  await ctx.close();
}
// Lab work draws what Explore draws (EX2 §5 F6 (b)), part 1 in air: the height, the landing with its label, the Magnus
// force of the rolling ball; at 390 px the view, the step's control and «Measure» together
async function labDraws(W, H, tag) {
  const ctx = await br.newContext({ viewport: { width: W, height: H } });
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  await page.goto(inLang(`${base}/run?demo=${WORLD}&screen=lab`));
  const LB = (body, timeout = 20000) => page.waitForFunction(`(() => { const s = window.__lfLab && window.__lfLab.step(); return ${body}; })()`, null, { timeout });
  await LB("s && s.cur");
  await page.locator('.dm-screen:not([hidden]) .dm-ctl[data-param="air"] .dm-ctl-seg button[data-value="true"]').click();
  await LB("s.cur && s.cur.pt.values.air === true && !s.pending");
  await page.evaluate(() => { const d = document.querySelector(".dm-screen:not([hidden]) .dm-overlays"); if (d) d.open = true; });
  await page.locator('.dm-screen:not([hidden]) input[data-overlay="forces"]').check();
  await page.locator(".dm-screen:not([hidden]) .dm-play").click();
  await LB("s.cur && s.cur.launchedAt !== null");
  await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = "1"; s.dispatchEvent(new Event("input")); });
  await settle(page, 80);
  const L1 = await layout(page);
  check(`${tag} lab part 1 in air: the Magnus force of the rolling ball is drawn under «forces» (the run's, on the drag's scale)`,
    !!(L1 && L1.lift && L1.lift.px >= 6 && L1.drag), { lift: L1 && L1.lift, drag: L1 && L1.drag });
  // the flight to its end: the last frame, once the launch has played out (the lab's own clock may still run)
  await page.waitForFunction(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max;
    s.dispatchEvent(new Event("input")); const c = document.querySelector(".dm-screen:not([hidden]) .dm-stage canvas");
    return !!(c && c.__layout && (c.__layout.marks || []).some((m) => m.kind === "landing")); }, null, { timeout: 15000, polling: 500 }).catch(() => {});
  await settle(page, 80);
  const L2 = await layout(page);
  const kinds = ((L2 && L2.marks) || []).map((m) => m.kind);
  check(`${tag} lab part 1: «h = … m», the landing's mark and its label «L = …, T = …» drawn, as in Explore (nothing hidden)`,
    !!(L2 && L2.hLabel && kinds.includes("landing") && kinds.includes("landing mark")), { kinds, h: L2 && L2.hLabel });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `${SHOTS}/s03_lab_air_${LANG}_${W}x${H}.png` });
  if (W < 1000) {
    await page.locator(".dm-screen:not([hidden]) .dm-ctl").first().scrollIntoViewIfNeeded();
    await settle(page);
    const vis = await page.evaluate(() => {
      const r = (q) => { const e = document.querySelector(`.dm-screen:not([hidden]) ${q}`); if (!e) return null; const b = e.getBoundingClientRect(); return { top: b.top, bottom: b.bottom }; };
      return { H: innerHeight, canvas: r(".dm-stage canvas"), measure: r(".dm-measure"), ctl: r(".dm-ctl") };
    });
    const inView = (b) => b && b.top >= -1 && b.bottom <= vis.H + 1;
    check(`${tag} lab (phone): the view, the step's control and «Measure» on the screen together`, inView(vis.canvas) && inView(vis.measure) && inView(vis.ctl), vis);
  }
  await noOverflow(page, `${tag} lab`);
  check(`${tag} lab: no page error`, errs.length === 0, { errs });
  await ctx.close();
}
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
  await noOverflow(page, `${tag} explore`);
  check(`${tag}: no page error`, errs.length === 0, { errs });
  await ctx.close();
  await watchCaptions(W, H, tag);
  await labDraws(W, H, tag);
}
await br.close();
console.log(failed ? `FAILED: ${failed}` : "all passed");
process.exit(failed ? 1 : 0);
