// S03 Watch: the three first worlds after their landings (steps 140, 340, 630), the view only
import { launch, startStatic, sleep, SITE } from "./lib.mjs";
await startStatic();
const br = await launch();
const ctx = await br.newContext({ viewport: { width: 1280, height: 860 } }); const page = await ctx.newPage();
await page.goto(`${SITE}/run.html?demo=s03_projectile&screen=watch&lang=en`);
await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 60000 });
await page.keyboard.press("Space");
for (const k of [140, 340, 630]) {
  await page.$eval(".dm-timeline", (i, k) => { i.value = String(k); i.dispatchEvent(new Event("input")); }, k); await sleep(500);
  await page.screenshot({ path: `/shots/s03w_landed_${k}.png`, clip: { x: 0, y: 80, width: 940, height: 690 } });
}
await br.close(); process.exit(0);
