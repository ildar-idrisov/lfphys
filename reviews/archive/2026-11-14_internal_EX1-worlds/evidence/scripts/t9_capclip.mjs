// the caption's box against the boxes that contain it (is it cut by an ancestor's overflow?) at 390 px
import { launch, startStatic, sleep, SITE } from "./lib.mjs";
await startStatic();
const br = await launch();
for (const world of ["s03_projectile", "u32_double_slit"]) for (const lang of ["en", "ru"]) {
  const ctx = await br.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  await page.goto(`${SITE}/run.html?demo=${world}&screen=watch&lang=${lang}`);
  await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 60000 });
  await page.keyboard.press("Space");
  const n = await page.$$eval(".dm-tick", (b) => b.length);
  const res = [];
  for (let j = 0; j < n; j++) {
    await page.$$eval(".dm-tick", (b, j) => b[j].click(), j); await sleep(250);
    res.push(await page.evaluate(() => {
      const c = document.querySelector(".dm-caption"), r = c.getBoundingClientRect();
      let top = -1e9, bot = 1e9;
      for (let e = c.parentElement; e; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.overflow !== "visible" || cs.overflowY !== "visible") { const b = e.getBoundingClientRect(); top = Math.max(top, b.top); bot = Math.min(bot, b.bottom); } }
      const bar = document.querySelector(".dm-screen[data-screen=watch] .dm-bar").getBoundingClientRect();
      return { cap: [Math.round(r.top), Math.round(r.bottom)], clip: [Math.round(top), Math.round(bot)], barTop: Math.round(bar.top), cutPx: Math.round(Math.max(0, top - r.top) + Math.max(0, r.bottom - Math.min(bot, bar.top))) };
    }));
  }
  console.log(JSON.stringify({ world, lang, cut: res.map((r) => r.cutPx), sample: res[3] || res[0] }));
  await ctx.close();
}
await br.close(); process.exit(0);
