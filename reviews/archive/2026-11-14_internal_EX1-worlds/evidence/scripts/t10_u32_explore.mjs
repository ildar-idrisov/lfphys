// u32 Explore: default at the end of the build-up; λ 400 and 700; d 300; a 10 and 40; traces; overlays; the drawer
import { launch, startStatic, sleep, SRV, SITE, watchErrors } from "./lib.mjs";
const where = process.argv[2] || "site";
const base = where === "site" ? SITE : SRV;
if (where === "site") await startStatic();
const br = await launch();
const S = ".dm-screen[data-screen=explore]";
const pick = async (page, param, value) => { await page.$eval(`${S} .dm-ctl[data-param=${param}]`, (row, value) => {
  const b = [...row.querySelectorAll("button")].find((x) => x.title === value || x.textContent.trim() === value); if (!b) throw new Error("no " + value + " in " + row.innerText); b.click(); }, value);
  await page.waitForFunction(() => { const p = window.__lfExplore.explore.point(); return p && p.W; }); await sleep(900); };
for (const lang of (process.argv[3] || "en,ru").split(",")) for (const w of (process.argv[4] || "1280,390").split(",").map(Number)) {
  const ctx = await br.newContext({ viewport: { width: w, height: w > 500 ? 860 : 844 } });
  const page = await ctx.newPage(); const errs = []; watchErrors(page, errs);
  await page.goto(where === "site" ? `${base}/run.html?demo=u32_double_slit&screen=explore&lang=${lang}` : `${base}/run?demo=u32_double_slit&screen=explore&lang=${lang}`);
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point() && window.__lfExplore.explore.point().W, null, { timeout: 90000 });
  await sleep(1500);
  const tag = `u32e_${where}_${lang}_${w}`;
  const st0 = await page.evaluate(() => { const E = window.__lfExplore.explore.state; return { playing: E.playing, clock: E.clock }; });
  const side = await page.$eval(`${S} .dm-side`, (e) => e.innerText);
  await page.screenshot({ path: `/shots/${tag}_0.png` });
  // let the build-up run to the end
  if (!(await page.evaluate(() => window.__lfExplore.explore.state.playing))) await page.click(`${S} .dm-play`);
  await page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 60000 }); await sleep(300);
  const head = await page.$eval(`${S} .dm-stage`, (e) => e.innerText.slice(0, 200));
  await page.screenshot({ path: `/shots/${tag}_1end.png` });
  const steps = [["lam_nm", "400"], ["lam_nm", "700"], ["d_um", "300"], ["a_um", "10"], ["a_um", "40"]];
  const heads = [];
  for (const [p, v] of steps) { await pick(page, p, v); heads.push([p, v, (await page.$eval(`${S} .dm-stage`, (e) => e.innerText.slice(0, 120))).replace(/\n/g, " / ")]); await page.screenshot({ path: `/shots/${tag}_${p}${v}.png` }); }
  const sw = await page.evaluate(() => [document.scrollingElement.scrollWidth, document.scrollingElement.scrollHeight]);
  console.log(JSON.stringify({ tag, st0, side, head, heads, sw, errs }));
  await ctx.close();
}
await br.close(); process.exit(0);
