// u32 Watch «More recordings»: each one at its second caption + 10 s; the stage's readout line
import { launch, startStatic, sleep, SITE } from "./lib.mjs";
await startStatic();
const br = await launch();
for (const lang of ["en", "ru"]) {
  const ctx = await br.newContext({ viewport: { width: 1280, height: 860 } }); const page = await ctx.newPage();
  await page.goto(`${SITE}/run.html?demo=u32_double_slit&screen=watch&lang=${lang}`);
  await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 60000 });
  const opts = await page.$$eval("select.dm-more option", (o) => o.map((x) => [x.value, x.textContent]));
  console.log(JSON.stringify({ lang, opts }));
  for (const [id] of opts.slice(1)) {
    await page.selectOption("select.dm-more", id);
    await page.waitForFunction((id) => window.__lfWatch.state.rec && window.__lfWatch.state.rec.id === id && window.__lfWatch.state.story, id, { timeout: 60000 });
    await page.keyboard.press("Space"); await sleep(200);
    if (await page.evaluate(() => window.__lfWatch.state.playing)) await page.keyboard.press("Space");
    await page.$$eval(".dm-tick", (b) => b[b.length - 1].click()); await sleep(300);
    // to the end
    await page.$eval(".dm-timeline", (i) => { i.value = i.max; i.dispatchEvent(new Event("input")); }); await sleep(500);
    const o = await page.evaluate(() => ({ cap: window.__lfWatch.caption(), head: document.querySelector(".dm-screen[data-screen=watch] .dm-stage").innerText.split("\n").slice(0, 3).join(" | ") }));
    console.log(JSON.stringify({ lang, id, ...o }));
    if (lang === "en") await page.screenshot({ path: `/shots/u32_more_${id}.png` });
  }
  await ctx.close();
}
await br.close(); process.exit(0);
