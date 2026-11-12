// Review LB1-p02-ux, Part B, tour b0: the catalogue's playground mode and the first look at p02 (double slit preset)
// at 1600x1000 and 1280x800, light and dark. Screenshots to /out; the panels' text to the log.
import { browser, base, newRun, openRun, shot, log, sleep, attachErrors } from "./b_lib.mjs";

const br = await browser();
const errs = [];
for (const [W, H] of [[1600, 1000], [1280, 800]]) {
  const page = await br.newPage({ viewport: { width: W, height: H } });
  attachErrors(page, errs);
  await page.goto(`${base}/`);
  await sleep(1500);
  const modes = await page.evaluate(() => [...document.querySelectorAll("button, .tab, a")].map((b) => b.textContent.trim()).filter((t) => /Плейгр|Демонстр/.test(t)));
  log(`b0 ${W}x${H} catalogue mode buttons`, modes);
  const pg = page.locator("text=Плейграунд").first();
  if (await pg.count()) { await pg.click(); await sleep(800); }
  await shot(page, `b0_catalogue_${W}x${H}`);
  await page.close();
}
const id = await newRun("p02_quantum", "double_slit");
log("b0 run", id);
for (const [W, H] of [[1600, 1000], [1280, 800]]) {
  const page = await br.newPage({ viewport: { width: W, height: H } });
  attachErrors(page, errs);
  await openRun(page, id);
  await shot(page, `b0_p02_double_slit_${W}x${H}`);
  const left = await page.evaluate(() => document.querySelector("#left").innerText.slice(0, 3000));
  const right = await page.evaluate(() => document.querySelector("#right").innerText.slice(0, 3000));
  if (W === 1600) { log("b0 LEFT:\n" + left); log("b0 RIGHT:\n" + right); }
  await page.keyboard.press("t");
  await sleep(800);
  await shot(page, `b0_p02_double_slit_${W}x${H}_dark`);
  await page.close();
}
log("b0 page errors", errs);
await br.close();
