// S03 Lab work, as a student: each part, every grid value: launch, wait for the landing, Measure; then the fit and «Check
// against the law»; screenshots of each part; the texts of the card, the table's first rows, the fit and the check
import { chromium } from "playwright";
import { launch, startStatic, sleep, SRV, SITE, watchErrors } from "./lib.mjs";
const where = process.argv[2] || "site";
const base = where === "site" ? SITE : SRV;
if (where === "site") await startStatic();
const lang = process.argv[3] || "en", w = Number(process.argv[4] || 1280);
const br = await launch();
const ctx = await br.newContext({ viewport: { width: w, height: w > 500 ? 900 : 844 } });
const page = await ctx.newPage(); const errs = []; watchErrors(page, errs);
await page.goto(where === "site" ? `${base}/run.html?demo=s03_projectile&screen=lab&lang=${lang}` : `${base}/run?demo=s03_projectile&screen=lab&lang=${lang}`);
await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 60000 });
await sleep(500);
const S = ".dm-screen[data-screen=lab]";
for (let part = 0; part < 3; part++) {
  await page.$$eval(`${S} .dm-steps button`, (b, k) => b[k].click(), part);
  await page.waitForFunction((k) => window.__lfLab.step() && window.__lfLab.step().cur && window.__lfLab.state.k === k, part, { timeout: 30000 });
  await sleep(400);
  const card = await page.$eval(`${S} .dm-card`, (e) => e.innerText);
  console.log(JSON.stringify({ part, card }));
  const vals = await page.$$eval(`${S} .dm-card .dm-ctl .dm-detent`, (b) => b.map((x) => x.title));
  for (let j = 0; j < vals.length; j++) {
    await page.$$eval(`${S} .dm-card .dm-ctl .dm-detent`, (b, j) => b[j].click(), j);
    await page.waitForFunction(() => !window.__lfLab.step().msg || true); await sleep(250);
    await page.click(`${S} .dm-play`);
    await page.waitForFunction(() => !window.__lfLab.state.playing, null, { timeout: 30000 }); await sleep(150);
    if (part === 0 && j === 8) await page.screenshot({ path: `/shots/lab_${where}_${lang}_${w}_p${part}_landed.png` });
    await page.click(`${S} .dm-measure`); await sleep(120);
  }
  // fits
  const fits = await page.$$eval(`${S} .dm-work select[aria-label]`, (s) => s.map((x) => [x.getAttribute("aria-label"), [...x.options].map((o) => o.value + "=" + o.text), x.value]));
  const fitText = await page.$eval(`${S} .dm-fit`, (e) => e.innerText);
  await page.click(`${S} .dm-check-law`); await sleep(300);
  const law = await page.$eval(`${S} .dm-law`, (e) => e.innerText);
  const rows = await page.$$eval(`${S} .dm-table tbody tr`, (r) => r.slice(0, 3).map((x) => x.innerText.replace(/\s+/g, " ")));
  console.log(JSON.stringify({ part, n: vals.length, vals, fits, fitText, law, rows }));
  await page.screenshot({ path: `/shots/lab_${where}_${lang}_${w}_p${part}.png`, fullPage: true });
  // the other fits offered
  const opts = await page.$$eval(`${S} .dm-work select[aria-label]`, (s) => [...s[2].options].map((o) => o.value));
  for (const m of opts) {
    await page.$eval(`${S} .dm-work select[aria-label]:nth-of-type(1)`, () => {});
    await page.evaluate((m) => { const s = [...document.querySelectorAll(".dm-screen[data-screen=lab] .dm-work select[aria-label]")][2]; s.value = m; s.dispatchEvent(new Event("change")); }, m);
    await sleep(200);
    const ft = await page.$eval(`${S} .dm-fit`, (e) => e.innerText);
    await page.click(`${S} .dm-check-law`); await sleep(200);
    const lw = await page.$eval(`${S} .dm-law`, (e) => e.innerText);
    console.log(JSON.stringify({ part, model: m, ft, lw }));
  }
  // also L against theta / h (the other x axis), with the parabola where offered
  const csv = await page.$eval(`${S} a[download]`, (a) => decodeURIComponent(a.href.split(",").slice(1).join(",")));
  console.log(JSON.stringify({ part, csv: csv.split("\n").slice(0, 4) }));
}
console.log(JSON.stringify({ errs }));
await br.close();
process.exit(0);
