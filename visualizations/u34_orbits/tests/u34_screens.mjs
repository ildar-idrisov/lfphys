// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u34's screens in a browser (EX2 design lfphys/sources/explore_EX2_2026-11-18_design.md §1.3, §2, §7 "Browser"), in the
// language of LFVIZ_LANG (en by default), at every viewport size given (1280x800, 390x844 and 390x700 by default). What
// the view drew where comes from its canvases' `__layout` (u34_orbits/web/view.js, written at every frame):
//  - Watch, every recording and every caption (its chapter tick): the caption never covers the pictures it describes
//    (on a desktop it lies in the band the view leaves under them, on a phone under the view); one scale for the whole
//    story (the plane's px per M the same at every caption of a recording); the plots shown with the clock's caption;
//  - Explore, the default point and the grid's corners, the zoom-whirl and a circle, each launched to its end: every
//    label inside its canvas and clear of the others; the body inside; on a phone the readouts laid over the view's
//    corner clear of the fitted orbit's box; an earlier point's trace labelled inside the canvas; the fold «Plots …»
//    opens the plots on a phone;
//  - Lab work, every part: at 390 px the view, the step's control, «Measure» and the time bar on the screen together;
//    the labels inside;
//  - every screen: no horizontal scroll, no page error; screenshots of every screen per language and size.
// Run against a PRIVATE server (never the shared one on 8479) with u34's recordings and atlases built by the code
// under test (site/fixtures.py --world u34_orbits), as tests/browser/demo_screens.mjs says, with this file:
//   sh -c "cp /t/lfi18n.mjs /v/u34_orbits/tests/u34_screens.mjs /pw/ && node /pw/u34_screens.mjs 8720"
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { LANG, inLang, loadI18n } from "./lfi18n.mjs";

const port = process.argv[2] || "8720";
const SIZES = (process.argv[3] || "1280x800,390x844,390x700").split(",").map((s) => s.split("x").map(Number));
const base = `http://127.0.0.1:${port}`;
const SHOTS = process.env.SHOTS || "/pw/shots";
mkdirSync(SHOTS, { recursive: true });
const WORLD = "u34_orbits";
let failed = 0;
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: `${LANG} ${name}`, ok: !!ok, ...info })); };
const settle = (page, ms = 120) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
const { t: tr } = await loadI18n(base);
const viz = await (await fetch(`${base}/api/viz/${WORLD}`)).json();
const scr = (k) => viz.screens.find((s) => s.kind === k);

// what the screen shown drew: both canvases' layouts and their boxes on the page, the caption's and the readouts' boxes
const snap = (page) => page.evaluate(() => {
  const box = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return b.width && b.height ? { l: b.left, t: b.top, r: b.right, b: b.bottom } : null; };
  const S = document.querySelector(".dm-screen:not([hidden])");
  const cv = [...S.querySelectorAll(".dm-stage canvas")];
  const cap = S.querySelector(".dm-caption");
  const rd = S.querySelector(".dm-stage > .dm-readouts");
  return { orb: cv[0] && cv[0].__layout ? JSON.parse(JSON.stringify(cv[0].__layout)) : null, orbBox: box(cv[0]),
    plot: cv[1] && cv[1].__layout ? JSON.parse(JSON.stringify(cv[1].__layout)) : null, plotBox: box(cv[1]),
    cap: cap && !cap.hidden && cap.textContent ? box(cap) : null, capText: cap ? cap.textContent : "",
    readouts: rd && getComputedStyle(rd).position === "absolute" ? box(rd) : null,
    bar: box([...S.querySelectorAll(".dm-bar")].find((e) => getComputedStyle(e).position === "sticky")),
    sw: document.scrollingElement.scrollWidth };
});
const meets = (a, b) => !!a && !!b && a.l < b.r - 0.5 && b.l < a.r - 0.5 && a.t < b.b - 0.5 && b.t < a.b - 0.5;
// every label of a layout inside its canvas and clear of the others (the view places them so)
function labelsOk(L) {
  if (!L || !L.labels) return { ok: false, why: "no layout" };
  const out = L.labels.filter((q) => q.x0 < -0.5 || q.y0 < -0.5 || q.x1 > L.w + 0.5 || q.y1 > L.h + 0.5);
  const lap = [];
  for (let i = 0; i < L.labels.length; i++) for (let j = i + 1; j < L.labels.length; j++) {
    const a = L.labels[i], b = L.labels[j];
    if (a.x0 < b.x1 - 0.5 && b.x0 < a.x1 - 0.5 && a.y0 < b.y1 - 0.5 && b.y0 < a.y1 - 0.5) lap.push([a.text, b.text]);
  }
  return { ok: !out.length && !lap.length, out: out.slice(0, 3), lap: lap.slice(0, 3), n: L.labels.length };
}

// a phone (D12): the control scrolled to just under the sticky view; it must then lie whole between the view and the
// sticky part at the bottom (Explore's time bar, Lab work's dock with «Measure»), none of them covering it
async function together(page, ctlQ, bottomQ) {
  await page.locator(`.dm-screen:not([hidden]) ${ctlQ}`).first().scrollIntoViewIfNeeded();
  await settle(page);
  await page.evaluate(([c]) => {
    const S = document.querySelector(".dm-screen:not([hidden])");
    const ctl = S.querySelector(c).getBoundingClientRect(), st = S.querySelector(".dm-stage").getBoundingClientRect();
    window.scrollBy(0, ctl.top - st.bottom - 4);
  }, [ctlQ]);
  await settle(page);
  return page.evaluate(([c, b]) => {
    const r = (q) => { const e = document.querySelector(`.dm-screen:not([hidden]) ${q}`); if (!e) return null; const x = e.getBoundingClientRect(); return { top: x.top, bottom: x.bottom }; };
    const v = { H: innerHeight, canvas: r(".dm-stage canvas"), stage: r(".dm-stage"), ctl: r(c), bottom: r(b), measure: r(".dm-measure"), bar: r(".dm-bar") };
    const inView = (x) => x && x.top >= -1 && x.bottom <= v.H + 1;
    v.ok = inView(v.canvas) && inView(v.ctl) && inView(v.bar) && v.ctl.top >= v.stage.bottom - 1 && v.ctl.bottom <= v.bottom.top + 1;
    return v;
  }, [ctlQ, bottomQ]);
}

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
async function open(ctx, screen) {
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 200)); });
  await page.goto(inLang(`${base}/run?demo=${WORLD}&screen=${screen}`));
  await page.waitForFunction((s) => document.querySelector(`.dm-screen[data-screen="${s}"]`) && !document.querySelector(`.dm-screen[data-screen="${s}"]`).hidden, screen, { timeout: 20000 });
  return { page, errs };
}

for (const [W, H] of SIZES) {
  const tag = `${W}x${H}`, phone = W < 1000;
  // --- Watch: every recording, every caption ------------------------------------------------------------------------
  {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const { page, errs } = await open(ctx, scr("watch").id);
    await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 30000 });
    const recs = [scr("watch").recording, ...(scr("watch").more || [])];
    for (const rid of recs) {
      if (rid !== recs[0]) {
        await page.selectOption(".dm-screen:not([hidden]) .dm-more", rid);
        await page.waitForFunction((r) => window.__lfWatch.state.rec && window.__lfWatch.state.rec.id === r && window.__lfWatch.state.story, rid, { timeout: 30000 });
      }
      const nCaps = await page.locator(".dm-screen:not([hidden]) .dm-tick").count();
      const bad = [], scales = new Set(), lab = [];
      for (let k = 0; k < nCaps; k++) {
        await page.locator(".dm-screen:not([hidden]) .dm-tick").nth(k).click();
        await settle(page);
        const s = await snap(page);
        if (!s.cap || meets(s.cap, s.orbBox) || meets(s.cap, s.plotBox)) bad.push({ k, cap: s.cap, orb: s.orbBox, plot: s.plotBox, text: s.capText.slice(0, 60) });
        scales.add(s.orb ? s.orb.scale.toPrecision(9) : "none");
        const lo = labelsOk(s.orb), lp = labelsOk(s.plot);
        if (!lo.ok || !lp.ok) lab.push({ k, lo, lp });
        if (rid === recs[0] && (k === 3 || k === 5)) {  // the clocks' captions: their plot is on the screen with them
          // on a phone, at the page's top (the tick's click scrolls the page): the orbit plane, the plot and the caption
          // together above the sticky time bar (review R2-P F17: the plot lay at 711–931 px of 844, under the bar)
          let t = s;
          if (phone) { await page.evaluate(() => window.scrollTo(0, 0)); await settle(page); t = await snap(page); }
          const above = !phone || (!!t.bar && t.plotBox && t.cap && t.orbBox && t.orbBox.t >= -0.5 && t.plotBox.b <= t.bar.t + 0.5 && t.cap.b <= t.bar.t + 0.5);
          check(`${tag} watch ${rid}: the clock's caption («${t.capText.slice(0, 30)}…») has the plot 1 − dτ/dt in view`,
            !!t.plotBox && t.plotBox.b - t.plotBox.t > 120 && t.plotBox.t >= 0 && above, { plot: t.plotBox, orb: t.orbBox, cap: t.cap, bar: t.bar });
        }
        if (k === 0 || k === nCaps - 1) await page.screenshot({ path: `${SHOTS}/u34_watch_${rid}_c${k}_${LANG}_${tag}.png` });
      }
      check(`${tag} watch ${rid}: every caption (${nCaps}) is shown clear of the orbit plane and the plots`, nCaps > 0 && !bad.length, { bad: bad.slice(0, 3) });
      check(`${tag} watch ${rid}: one scale for the whole recording`, scales.size === 1 && !scales.has("none"), { scales: [...scales] });
      check(`${tag} watch ${rid}: every label inside its canvas and clear of the others`, !lab.length, { lab: lab.slice(0, 2) });
    }
    const s = await snap(page);
    check(`${tag} watch: no horizontal scroll`, s.sw <= W, { sw: s.sw });
    check(`${tag} watch: no page error`, !errs.length, { errs });
    await ctx.close();
  }
  // --- Explore: the default point, the corners, the zoom-whirl, a circle ------------------------------------------------
  {
    const ex = scr("explore");
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const { page, errs } = await open(ctx, ex.id);
    const X = `(window.__lfExplore || {})[${JSON.stringify(ex.id)}]`;
    await page.waitForFunction(`${X} && ${X}.point()`, null, { timeout: 30000 });
    const mf = await page.evaluate(`${X}.atlas.manifest`);
    const grid = Object.fromEntries(mf.controls.map((c) => [c.param, c.values]));
    const pick = async (vals) => {
      await page.evaluate(([v, g]) => {
        const E = (window.__lfExplore || {}).explore;
        for (const [p, x] of Object.entries(v)) {
          if (E.values()[p] === x) continue;
          document.querySelectorAll(`.dm-screen:not([hidden]) .dm-ctl[data-param="${p}"] .dm-detent`)[g[p].indexOf(x)].click();
        }
      }, [vals, grid]);
      await page.waitForFunction(([v]) => { const p = (window.__lfExplore || {}).explore.point(); return p && Object.entries(v).every(([k, x]) => p.values[k] === x); }, [vals], { timeout: 20000 });
      await settle(page);
    };
    // ▶ Launch, then the time bar to the point's end (the flight itself takes a minute of played time at the far points)
    const launchToEnd = async () => {
      await page.locator(".dm-screen:not([hidden]) .dm-play").click();
      await page.waitForFunction(`${X}.state.cur && ${X}.state.cur.launchedAt !== null`, null, { timeout: 30000 });
      await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max; s.dispatchEvent(new Event("input")); });
      await page.waitForFunction(`!${X}.state.playing`, null, { timeout: 30000 });
      await settle(page);
    };
    const pts = [{ r0: 20, speed: 1.1 }, { r0: 7, speed: 0.9 }, { r0: 7, speed: 1.05 }, { r0: 30, speed: 1.1 }, { r0: 30, speed: 0.9 },
      { r0: 10, speed: 0.95 }, { r0: 15, speed: 1.0 }];
    const bad = [];
    for (const [j, v] of pts.entries()) {
      await pick(v);
      await launchToEnd();
      const s = await snap(page);
      const lo = labelsOk(s.orb), lp = labelsOk(s.plot);
      const L = s.orb;
      const body = L && L.body && L.body.x >= 0 && L.body.x <= L.w && L.body.y >= 0 && L.body.y <= L.h;
      // the fitted orbit's box (centre ± R) on the page, and the readouts laid over the stage on a phone
      const ob = L && s.orbBox ? { l: s.orbBox.l + L.centre.x - L.R * L.scale, r: s.orbBox.l + L.centre.x + L.R * L.scale,
        t: s.orbBox.t + L.centre.y - L.R * L.scale, b: s.orbBox.t + L.centre.y + L.R * L.scale } : null;
      const covered = s.readouts && ob && meets(s.readouts, ob);
      if (!lo.ok || !lp.ok || !body || covered) bad.push({ v, lo, lp, body: L && L.body, covered, ob, readouts: s.readouts });
      if (j === 0 || j === 5) await page.screenshot({ path: `${SHOTS}/u34_explore_r${v.r0}_v${v.speed}_${LANG}_${tag}.png` });
    }
    check(`${tag} explore: at ${pts.length} points launched to their end the labels are inside and apart, the body inside${phone ? ", the readouts clear of the orbit" : ""}`,
      !bad.length, { bad: bad.slice(0, 2) });
    // an earlier point's trace, labelled with what differs, inside the canvas
    const s2 = await snap(page);
    const traceLab = (s2.orb && s2.orb.labels || []).filter((q) => q.kind === "trace");
    check(`${tag} explore: earlier points are traces labelled inside the canvas («${traceLab.length ? traceLab[traceLab.length - 1].text : ""}»)`,
      traceLab.length >= 1 && traceLab.every((q) => q.x0 >= 0 && q.x1 <= s2.orb.w && q.y0 >= 0 && q.y1 <= s2.orb.h), { traceLab });
    if (phone) {  // the plots fold under the plane; the fold opens them
      const before = await snap(page);
      await page.locator(".dm-screen:not([hidden]) .u34-foldbtn").click();
      await settle(page);
      const after = await snap(page);
      check(`${tag} explore: the plots fold under the plane and «${tr("Plots r(t) and 1 − dτ/dt, and what the lines are").slice(0, 20)}…» opens them`,
        !before.plotBox && after.plotBox && after.plotBox.b - after.plotBox.t > 150, { before: before.plotBox, after: after.plotBox });
      await page.locator(".dm-screen:not([hidden]) .u34-foldbtn").click();
      const vis = await together(page, ".dm-ctl", ".dm-bar");
      check(`${tag} explore: the view, a control and the time bar on the screen together, the control between them`, vis.ok, vis);
    }
    check(`${tag} explore: no horizontal scroll`, s2.sw <= W, { sw: s2.sw });
    check(`${tag} explore: no page error`, !errs.length, { errs });
    await ctx.close();
  }
  // --- Lab work: every part ----------------------------------------------------------------------------------------------
  {
    const lab = scr("lab");
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const { page, errs } = await open(ctx, lab.id);
    const LB = (body, timeout = 30000) => page.waitForFunction(`(() => { const s = window.__lfLab && window.__lfLab.step(); return ${body}; })()`, null, { timeout });
    await LB("s && s.cur");
    for (const [k, st] of lab.steps.entries()) {
      if (k > 0) {  // (on a short phone the steps' buttons may lie under the sticky dock until scrolled: pressed by script)
        await page.evaluate((j) => document.querySelectorAll(".dm-screen:not([hidden]) .dm-steps button")[j].click(), k);
        await LB(`s && s.step.id === ${JSON.stringify(st.id)} && s.cur`);
      }
      await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max; s.dispatchEvent(new Event("input")); });
      await settle(page, 300);
      const s = await snap(page);
      const lo = labelsOk(s.orb);
      check(`${tag} lab part ${k + 1}: the labels inside the canvas and apart, as in Explore`, lo.ok, lo);
      if (phone) {
        const vis = await together(page, ".dm-card .dm-ctl", ".dm-dock");
        check(`${tag} lab part ${k + 1}: the view, the step's control, «${tr("Measure")}» and the time bar on the screen together, the control between the view and the dock`,
          vis.ok && vis.measure && vis.measure.top >= vis.ctl.bottom - 1 && vis.measure.bottom <= vis.H + 1, vis);
      }
      await page.evaluate(() => { window.scrollTo(0, 0); });
      await settle(page);
      await page.screenshot({ path: `${SHOTS}/u34_lab${k + 1}_${LANG}_${tag}.png` });
      check(`${tag} lab part ${k + 1}: no horizontal scroll`, s.sw <= W, { sw: s.sw });
    }
    check(`${tag} lab: no page error`, !errs.length, { errs });
    await ctx.close();
  }
}
await br.close();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
