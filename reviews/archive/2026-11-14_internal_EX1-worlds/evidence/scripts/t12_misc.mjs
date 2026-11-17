// (a) u32 Explore at λ 500, d 50, a 40 and a 10: the |γ12| readout at the end; (b) S03 Explore on the server: an off-grid
// angle 42° computed live; (c) S03 «▶ Compute live» from Lab part 1: what the live player shows (v0?)
import { launch, sleep, SRV, watchErrors } from "./lib.mjs";
const br = await launch();
{
  const ctx = await br.newContext({ viewport: { width: 1280, height: 860 } }); const page = await ctx.newPage();
  await page.goto(`${SRV}/run?demo=u32_double_slit&screen=explore&lang=en`);
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point() && window.__lfExplore.explore.point().W, null, { timeout: 90000 });
  const S = ".dm-screen[data-screen=explore]";
  for (const [p, v] of [["lam_nm", "500"], ["d_um", "50"], ["a_um", "40"]]) {
    await page.$eval(`${S} .dm-ctl[data-param=${p}]`, (row, v) => [...row.querySelectorAll("button")].find((x) => x.title === v).click(), v); await sleep(1500); }
  await page.click(`${S} .dm-play`); await page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 60000 }); await sleep(300);
  const head = await page.$eval(`${S} .dm-stage`, (e) => e.innerText.split("\n").slice(0, 3).join(" | "));
  console.log(JSON.stringify({ u32: "500/50/40", head }));
  await page.locator(`${S} .dm-stage`).screenshot({ path: "/shots/u32_gamma_500_50_40.png", clip: undefined });
  await ctx.close();
}
{
  const ctx = await br.newContext({ viewport: { width: 1280, height: 860 } }); const page = await ctx.newPage(); const errs = []; watchErrors(page, errs);
  await page.goto(`${SRV}/run?demo=s03_projectile&screen=explore&lang=en`);
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 60000 });
  const S = ".dm-screen[data-screen=explore]";
  // drag the angle slider to 42 (server: fine steps)
  await page.$eval(`${S} .dm-ctl[data-param=angle_deg] input[type=range]`, (i) => { i.value = "42"; i.dispatchEvent(new Event("input")); i.dispatchEvent(new Event("change")); });
  const t0 = Date.now();
  await page.waitForFunction(() => { const p = window.__lfExplore.explore.point(); return p && p.live; }, null, { timeout: 120000 }).catch(() => {});
  const pt = await page.evaluate(() => { const p = window.__lfExplore.explore.point(); return p ? { live: !!p.live, values: p.values, state: p.state } : null; });
  await page.click(`${S} .dm-play`); await page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 30000 }); await sleep(300);
  const ro = await page.$$eval(".dm-readout", (r) => r.map((x) => x.innerText.replace(/\n/g, " ")));
  console.log(JSON.stringify({ s03live: pt, ms: Date.now() - t0, ro, errs }));
  await page.screenshot({ path: "/shots/s03_live42.png" });
  await ctx.close();
}
{
  const ctx = await br.newContext({ viewport: { width: 1280, height: 860 } }); const page = await ctx.newPage();
  await page.goto(`${SRV}/run?demo=s03_projectile&screen=lab&lang=en`);
  await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 60000 });
  await page.click(".dm-live"); await page.waitForURL(/run\?id=/, { timeout: 30000 }); await sleep(4000);
  const body = await page.evaluate(() => document.body.innerText);
  const m = body.match(/Launch speed[^\n]*\n?[^\n]*/);
  console.log(JSON.stringify({ live: page.url(), v0: m ? m[0] : null, hasV15: /1\.5/.test(body) }));
  await page.screenshot({ path: "/shots/s03_lab_compute_live.png" });
  await ctx.close();
}
await br.close(); process.exit(0);
