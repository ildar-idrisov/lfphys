// S03 Explore: default, launch; air on + launch (trace); all overlays mid-flight; a refusal; EN/RU, 1280/390
import { chromium } from "playwright";
import { launch, startStatic, sleep, SRV, SITE, watchErrors } from "./lib.mjs";
const where = process.argv[2] || "srv";
const base = where === "site" ? SITE : SRV;
if (where === "site") await startStatic();
const br = await launch();
const ctlClick = async (page, param, value) => page.$eval(`.dm-screen[data-screen=explore] .dm-ctl[data-param=${param}]`, (row, value) => {
  const b = [...row.querySelectorAll("button")].find((x) => x.dataset.value === value || x.textContent.trim() === value || x.title === value);
  if (!b) throw new Error("no button " + value + " in " + row.innerText); b.click(); }, value);
const landed = async (page) => page.waitForFunction(() => { const E = window.__lfExplore.explore.state; return !E.playing; }, null, { timeout: 30000 });
for (const lang of (process.argv[3] || "en,ru").split(",")) for (const w of (process.argv[4] || "1280,390").split(",").map(Number)) {
  const ctx = await br.newContext({ viewport: { width: w, height: w > 500 ? 860 : 844 } });
  const page = await ctx.newPage();
  const errs = []; watchErrors(page, errs);
  const u = where === "site" ? `${base}/run.html?demo=s03_projectile&screen=explore&lang=${lang}` : `${base}/run?demo=s03_projectile&screen=explore&lang=${lang}`;
  await page.goto(u);
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 60000 });
  await sleep(500);
  const tag = `s03e_${where}_${lang}_${w}`;
  await page.screenshot({ path: `/shots/${tag}_0default.png`, fullPage: true });
  const side = await page.$eval(".dm-screen[data-screen=explore] .dm-side", (e) => e.innerText);
  console.log(JSON.stringify({ tag, side }));
  await page.click(".dm-screen[data-screen=explore] .dm-play"); await landed(page); await sleep(300);
  const ro1 = await page.$$eval(".dm-readout", (r) => r.map((x) => x.innerText.replace(/\n/g, " ")));
  await page.screenshot({ path: `/shots/${tag}_1launched.png`, fullPage: true });
  // air on, launch again
  await ctlClick(page, "air", "true"); await sleep(600);
  await page.click(".dm-screen[data-screen=explore] .dm-play"); await landed(page); await sleep(300);
  const ro2 = await page.$$eval(".dm-readout", (r) => r.map((x) => x.innerText.replace(/\n/g, " ")));
  await page.screenshot({ path: `/shots/${tag}_2air.png`, fullPage: true });
  // all overlays, then a launch and a pause mid-flight
  if (w < 500) await page.$eval(".dm-overlays", (d) => { d.open = true; });
  for (const id of ["strobe", "v", "v_parts", "forces", "energy"]) await page.$eval(`.dm-overlays input[data-overlay=${id}]`, (cb) => { if (!cb.checked) cb.click(); });
  await page.click(".dm-screen[data-screen=explore] .dm-play"); await sleep(700); await page.keyboard.press("Space"); await sleep(300);
  await page.screenshot({ path: `/shots/${tag}_3overlays.png`, fullPage: true });
  // the refusal: h 0, angle 0
  await ctlClick(page, "h_m", "0"); await sleep(400); await ctlClick(page, "angle_deg", "0"); await sleep(800);
  const ref = await page.$eval(".dm-refusal-side", (e) => e.innerText);
  const playDis = await page.$eval(".dm-screen[data-screen=explore] .dm-play", (b) => [b.disabled, b.title]);
  await page.screenshot({ path: `/shots/${tag}_4refused.png`, fullPage: true });
  const sw = await page.evaluate(() => document.scrollingElement.scrollWidth);
  console.log(JSON.stringify({ tag, ro1, ro2, ref, playDis, sw, errs }));
  await ctx.close();
}
await br.close();
process.exit(0);
