import { chromium } from "playwright";
const base = "http://127.0.0.1:8682";
const br = await chromium.launch();
const ctx = await br.newContext({ viewport: { width: 1280, height: 700 } });
const r = await (await fetch(base + "/api/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ viz: "u31_light_travel", preset: "sun_earth" }) })).json();
const a = await ctx.newPage();
await a.goto(`${base}/run?id=${r.id}&lang=ru`);
await a.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
await a.click("#rec");
await new Promise((ok) => setTimeout(ok, 3000));
for (const lang of ["en", "ru"]) {
  const b = await ctx.newPage();
  await b.goto(`${base}/?lang=${lang}`);
  await b.waitForSelector("#continue a", { timeout: 20000 }).catch(() => {});
  console.log(JSON.stringify({ lang, cont: await b.evaluate(() => document.getElementById("continue")?.innerText), playerStatus: await a.evaluate(() => document.getElementById("status").textContent + " | " + document.getElementById("rec").textContent) }));
  await b.screenshot({ path: `/shots/e7_continue_${lang}.png` });
  await b.close();
}
await a.click("#rec");
await br.close();
