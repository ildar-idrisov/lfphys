// the drawer «How we know this is right» on each screen: its text (school list / standard table), after the run's end
import { launch, startStatic, sleep, SITE } from "./lib.mjs";
await startStatic();
const br = await launch();
const lang = process.argv[2] || "en";
async function grab(world, screen, prep) {
  const ctx = await br.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(`${SITE}/run.html?demo=${world}&screen=${screen}&lang=${lang}`);
  await sleep(3000);
  if (prep) await prep(page);
  await page.click(".dm-how"); await sleep(600);
  await page.$$eval(".dm-drawer details", (d) => d.forEach((x) => { x.open = true; })); await sleep(300);
  const txt = await page.$eval(".dm-drawer-body", (e) => e.innerText);
  console.log(`===== ${world} ${screen} ${lang}\n${txt}\n`);
  await page.screenshot({ path: `/shots/drawer_${world}_${screen}_${lang}.png` });
  await ctx.close();
}
const S = (s) => `.dm-screen[data-screen=${s}]`;
await grab("s03_projectile", "explore", async (p) => {
  await p.$eval(`${S("explore")} .dm-ctl[data-param=air] button[data-value=true]`, (b) => b.click()); await sleep(800);
  await p.click(`${S("explore")} .dm-play`); await p.waitForFunction(() => !window.__lfExplore.explore.state.playing); await sleep(300); });
await grab("s03_projectile", "lab", async (p) => { await p.click(`${S("lab")} .dm-play`); await p.waitForFunction(() => !window.__lfLab.state.playing); await sleep(300); });
await grab("s03_projectile", "watch", async (p) => { await p.keyboard.press("Space"); await p.$$eval(".dm-tick", (b) => b[1].click()); for (let k = 0; k < 40; k++) await p.keyboard.press("ArrowRight"); await sleep(300); });
await grab("u32_double_slit", "explore", async (p) => { await p.click(`${S("explore")} .dm-play`); await p.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 60000 }); await sleep(300); });
await br.close(); process.exit(0);
