// w04: v01 (no set-up panel; its live control is the action "Speed (changes at once)"): a speed of 2 c refused, in
// each language; the toast's and the field's text read and photographed
import { browser, newPage, post, del, sleep, startRun, waitPlayer, shot, scan, setLog, log, base } from "./r_lib.mjs";
setLog("w04_v01_refusal");
const br = await browser();
for (const L of ["en", "ru"]) {
  const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
  await ctx.addInitScript(() => { window.__toasts = []; new MutationObserver((ms) => { for (const m of ms) for (const n of m.addedNodes) if (n.nodeType === 1 && n.classList && n.classList.contains("toast")) window.__toasts.push(n.textContent); }).observe(document, { childList: true, subtree: true }); });
  const page = await newPage(ctx, `v01_${L}`);
  const r = await startRun({ viz: "v01_light_travel", seed: 3, preset: "sun_earth" });
  await page.goto(`${base}/run?id=${r.id}&lang=${L}`);
  await waitPlayer(page);
  await page.click("#rec"); await sleep(3000); await page.click("#rec"); await sleep(1000);
  const sel = await page.evaluate(() => { const i = [...document.querySelectorAll("#left input[type=number]")].find((e) => e.closest(".ctl, div") && e.offsetParent && Number(e.max) <= 1.0001 && Number(e.max) > 0); if (i) { i.id = "rv-speed"; return { v: i.value, max: i.max }; } return null; });
  log({ L, speedField: sel });
  if (sel) {
    await page.fill("#rv-speed", "2"); await page.press("#rv-speed", "Enter"); await sleep(2500);
    const errs = await page.evaluate(() => [...document.querySelectorAll(".ctl-err, .field-err")].map((e) => e.textContent).filter(Boolean));
    log({ L, refusal: errs, toasts: await page.evaluate(() => window.__toasts) });
    await scan(page, L, `v01 ${L} refusal`);
    await shot(page, `w04_v01_refusal_${L}`);
  }
  await ctx.close();
  await post(`/api/runs/${r.id}/stop`); await sleep(1500); await del(`/api/runs/${r.id}`);
}
await br.close();
