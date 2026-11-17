// S03 Explore edge points: vertical from the floor at 25 m/s; horizontal from 10 m at 5 m/s; then 3 different shots as traces
import { launch, startStatic, sleep, SITE } from "./lib.mjs";
await startStatic();
const br = await launch();
const ctx = await br.newContext({ viewport: { width: 1280, height: 860 } }); const page = await ctx.newPage();
await page.goto(`${SITE}/run.html?demo=s03_projectile&screen=explore&lang=en`);
await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 60000 });
const S = ".dm-screen[data-screen=explore]";
const set = async (p, v) => { await page.$eval(`${S} .dm-ctl[data-param=${p}]`, (row, v) => [...row.querySelectorAll("button")].find((x) => x.title === v || x.dataset.value === v).click(), v); await sleep(700); };
const fire = async (name) => { await page.click(`${S} .dm-play`); await page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 30000 }); await sleep(300);
  await page.locator(`${S} .dm-stage`).screenshot({ path: `/shots/s03e_${name}.png` }); };
await set("h_m", "0"); await set("v0", "25"); await set("angle_deg", "90"); await fire("vertical");
await page.click(`${S} .dm-clear`);
await set("h_m", "10"); await set("v0", "5"); await set("angle_deg", "0"); await fire("horiz10");
await set("v0", "10"); await fire("horiz10b"); await set("v0", "15"); await fire("horiz10c");
console.log("ok");
await br.close(); process.exit(0);
