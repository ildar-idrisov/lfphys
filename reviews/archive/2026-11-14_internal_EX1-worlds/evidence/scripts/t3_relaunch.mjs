// S03 Explore: (a) the same point launched twice (strobe on / off) — the trace shares the point's world;
// (b) at 390 px: scroll to the bottom, is the air toggle visible above the sticky bar?
import { chromium } from "playwright";
import { launch, startStatic, sleep, SRV, SITE, watchErrors } from "./lib.mjs";
const where = process.argv[2] || "site";
const base = where === "site" ? SITE : SRV;
if (where === "site") await startStatic();
const br = await launch();
const open = async (w, lang = "en") => {
  const ctx = await br.newContext({ viewport: { width: w, height: w > 500 ? 860 : 844 } });
  const page = await ctx.newPage(); const errs = []; watchErrors(page, errs);
  await page.goto(where === "site" ? `${base}/run.html?demo=s03_projectile&screen=explore&lang=${lang}` : `${base}/run?demo=s03_projectile&screen=explore&lang=${lang}`);
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 60000 });
  await sleep(400); return { ctx, page, errs };
};
const landed = async (page) => page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 30000 });
for (const strobe of [false, true]) {
  const { ctx, page, errs } = await open(1280);
  if (strobe) await page.$eval(".dm-overlays input[data-overlay=strobe]", (cb) => cb.click());
  await page.click(".dm-screen[data-screen=explore] .dm-play"); await landed(page);
  await page.click(".dm-screen[data-screen=explore] .dm-play"); await sleep(900); await page.keyboard.press("Space"); await sleep(300);
  const st = await page.evaluate(() => { const E = window.__lfExplore.explore.state; return { traces: E.traces.length, same: E.traces[0] && E.traces[0].pt.W === E.cur.pt.W }; });
  await page.locator(".dm-screen[data-screen=explore] .dm-stage").screenshot({ path: `/shots/s03_relaunch_strobe${strobe}.png` });
  console.log(JSON.stringify({ strobe, ...st, errs }));
  await ctx.close();
}
for (const lang of ["en", "ru"]) {
  const { ctx, page } = await open(390, lang);
  await page.evaluate(() => window.scrollTo(0, document.scrollingElement.scrollHeight)); await sleep(400);
  const o = await page.evaluate(() => {
    const r = (s) => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.top), Math.round(b.bottom)]; };
    return { air: r(".dm-screen[data-screen=explore] .dm-ctl[data-param=air]"), show: r(".dm-overlays"), bar: r(".dm-screen[data-screen=explore] .dm-bar"), clear: r(".dm-clear"), vh: innerHeight, canvas: r(".dm-screen[data-screen=explore] .dm-stage canvas") };
  });
  console.log(JSON.stringify({ lang, ...o }));
  await page.screenshot({ path: `/shots/s03e_390_${lang}_bottom.png` });
  await page.evaluate(() => window.scrollTo(0, 0)); await sleep(300);
  await page.screenshot({ path: `/shots/s03e_390_${lang}_top.png` });
  await ctx.close();
}
await br.close();
process.exit(0);
