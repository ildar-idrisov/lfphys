// review P, e4: a server with no local recordings (a fresh clone: recordings are git-ignored)
import { chromium } from "playwright";
const base = process.argv[2] || "http://127.0.0.1:8682";
const L = (k, v) => console.log(JSON.stringify({ k, v }));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch();
const ctx = await br.newContext({ viewport: { width: 1280, height: 900 } });
for (const lang of ["en", "ru"]) {
  const page = await ctx.newPage();
  const ext = [];
  page.on("request", (r) => { if (!r.url().startsWith(base)) ext.push(r.url()); });
  await page.goto(`${base}/?lang=${lang}#university`);
  await page.waitForSelector(".st-card");
  await sleep(800);
  const b = await page.$$eval(".st-card a.button", (a) => a.map((e) => ({ text: e.textContent, off: e.classList.contains("disabled"), title: e.title, href: e.getAttribute("href") })));
  L(lang + " university buttons (no local recordings)", { n: b.length, enabled: b.filter((x) => !x.off).length, sample: b.slice(0, 2) });
  await page.screenshot({ path: `/shots/e4_univ_norec_${lang}.png`, clip: { x: 0, y: 0, width: 1280, height: 900 } });
  await Promise.all([page.waitForURL(/rec=/), page.click("#card-u32_double_slit a.button")]);
  await sleep(5000);
  L(lang + " after click", { url: page.url(), body: (await page.evaluate(() => document.body.innerText)).slice(0, 300), ext });
  await page.screenshot({ path: `/shots/e4_click_norec_${lang}.png` });
  await page.close();
}
await br.close();
