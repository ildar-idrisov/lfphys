// w05: a Russian user types a decimal comma into a number field (v05 wavelength, 600,5) — with the browser's own locale
// en-US (Playwright's default) and ru-RU; what the field holds and what the world received
import { browser, newPage, post, get, del, sleep, startRun, waitPlayer, shot, setLog, log, base } from "./r_lib.mjs";
setLog("w05_comma_input");
const br = await browser();
for (const locale of ["en-US", "ru-RU"]) {
  const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 }, locale });
  const page = await newPage(ctx, `comma_${locale}`);
  const r = await startRun({ viz: "v05_optics_bench", seed: 3 });
  await page.goto(`${base}/run?id=${r.id}&lang=ru`);
  await waitPlayer(page);
  await sleep(1500);
  const id = await page.evaluate(() => { const i = [...document.querySelectorAll("#left input[type=number]")][0]; i.id = "rv-n"; return { value: i.value, shown: i.value }; });
  await page.click("#rv-n", { clickCount: 3 });
  await page.keyboard.type("600,5");
  const typed = await page.evaluate(() => ({ value: document.getElementById("rv-n").value, valid: document.getElementById("rv-n").validity.valid, bad: document.getElementById("rv-n").validity.badInput }));
  await page.keyboard.press("Enter");
  await sleep(2500);
  const after = await page.evaluate(() => ({ value: document.getElementById("rv-n")?.value, errs: [...document.querySelectorAll(".ctl-err, .field-err")].map((e) => e.textContent).filter(Boolean), toasts: [...document.querySelectorAll(".toast")].map((e) => e.textContent) }));
  const run = await get(`/api/runs`);
  log({ locale, before: id, typed, after });
  await shot(page, `w05_comma_${locale}`);
  // the same with a point
  await page.click("#rv-n", { clickCount: 3 });
  await page.keyboard.type("600.5");
  const typed2 = await page.evaluate(() => ({ value: document.getElementById("rv-n").value, badInput: document.getElementById("rv-n").validity.badInput }));
  await page.keyboard.press("Enter"); await sleep(2000);
  log({ locale, point: typed2, after: await page.evaluate(() => ({ value: document.getElementById("rv-n")?.value, errs: [...document.querySelectorAll(".ctl-err, .field-err")].map((e) => e.textContent).filter(Boolean) })) });
  await ctx.close();
  await post(`/api/runs/${r.id}/stop`); await sleep(1500); await del(`/api/runs/${r.id}`);
}
await br.close();
