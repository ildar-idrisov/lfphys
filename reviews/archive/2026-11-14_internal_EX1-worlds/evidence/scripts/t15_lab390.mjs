// S03 Lab work at 390 px (RU): three measurements in part 1; where is the view when «Измерить» is pressed; full page
import { launch, startStatic, sleep, SITE } from "./lib.mjs";
await startStatic();
const br = await launch();
const ctx = await br.newContext({ viewport: { width: 390, height: 844 } }); const page = await ctx.newPage();
await page.goto(`${SITE}/run.html?demo=s03_projectile&screen=lab&lang=ru`);
await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 60000 });
const S = ".dm-screen[data-screen=lab]";
for (const j of [0, 8, 16]) {
  await page.$$eval(`${S} .dm-card .dm-ctl .dm-detent`, (b, j) => b[j].click(), j); await sleep(200);
  await page.click(`${S} .dm-play`); await page.waitForFunction(() => !window.__lfLab.state.playing, null, { timeout: 30000 }); await sleep(100);
  await page.click(`${S} .dm-measure`); await sleep(150);
}
const geo = await page.evaluate(() => { const r = (s) => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.top), Math.round(b.bottom)]; };
  return { canvas: r(".dm-screen[data-screen=lab] .dm-stage canvas"), measure: r(".dm-screen[data-screen=lab] .dm-measure"), bar: r(".dm-screen[data-screen=lab] .dm-bar"), table: r(".dm-screen[data-screen=lab] .dm-table"), plot: r(".dm-screen[data-screen=lab] .dm-plot"), sh: document.scrollingElement.scrollHeight, sw: document.scrollingElement.scrollWidth }; });
console.log(JSON.stringify(geo));
await page.screenshot({ path: "/shots/lab390_measure_view.png" });
await page.screenshot({ path: "/shots/lab390_full.png", fullPage: true });
await br.close(); process.exit(0);
