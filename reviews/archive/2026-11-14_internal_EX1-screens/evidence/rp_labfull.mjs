// R-P probe: every part of the S03 lab measured over its whole grid, then «Check against the law» (the language of LFVIZ_LANG)
import { chromium } from "playwright";
const port = process.argv[2] || "8702", base = `http://127.0.0.1:${port}`;
const LANG = process.env.LFVIZ_LANG || "en";
const SH = process.env.SHOTS || "/pw/shots";
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const settle = (page, ms = 300) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
const ctx = await br.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();
await page.goto(`${base}/run?demo=s03_projectile&screen=lab&lang=${LANG}`);
await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 30000 });
await page.evaluate(() => localStorage.clear());
for (const k of [0, 1, 2]) {
  await page.locator(".dm-steps button").nth(k).click();
  await page.waitForFunction((k) => window.__lfLab.state.k === k && window.__lfLab.step() && window.__lfLab.step().cur, k, { timeout: 30000 });
  await page.evaluate(() => { const s = window.__lfLab.step(); s.rows.length = 0; });
  const param = await page.evaluate(() => window.__lfLab.step().A.controls[0].param);
  const n = await page.locator(`.dm-ctl[data-param="${param}"] .dm-detent`).count();
  for (let j = 0; j < n; j++) {
    await page.locator(`.dm-ctl[data-param="${param}"] .dm-detent`).nth(j).click();
    await page.waitForFunction(([p, j]) => { const s = window.__lfLab.step(); return s.cur && s.cur.pt.values[p] === s.A.controls[0].values[j]; }, [param, j], { timeout: 10000 });
    await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max; s.dispatchEvent(new Event("input")); });
    await settle(page, 30);
    await page.locator(".dm-measure").click();
  }
  await page.locator(".dm-check-law").click(); await settle(page, 200);
  const law = await page.locator(".dm-law").innerText();
  const fit = await page.locator(".dm-fit").innerText();
  out(`part ${k + 1}: ${n} points measured`, { fit, law, rows: await page.evaluate(() => window.__lfLab.rows().length) });
  await page.locator(".dm-plot").scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${SH}/rp_labfull_${k + 1}_${LANG}.png`, fullPage: true });
}
// part 3: the grey ball's L against θ, the step's own check
await page.locator(".dm-work select").nth(1).selectOption("L_vac"); await settle(page, 200);
await page.locator(".dm-check-law").click(); await settle(page, 200);
out("part 3 with y = L in vacuum (the grey ball)", { fit: await page.locator(".dm-fit").innerText(), law: await page.locator(".dm-law").innerText() });
// part 1 with x = h
await page.locator(".dm-steps button").nth(0).click(); await settle(page, 400);
await page.locator(".dm-work select").nth(0).selectOption("h"); await settle(page, 200);
await page.locator(".dm-check-law").click(); await settle(page, 200);
out("part 1 with x = h (not √h)", { fit: await page.locator(".dm-fit").innerText(), law: await page.locator(".dm-law").innerText() });
await br.close();
