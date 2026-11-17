// does every caption fit its strip? (scrollHeight > clientHeight → clipped); the caption's box against the view's canvas
import { launch, startStatic, sleep, SITE, watchErrors } from "./lib.mjs";
await startStatic();
const br = await launch();
for (const world of ["s03_projectile", "u32_double_slit"]) for (const lang of ["en", "ru"]) for (const w of [390, 1280]) {
  const ctx = await br.newContext({ viewport: { width: w, height: w > 500 ? 860 : 844 } });
  const page = await ctx.newPage();
  await page.goto(`${SITE}/run.html?demo=${world}&screen=watch&lang=${lang}`);
  await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 60000 });
  await page.keyboard.press("Space");
  const n = await page.$$eval(".dm-tick", (b) => b.length);
  const out = [];
  for (let j = 0; j < n; j++) {
    await page.$$eval(".dm-tick", (b, j) => b[j].click(), j); await sleep(250);
    out.push(await page.evaluate(() => { const c = document.querySelector(".dm-caption"); const cs = getComputedStyle(c);
      return { sh: c.scrollHeight, ch: c.clientHeight, ov: cs.overflowY, fs: cs.fontSize }; }));
  }
  const clipped = out.map((o, j) => (o.sh > o.ch + 1 ? j : null)).filter((x) => x !== null);
  console.log(JSON.stringify({ world, lang, w, clipped, first: out[0] }));
  await ctx.close();
}
await br.close(); process.exit(0);
