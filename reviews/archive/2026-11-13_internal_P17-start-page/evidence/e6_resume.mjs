import { chromium } from "playwright";
const base = "http://127.0.0.1:8682";
const br = await chromium.launch();
const page = await (await br.newContext({ viewport: { width: 1600, height: 1000 } })).newPage();
const errs = []; page.on("pageerror", (e) => errs.push(e.message));
for (const id of ["20261111-170830-v04-2ca9", "20261111-171659-v02-8d90"]) {
  await page.goto(`${base}/run?id=${id}&lang=en`);
  await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
  const f0 = await page.evaluate(() => window.__lfPlayer.frames());
  await page.click("#rec");
  let st = "";
  for (let i = 0; i < 60; i++) { await new Promise((r) => setTimeout(r, 2000)); st = await page.evaluate(() => document.getElementById("status").textContent); const f = await page.evaluate(() => window.__lfPlayer.frames()); if (f > f0 + 20) break; }
  const f1 = await page.evaluate(() => window.__lfPlayer.frames());
  console.log(JSON.stringify({ id, f0, f1, st, errs }));
  await page.click("#rec").catch(() => {});
}
await br.close();
