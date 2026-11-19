// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u37's screens in a browser (EX2 design lfphys/sources/explore_EX2_2026-11-18_design.md §1.3, §7 "Browser"), in the
// language of LFVIZ_LANG (en by default), at every viewport size given (1280x800 and 390x844 by default), from the
// view's own layout (canvas.__layout: the box of every text it drew and of its parts):
//  - Watch: the caption never covers a picture (a fixed band under the pictures on a wide screen, its own place on a
//    phone), at the start and at each caption's chapter tick;
//  - every screen and lab part: no text of the view outside its canvas, no horizontal scroll, no page error; in English
//    no Cyrillic in the visible text;
//  - Explore and Lab work on a phone: the statistics start under the readouts laid over the view (no text of the
//    view under that box), the spacetime diagram folded under its toggle and drawn when opened;
//  - Lab work on a phone: for each part the view, the part's first control and «Measure» on the screen together;
//  - screenshots of every screen and lab part per language and size (taken after the checks: a full-page screenshot
//    leaves Chromium's document a few pixels wider, whatever the view).
// Run against a PRIVATE server with u37's recordings and atlases built by the code under test (site/fixtures.py --world
// u37_bell_test), never the shared one on 8479, as u32_double_slit/tests/u32_screens.mjs says:
//   node u37_screens.mjs <port> [sizes]
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { LANG, inLang } from "./lfi18n.mjs";

const port = process.argv[2] || "8722";
const SIZES = (process.argv[3] || "1280x800,390x844").split(",").map((s) => s.split("x").map(Number));
const base = `http://127.0.0.1:${port}`;
const SHOTS = process.env.SHOTS || "/pw/shots";
mkdirSync(SHOTS, { recursive: true });
const WORLD = "u37_bell_test";
const CYR = /[Ѐ-ӿ]/;  // i18n-ok: recognises Cyrillic
let failed = 0;
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: `${LANG} ${name}`, ok: !!ok, ...info })); };
const settle = (page, ms = 300) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);

const viz = await (await fetch(`${base}/api/viz/${WORLD}`)).json();
const lab = viz.screens.find((s) => s.kind === "lab");
check("u37 has Watch, Explore and Lab work with four parts", viz.screens.map((s) => s.kind).join() === "watch,explore,lab" && lab.steps.length === 4);

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });

async function open(ctx, screen) {
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 200)); });
  await page.goto(inLang(`${base}/run?demo=${WORLD}&screen=${screen}`));
  await page.waitForFunction((s) => document.querySelector(`.dm-screen[data-screen="${s}"]`) && !document.querySelector(`.dm-screen[data-screen="${s}"]`).hidden, screen, { timeout: 30000 });
  await page.waitForFunction(() => [...document.querySelectorAll(".dm-screen:not([hidden]) .dm-stage canvas")].some((c) => c.__layout && c.__layout.texts.length), null, { timeout: 30000 });
  return { page, errs };
}
// every text of every canvas of the view inside its canvas
const textsOut = (page) => page.evaluate(() => [...document.querySelectorAll(".dm-screen:not([hidden]) .dm-stage canvas")]
  .filter((c) => c.__layout && c.clientWidth > 0)
  .flatMap((c) => c.__layout.texts.filter((b) => b.x0 < -1 || b.x1 > c.__layout.w + 1 || b.y0 < -1 || b.y1 > c.__layout.h + 1)
    .map((b) => ({ s: b.s.slice(0, 50), x0: Math.round(b.x0), x1: Math.round(b.x1), y0: Math.round(b.y0), y1: Math.round(b.y1), w: c.__layout.w, h: c.__layout.h }))));
async function common(page, tag, W, errs) {
  const sw = await page.evaluate(() => document.scrollingElement.scrollWidth);
  check(`${tag}: no horizontal scroll`, sw <= W, { scrollWidth: sw, width: W });
  const out = await textsOut(page);
  check(`${tag}: no text of the view outside its canvas`, out.length === 0, { out: out.slice(0, 4) });
  if (LANG === "en") {
    const txt = await page.evaluate(() => document.getElementById("demo").innerText);
    check(`${tag}: no Cyrillic in the visible text`, !CYR.test(txt), { sample: (txt.match(/.{0,30}[Ѐ-ӿ].{0,30}/) || [""])[0] });  // i18n-ok
  }
  check(`${tag}: no page error`, errs.length === 0, { errs });
}
// the caption against every canvas shown
const captionClear = (page) => page.evaluate(() => {
  const cap = document.querySelector(".dm-screen:not([hidden]) .dm-caption");
  if (!cap || cap.hidden || !cap.textContent.trim()) return { none: true };
  const c = cap.getBoundingClientRect();
  const bad = [...document.querySelectorAll(".dm-screen:not([hidden]) .dm-stage canvas")].map((e) => e.getBoundingClientRect())
    .filter((r) => r.width > 0 && r.height > 0)
    .filter((r) => Math.min(r.right, c.right) - Math.max(r.left, c.left) > 1 && Math.min(r.bottom, c.bottom) - Math.max(r.top, c.top) > 1)
    .map((r) => ({ top: Math.round(r.top), bottom: Math.round(r.bottom) }));
  return { cap: { top: Math.round(c.top), bottom: Math.round(c.bottom) }, bad };
});
// on a phone the readouts box is laid over the view: no text of the statistics under it
const underReadouts = (page) => page.evaluate(() => {
  const ro = document.querySelector(".dm-screen:not([hidden]) .dm-stage > .dm-readouts");
  if (!ro || !ro.offsetHeight || getComputedStyle(ro).position !== "absolute") return { none: true };
  const rb = ro.getBoundingClientRect();
  const bad = [];
  for (const c of document.querySelectorAll(".dm-screen:not([hidden]) .dm-stage canvas")) {
    if (!c.__layout) continue;
    const cb = c.getBoundingClientRect();
    for (const b of c.__layout.texts) {
      const x0 = cb.left + b.x0, x1 = cb.left + b.x1, y0 = cb.top + b.y0, y1 = cb.top + b.y1;
      if (Math.min(x1, rb.right) - Math.max(x0, rb.left) > 1 && Math.min(y1, rb.bottom) - Math.max(y0, rb.top) > 1) bad.push(b.s.slice(0, 40));
    }
  }
  return { bad };
});

for (const [W, H] of SIZES) {
  const tag0 = `${W}x${H}`;
  const ctx = await br.newContext({ viewport: { width: W, height: H } });
  // --- Watch ---
  {
    const { page, errs } = await open(ctx, "watch");
    await settle(page, 600);
    const n = await page.locator(".dm-screen:not([hidden]) .dm-tick").count();
    const res = [];
    for (let k = 0; k < n; k++) {
      await page.locator(".dm-screen:not([hidden]) .dm-tick").nth(k).click();
      await settle(page, 500);
      res.push({ k, ...(await captionClear(page)) });
    }
    check(`${tag0} watch: a caption at every chapter tick, never over a picture`, n >= 6 && res.every((r) => !r.none && r.bad.length === 0), { res: res.filter((r) => r.none || r.bad.length).slice(0, 3) });
    await common(page, `${tag0} watch`, W, errs);
    // (a full-page screenshot last: Chromium lays the page out at its full height for it, which leaves the document a
    // few pixels wider afterwards whatever the view)
    await page.locator(".dm-screen:not([hidden]) .dm-tick").nth(2).click();
    await settle(page, 500);
    await page.screenshot({ path: `${SHOTS}/u37_watch_${LANG}_${tag0}.png`, fullPage: W < 1000 });
    await page.close();
  }
  // --- Explore ---
  {
    const { page, errs } = await open(ctx, "explore");
    await page.locator(".dm-screen:not([hidden]) .dm-play").first().click().catch(() => {});
    await page.waitForTimeout(5000);
    await settle(page);
    if (W < 1000) {
      const u = await underReadouts(page);
      check(`${tag0} explore (phone): no text of the view under the readouts laid over it`, u.none || u.bad.length === 0, u);
      const tg = page.locator(".dm-screen:not([hidden]) .u37-st-tg");
      await tg.scrollIntoViewIfNeeded();
      await tg.click();
      await settle(page, 500);
      const st = await page.evaluate(() => { const c = document.querySelector(".dm-screen:not([hidden]) .u37-st canvas"); return { h: c.clientHeight, n: c.__layout ? c.__layout.texts.length : 0 }; });
      check(`${tag0} explore (phone): the spacetime diagram opens under its toggle and is drawn`, st.h >= 200 && st.n > 3, st);
      await page.evaluate(() => window.scrollTo(0, 0));
      await settle(page);
    }
    await common(page, `${tag0} explore`, W, errs);
    await page.screenshot({ path: `${SHOTS}/u37_explore_${LANG}_${tag0}.png`, fullPage: W < 1000 });
    await page.close();
  }
  // --- Lab work: every part ---
  {
    const { page, errs } = await open(ctx, "lab");
    const shots = [];
    for (let k = 0; k < lab.steps.length; k++) {
      const st = lab.steps[k];
      if (k > 0) { await page.locator(".dm-screen:not([hidden]) .dm-steps button").nth(k).click(); }
      await page.waitForTimeout(1500);
      await page.locator(".dm-screen:not([hidden]) .dm-play").first().click().catch(() => {});
      await page.waitForTimeout(3000);
      await settle(page);
      if (W < 1000) {
        await page.locator(".dm-screen:not([hidden]) .dm-ctl").first().scrollIntoViewIfNeeded();
        await settle(page);
        const vis = await page.evaluate(() => {
          const r = (q) => { const e = document.querySelector(`.dm-screen:not([hidden]) ${q}`); if (!e) return null; const b = e.getBoundingClientRect(); return { top: Math.round(b.top), bottom: Math.round(b.bottom) }; };
          return { H: innerHeight, stat: r(".u37-stat canvas"), set: r(".u37-set canvas"), ctl: r(".dm-ctl"), measure: r(".dm-measure") };
        });
        const inV = (b) => b && b.top >= -1 && b.bottom <= vis.H + 1;
        check(`${tag0} lab ${st.id} (phone): the view, the part's control and «Measure» on the screen together`, inV(vis.stat) && inV(vis.set) && inV(vis.ctl) && inV(vis.measure), vis);
        const u = await underReadouts(page);
        check(`${tag0} lab ${st.id} (phone): no text of the view under the readouts laid over it`, u.none || u.bad.length === 0, u);
        await page.evaluate(() => window.scrollTo(0, 0));
        await settle(page);
      }
      const out = await textsOut(page);
      check(`${tag0} lab ${st.id}: no text of the view outside its canvas`, out.length === 0, { out: out.slice(0, 4) });
      const sw = await page.evaluate(() => document.scrollingElement.scrollWidth);
      check(`${tag0} lab ${st.id}: no horizontal scroll`, sw <= W, { scrollWidth: sw, width: W });
      await page.screenshot({ path: `${SHOTS}/u37_lab${k + 1}_${st.id}_${LANG}_${tag0}.png`, fullPage: false });
    }
    await common(page, `${tag0} lab`, W, errs);
    await page.close();
  }
  await ctx.close();
}
await br.close();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
