// S03 Lab work: «Check against the law» with other axes than the step's (part 1 L(h); part 2 L(θ) parabola and line0;
// part 3 the grey ball's column); the texts in RU
import { chromium } from "playwright";
import { launch, startStatic, sleep, SITE, watchErrors } from "./lib.mjs";
await startStatic();
const lang = process.argv[2] || "en";
const br = await launch();
const ctx = await br.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage(); const errs = []; watchErrors(page, errs);
await page.goto(`${SITE}/run.html?demo=s03_projectile&screen=lab&lang=${lang}`);
await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 60000 });
await sleep(400);
const S = ".dm-screen[data-screen=lab]";
const sel = async (k, v) => { await page.evaluate(([k, v]) => { const s = [...document.querySelectorAll(".dm-screen[data-screen=lab] .dm-work select[aria-label]")][k]; s.value = v; s.dispatchEvent(new Event("change")); }, [k, v]); await sleep(200); };
const check = async (tag) => { const ft = await page.$eval(`${S} .dm-fit`, (e) => e.innerText); const b = await page.$(`${S} .dm-check-law`); if (b && !(await b.isDisabled())) await b.click(); await sleep(200);
  const lw = await page.$eval(`${S} .dm-law`, (e) => e.innerText); console.log(JSON.stringify({ tag, ft, lw })); };
async function runPart(part, picks) {
  await page.$$eval(`${S} .dm-steps button`, (b, k) => b[k].click(), part);
  await page.waitForFunction((k) => window.__lfLab.state.k === k && window.__lfLab.step() && window.__lfLab.step().cur, part); await sleep(300);
  const n = await page.$$eval(`${S} .dm-card .dm-ctl .dm-detent`, (b) => b.length);
  // the table is kept per step in localStorage: clear it first
  await page.click(`${S} .dm-work button:has-text("${lang === "ru" ? "Очистить" : "Clear"}")`).catch(() => {});
  for (const j of picks(n)) {
    await page.$$eval(`${S} .dm-card .dm-ctl .dm-detent`, (b, j) => b[j].click(), j); await sleep(200);
    await page.click(`${S} .dm-play`); await page.waitForFunction(() => !window.__lfLab.state.playing, null, { timeout: 30000 }); await sleep(100);
    await page.click(`${S} .dm-measure`); await sleep(100);
  }
}
// part 1: all heights; L(h) with line0 and line
await runPart(0, (n) => [...Array(n).keys()]);
await check("p1 default");
await sel(0, "h"); await check("p1 x=h line0");
await sel(2, "line"); await check("p1 x=h line");
// part 1, a measurement before the landing
await page.$$eval(`${S} .dm-card .dm-ctl .dm-detent`, (b) => b[3].click()); await sleep(200);
await page.click(`${S} .dm-measure`); await sleep(200);
console.log(JSON.stringify({ tag: "p1 measure before launch", msg: await page.$eval(`${S} .dm-msg`, (e) => e.innerText) }));
// part 2: all angles; L(θ) parabola; L(θ) line0
await runPart(1, (n) => [...Array(n).keys()]);
await sel(0, "theta"); await sel(2, "quadratic"); await check("p2 x=theta quadratic");
await sel(2, "line0"); await check("p2 x=theta line0");
// part 2 with only 15..45 (one side): the parabola
await page.click(`${S} .dm-work button:has-text("${lang === "ru" ? "Очистить" : "Clear"}")`); await sleep(200);
await runPart(1, () => [0, 1, 2, 3, 4, 5, 6]);
await sel(0, "theta"); await sel(2, "quadratic"); await check("p2 15-45 quadratic");
// part 3: the grey ball's column as y
await runPart(2, (n) => [...Array(n).keys()]);
await sel(1, "L_vac"); await check("p3 y=L_vac quadratic");
await sel(1, "L"); await check("p3 y=L quadratic");
console.log(JSON.stringify({ errs }));
await br.close(); process.exit(0);
