// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u35's screens in a browser (EX2 design lfphys/sources/explore_EX2_2026-11-18_design.md §1.3, §3, §7 "Browser"), in
// the language of LFVIZ_LANG (en by default), at every viewport size given (1280x800, 390x844 and 390x700 by default).
// What the view drew where comes from its two canvases' `__layout` (u35_optics_bench/web/view.js, written at every
// frame: the labels' boxes and the marks they describe: the structure, the source, the detectors, the analysers, the
// polarisation ellipses, the counters):
//  - Watch, every recording and every caption (its chapter tick): the caption never covers what it describes (on a
//    desktop it lies in the band the view leaves under the pictures, on a phone under the view); one scale for the
//    whole story (the bench's canvas keeps its size at every caption);
//  - Explore («Boundary», «Coatings», «Polarisation»), the default point and the grid's corners, each played to its
//    end: every label inside its canvas; on a phone the readouts under the view, not over it; the fold «Curves …»
//    opens the curves on a phone;
//  - Lab work, every part: at 390 px the view, the step's control, «Measure» and the time bar on the screen together;
//    the labels inside;
//  - the five tabs fit the phone's tab bar (no tab wider than its box);
//  - every screen: no horizontal scroll, no page error; screenshots of every screen and lab part per language and size.
// Run against a PRIVATE server (never the shared one on 8479) with u35's recordings and atlases built by the code
// under test (site/fixtures.py --world u35_optics_bench), as tests/browser/demo_screens.mjs says, with this file:
//   sh -c "cp /t/lfi18n.mjs /v/u35_optics_bench/tests/u35_screens.mjs /pw/ && node /pw/u35_screens.mjs 8721"
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { LANG, inLang, loadI18n } from "./lfi18n.mjs";

const port = process.argv[2] || "8721";
const SIZES = (process.argv[3] || "1280x800,390x844,390x700").split(",").map((s) => s.split("x").map(Number));
const base = `http://127.0.0.1:${port}`;
const SHOTS = process.env.SHOTS || "/pw/shots";
mkdirSync(SHOTS, { recursive: true });
const WORLD = "u35_optics_bench";
let failed = 0;
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: `${LANG} ${name}`, ok: !!ok, ...info })); };
const settle = (page, ms = 150) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
await loadI18n(base);
const viz = await (await fetch(`${base}/api/viz/${WORLD}`)).json();
const explores = viz.screens.filter((s) => s.kind === "explore");
const lab = viz.screens.find((s) => s.kind === "lab");
const watch = viz.screens.find((s) => s.kind === "watch");

// what the screen shown drew: each canvas's layout with its box on the page, the caption's and the readouts' boxes
const snap = (page) => page.evaluate(() => {
  const box = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return b.width && b.height ? { l: b.left, t: b.top, r: b.right, b: b.bottom } : null; };
  const S = document.querySelector(".dm-screen:not([hidden])");
  const cvs = [...S.querySelectorAll("canvas[data-u35]")].map((c) => ({ which: c.dataset.u35, box: box(c), L: c.__layout ? JSON.parse(JSON.stringify(c.__layout)) : null }));
  const cap = S.querySelector(".dm-caption");
  return { cvs, caption: cap && !cap.hidden ? box(cap) : null, captionPos: cap ? getComputedStyle(cap).position : null,
    readouts: box(S.querySelector(".dm-stage > .dm-readouts")), W: innerWidth, H: innerHeight, sw: document.documentElement.scrollWidth };
});
const hit = (a, b) => !!(a && b && a.l < b.r - 0.5 && b.l < a.r - 0.5 && a.t < b.b - 0.5 && b.t < a.b - 0.5);
// a canvas item in page coordinates
const onPage = (cv, x) => ({ l: cv.box.l + x.x, t: cv.box.t + x.y, r: cv.box.l + x.x + x.w, b: cv.box.t + x.y + x.h });
function labelsOutside(s) {
  const out = [];
  for (const cv of s.cvs) {
    if (!cv.L || !cv.box) continue;
    for (const lb of cv.L.labels) if (lb.x < -1 || lb.y < -1 || lb.x + lb.w > cv.L.w + 1 || lb.y + lb.h > cv.L.h + 1) out.push(`${cv.which}: ${lb.text}`);
  }
  return out;
}
function coveredByCaption(s) {
  if (!s.caption) return [];
  const out = [];
  for (const cv of s.cvs) {
    if (!cv.L || !cv.box) continue;
    for (const x of [...cv.L.labels, ...cv.L.marks]) if (hit(s.caption, onPage(cv, x))) out.push(`${cv.which}: ${x.text || x.kind}`);
  }
  return out;
}
async function common(page, tag, errs) {
  const s = await snap(page);
  check(`${tag}: no horizontal scroll`, s.sw <= s.W, { scrollWidth: s.sw, width: s.W });
  check(`${tag}: no label out of its canvas`, !labelsOutside(s).length, { out: labelsOutside(s).slice(0, 5) });
  const wide = await page.evaluate(() => [...document.querySelectorAll(".dm-screen:not([hidden]) .dm-ctl-label, .dm-screen:not([hidden]) .dm-readouts > *, .dm-screen:not([hidden]) button, .dm-tab, .dm-screen:not([hidden]) summary")]
    .filter((e) => e.offsetParent !== null && e.clientWidth > 0 && !e.classList.contains("dm-detent") && e.scrollWidth > e.clientWidth + 1).map((e) => (e.className || e.tagName) + ": " + e.textContent.slice(0, 40)));
  // (a slider's detents are left out: their hit area, an absolutely placed pseudo-element, is wider than their label)
  check(`${tag}: no text wider than its box (controls, readouts, buttons, tabs)`, !wide.length, { wide: wide.slice(0, 5) });
  check(`${tag}: no page error`, errs.length === 0, { errs: errs.slice(0, 3) });
}
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
async function open(ctx, screen, extra = "") {
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 200)); });
  await page.goto(inLang(`${base}/run?demo=${WORLD}&screen=${screen}${extra}`));
  await page.waitForFunction((sc) => { const e = document.querySelector(`.dm-screen[data-screen="${sc}"]`); return e && !e.hidden; }, screen, { timeout: 20000 });
  return { page, errs };
}
const toEnd = async (page) => { await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); if (s) { s.value = s.max; s.dispatchEvent(new Event("input")); } }); await settle(page); };

for (const [W, H] of SIZES) {
  const tag0 = `${W}x${H}`;
  // --- Watch: every recording, every caption --------------------------------------------------------------------------
  for (const rec of [watch.recording, ...(watch.more || [])]) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const { page, errs } = await open(ctx, watch.id);
    await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 30000 });
    if (rec !== watch.recording) {
      await page.locator(".dm-screen:not([hidden]) select.dm-more").selectOption(rec).catch(() => {});
      await page.waitForFunction((r) => window.__lfWatch && window.__lfWatch.state.story && document.querySelector(".dm-screen:not([hidden]) select.dm-more").value === r, rec, { timeout: 30000 }).catch(() => {});
      await settle(page, 800);
    }
    const n = await page.locator(".dm-screen:not([hidden]) .dm-tick").count();
    const covered = [], sizes = new Set();
    for (let k = 0; k < n; k++) {
      await page.locator(".dm-screen:not([hidden]) .dm-tick").nth(k).click();
      await settle(page, 400);
      const s = await snap(page);
      covered.push(...coveredByCaption(s).map((x) => `caption ${k}: ${x}`));
      const bench = s.cvs.find((c) => c.which === "bench");
      sizes.add(bench && bench.box ? `${Math.round(bench.box.r - bench.box.l)}x${Math.round(bench.box.b - bench.box.t)}` : "none");
      if (k === Math.min(3, n - 1)) await page.screenshot({ path: `${SHOTS}/u35_watch_${rec}_${LANG}_${tag0}.png` });
    }
    check(`${tag0} watch ${rec}: ${n} captions, none covers what the view drew (labels, detectors, structure, counters)`, n >= 2 && !covered.length, { covered: covered.slice(0, 6) });
    check(`${tag0} watch ${rec}: one scale for the whole story (the bench's size the same at every caption)`, sizes.size === 1, { sizes: [...sizes] });
    await common(page, `${tag0} watch ${rec}`, errs);
    await ctx.close();
  }
  // --- Explore: the default point and the grid's corners --------------------------------------------------------------
  for (const ex of explores) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const { page, errs } = await open(ctx, ex.id);
    const X = `(window.__lfExplore || {})[${JSON.stringify(ex.id)}]`;
    await page.waitForFunction(`${X} && ${X}.point()`, null, { timeout: 30000 });
    await toEnd(page);
    const s0 = await snap(page);
    await page.screenshot({ path: `${SHOTS}/u35_${ex.id}_${LANG}_${tag0}.png`, fullPage: W < 1000 });
    if (W < 1000) {
      const b = s0.cvs.find((c) => c.which === "bench");
      check(`${tag0} ${ex.id} (phone): the readouts lie under the view, not over it`, !s0.readouts || !hit(s0.readouts, b.box), { readouts: s0.readouts, bench: b.box });
      await page.locator(".dm-screen:not([hidden]) details.u35-fold > summary").click();
      await settle(page, 300);
      const s1 = await snap(page);
      const cur = s1.cvs.find((c) => c.which === "curves");
      check(`${tag0} ${ex.id} (phone): the fold «Curves …» opens the curves under the view`, !!cur && !!cur.box && cur.box.b - cur.box.t > 200 && cur.L && cur.L.labels.length > 3, { cur: cur && cur.box });
      await page.screenshot({ path: `${SHOTS}/u35_${ex.id}_curves_${LANG}_${tag0}.png`, fullPage: true });
    } else {
      const cur = s0.cvs.find((c) => c.which === "curves");
      check(`${tag0} ${ex.id}: the curves are drawn beside the bench`, !!cur && cur.L && cur.L.labels.length > 3, { labels: cur && cur.L && cur.L.labels.length });
    }
    // the grid's corners: every control at its first and its last value
    const corners = [];
    for (const which of [0, 1]) {
      for (const c of ex.controls) {
        const v = c.values[which ? c.values.length - 1 : 0];
        if ((await page.evaluate(`${X}.values()`))[c.param] === v) continue;
        // pressed by script: on a phone the sticky time bar may lie over the control (the layout is checked elsewhere)
        const target = c.values.every((x) => typeof x === "number")
          ? page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${c.param}"] .dm-detent`).nth(c.values.indexOf(v))
          : page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${c.param}"] .dm-ctl-seg button[data-value='${JSON.stringify(v)}']`);
        await target.evaluate((e) => e.click());
        await page.waitForFunction(`${X}.point() && ${X}.point().values[${JSON.stringify(c.param)}] === ${JSON.stringify(v)}`, null, { timeout: 20000 });
      }
      await toEnd(page);
      const s = await snap(page);
      corners.push(...labelsOutside(s));
    }
    check(`${tag0} ${ex.id}: at the grid's corners every label inside its canvas`, !corners.length, { out: corners.slice(0, 5) });
    await common(page, `${tag0} ${ex.id}`, errs);
    await ctx.close();
  }
  // --- Lab work: every part -------------------------------------------------------------------------------------------
  {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const { page, errs } = await open(ctx, lab.id);
    const LB = (body, timeout = 20000) => page.waitForFunction(`(() => { const s = window.__lfLab && window.__lfLab.step(); return ${body}; })()`, null, { timeout });
    await LB("s && s.cur", 30000);
    for (const [k, st] of lab.steps.entries()) {
      if (k > 0) { await page.locator(".dm-steps button").nth(k).click(); await LB(`s && s.step.id === ${JSON.stringify(st.id)} && s.cur`); }
      await toEnd(page);
      await page.screenshot({ path: `${SHOTS}/u35_lab_${st.id}_${LANG}_${tag0}.png`, fullPage: W < 1000 });
      const s = await snap(page);
      check(`${tag0} lab part ${k + 1} (${st.id}): every label inside its canvas`, !labelsOutside(s).length, { out: labelsOutside(s).slice(0, 5) });
      if (W < 1000) {
        const ctl = (st.controls && st.controls[0]) || (explores.find((e) => e.id === st.atlas) || {}).controls[0];
        await page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${ctl.param || ctl.id}"]`).first().scrollIntoViewIfNeeded();
        await settle(page, 100);
        const vis = await page.evaluate((prm) => {
          const r = (q) => { const e = document.querySelector(`.dm-screen:not([hidden]) ${q}`); if (!e) return null; const b = e.getBoundingClientRect(); return { top: Math.round(b.top), bottom: Math.round(b.bottom) }; };
          return { H: innerHeight, canvas: r(".dm-stage canvas"), ctl: r(`.dm-ctl[data-param="${prm}"]`), measure: r(".dm-measure"), bar: r(".dm-bar") };
        }, ctl.param || ctl.id);
        const inV = (b) => b && b.top >= -1 && b.bottom <= vis.H + 1;
        check(`${tag0} lab part ${k + 1} (phone): the view, the step's control, «Measure» and the time bar on the screen together`,
          inV(vis.canvas) && inV(vis.ctl) && inV(vis.measure) && inV(vis.bar) && vis.ctl.bottom <= Math.min(vis.measure.top, vis.bar.top) + 1, vis);
      }
    }
    await common(page, `${tag0} lab`, errs);
    await ctx.close();
  }
  // --- the five tabs on a phone ---------------------------------------------------------------------------------------
  if (W < 1000) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const { page, errs } = await open(ctx, explores[0].id);
    // (the narrower tabs are the player's demo.css, from the first paint; measured once the view is on the page too)
    await page.waitForSelector(".u35-c", { timeout: 20000 });
    await settle(page);
    const tabs = await page.evaluate(() => [...document.querySelectorAll(".dm-tab")].map((e) => { const b = e.getBoundingClientRect(); return { text: e.textContent.trim(), l: b.left, r: b.right, sw: e.scrollWidth, cw: e.clientWidth }; }));
    check(`${tag0}: the ${tabs.length} tabs fit the phone's tab bar`, tabs.length === viz.screens.length && tabs.every((x) => x.l >= -1 && x.r <= W + 1 && x.sw <= x.cw + 1), { tabs });
    await common(page, `${tag0} tabs`, errs);
    await ctx.close();
  }
}
await br.close();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
