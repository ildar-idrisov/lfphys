// w02: records written before the i18n commit (2026-10-28, 2026-11-11), replayed in each language: the run page at the
// end of the record, all panels open, the history played back from the start; scanned and photographed
import { browser, newPage, post, get, sleep, waitPlayer, shot, scan, setLog, log, base, openPanel } from "./r_lib.mjs";
setLog("w02_records");
const runs = (await get("/api/runs")).filter((r) => /^2026(10|1111)/.test(r.id));
log({ records: runs.map((r) => [r.id, r.title, r.state]) });
const br = await browser();
for (const r of runs) {
  for (const L of ["en", "ru"]) {
    const tag = `${r.id.slice(0, 8)}_${r.viz.slice(0, 3)}_${L}`;
    const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
    const page = await newPage(ctx, tag);
    try {
      await page.goto(`${base}/run?id=${r.id}&lang=${L}`);
      await waitPlayer(page, 180000);
      await sleep(2000);
      await scan(page, L, `${tag} record end`);
      await shot(page, `w02_${tag}_end`);
      await openPanel(page, /./);
      await page.evaluate(() => { for (const d of document.querySelectorAll("#right details, #left details")) d.open = true; });
      await sleep(800);
      await scan(page, L, `${tag} panels`);
      for (const side of ["left", "right"]) {
        const panels = await page.$$(`#${side} .panel`);
        let k = 0;
        for (const p of panels) { try { await p.screenshot({ path: `/shots/w02_${tag}_${side}${String(k).padStart(2, "0")}.png` }); } catch (e) { /* hidden */ } k++; }
      }
      // the history from the start, played forwards a little
      await page.keyboard.press("Home"); await sleep(1500);
      await page.click("#fwd"); await sleep(3000); await page.click("#fwd").catch(() => {});
      await sleep(800);
      await scan(page, L, `${tag} replay from start`);
      await shot(page, `w02_${tag}_replay`);
      // help
      await page.click("#help"); await sleep(600);
      await scan(page, L, `${tag} help`);
      await page.keyboard.press("Escape");
    } catch (e) { log({ tag, error: e.message.slice(0, 300) }); await shot(page, `w02_${tag}_error`); }
    await ctx.close();
  }
}
await br.close();
