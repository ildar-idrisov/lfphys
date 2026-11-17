// R-P probe: a server without local recordings (a fresh checkout: recordings are git-ignored), the public site published:
// the S03 card's screen buttons and the Explore screen. Requests to the public site are answered by a stub with S03 present.
import { chromium } from "playwright";
const port = process.argv[2] || "8702", base = `http://127.0.0.1:${port}`;
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const br = await chromium.launch();
const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
const ext = [];
await ctx.route(/github\.io/, (route) => { ext.push(route.request().url()); route.abort(); });  // no external request leaves
const page = await ctx.newPage();
await page.goto(`${base}/?lang=en#school/s03_projectile`);
await page.waitForSelector("#card-s03_projectile", { timeout: 30000 });
await page.waitForTimeout(1500);
const btns = await page.$$eval("#card-s03_projectile a.st-screen", (a) => a.map((b) => ({ t: b.textContent, off: b.classList.contains("disabled"), title: b.title })));
out("no local recordings: the S03 card", { btns, ext });
await page.goto(`${base}/run?demo=s03_projectile&screen=explore&lang=en`);
await page.waitForTimeout(3000);
out("no local recordings: Explore", { text: (await page.locator("#demo").innerText()).slice(0, 300) });
const u = await page.$$eval("#card-u34_orbits a.button", (a) => a.map((b) => b.textContent)).catch(() => []);
await page.goto(`${base}/?lang=en#university/u34_orbits`); await page.waitForTimeout(1500);
out("no local recordings: u34's «▷ Recording» (falls back to the site when published)", { btns: await page.$$eval("#card-u34_orbits a.button", (a) => a.map((b) => ({ t: b.textContent, off: b.classList.contains("disabled"), title: b.title }))), ext: ext.slice(0, 3) });
await br.close();
