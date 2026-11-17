// S03 Watch: each caption's frame and a moment later; the caption text, the time label, the info; EN/RU, 1280/390
import { chromium } from "playwright";
import { launch, startStatic, sleep, SRV, SITE, watchErrors } from "./lib.mjs";
const where = process.argv[2] || "srv";
const base = where === "site" ? SITE : SRV;
if (where === "site") await startStatic();
const br = await launch();
for (const lang of (process.argv[3] || "en,ru").split(",")) for (const w of (process.argv[4] || "1280,390").split(",").map(Number)) {
  const ctx = await br.newContext({ viewport: { width: w, height: w > 500 ? 860 : 844 } });
  const page = await ctx.newPage();
  const errs = []; watchErrors(page, errs);
  const u = where === "site" ? `${base}/run.html?demo=u32_double_slit&screen=watch&lang=${lang}` : `${base}/run?demo=u32_double_slit&screen=watch&lang=${lang}`;
  await page.goto(u);
  await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 60000 });
  await page.keyboard.press("Space"); // pause
  const ticks = await page.$$eval(".dm-tick", (b) => b.map((x) => x.title));
  const nt = ticks.length;
  for (let j = 0; j < nt; j++) {
    await page.$$eval(".dm-tick", (b, j) => b[j].click(), j);
    await sleep(400);
    for (const extra of [0, 50]) {   // the caption's frame, then 50 frames (2.5 s played) later
      if (extra) { for (let k = 0; k < extra; k++) await page.keyboard.press("ArrowRight"); await sleep(300); }
      const o = await page.evaluate(() => ({ ro: (document.querySelector(".dm-screen[data-screen=watch] .dm-stage") || document.body).innerText.slice(0, 400), cap: window.__lfWatch.caption(), step: window.__lfWatch.step(), time: document.querySelector(".dm-time").textContent,
        info: document.querySelector(".dm-watch-info").innerText, sw: document.scrollingElement.scrollWidth }));
      console.log(JSON.stringify({ where, lang, w, j, extra, ...o }));
      await page.screenshot({ path: `/shots/u32w_${where}_${lang}_${w}_c${j}_${extra}.png` });
    }
  }
  console.log(JSON.stringify({ where, lang, w, errs }));
  await ctx.close();
}
await br.close();
process.exit(0);
