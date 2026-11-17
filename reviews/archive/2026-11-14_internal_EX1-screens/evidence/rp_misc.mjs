// R-P probe: addresses (an alias, a world without screens, an unknown world, an unknown screen) and the drawer's folds
import { chromium } from "playwright";
const ROOT = process.argv[2];  // http://127.0.0.1:8702/  (server) or http://127.0.0.1:8702/lfphys/ (site)
const site = ROOT.includes("/lfphys/");
const runp = site ? "run.html" : "run";
const out = (k, v) => console.log(JSON.stringify({ k, site, ...v }));
const br = await chromium.launch();
const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
const page = await ctx.newPage();
const errs = []; page.on("pageerror", (e) => errs.push(e.message.slice(0, 120)));
for (const q of ["demo=v02_double_slit&screen=explore", "demo=u34_orbits", "demo=nonexistent", "demo=s03_projectile&screen=bogus", "demo=s03_projectile&screen=lab&lang=ru"]) {
  await page.goto(`${ROOT}${runp}?${q}`);
  await page.waitForTimeout(3500);
  out(q, { url: page.url().replace(ROOT, ""), tab: await page.evaluate(() => (document.querySelector(".dm-tab.on") || {}).textContent || null),
    text: (await page.evaluate(() => (document.getElementById("demo").hidden ? document.body.innerText : document.getElementById("demo").innerText))).replace(/\s+/g, " ").slice(0, 160) });
}
// the drawer of S03 Explore after a landing: the folds' contents
await page.goto(`${ROOT}${runp}?demo=s03_projectile&screen=explore&lang=en`);
await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 30000 });
await page.locator(".dm-how").click(); await page.waitForTimeout(400);
const before = await page.locator(".dm-drawer-body").innerText();
await page.keyboard.press("Escape");
await page.locator(".dm-play").click(); await page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 30000 });
await page.locator(".dm-how").click(); await page.waitForTimeout(400);
await page.$$eval(".dm-drawer-body details", (d) => d.forEach((x) => { x.open = true; }));
await page.waitForTimeout(200);
const after = await page.locator(".dm-drawer-body").innerText();
out("S03 explore drawer before the launch", { text: before.replace(/\n+/g, " | ").slice(0, 300) });
out("S03 explore drawer after the landing, every fold open", { text: after.replace(/\n+/g, " | ").slice(0, 2400) });
await page.screenshot({ path: `/pw/shots/rp_drawer_s03_${site ? "site" : "srv"}.png` });
out("errors", { errs });
await br.close();
