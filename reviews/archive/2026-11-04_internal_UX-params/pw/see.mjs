// What the user sees on the run page: toasts, the events panel, the transport state; a screenshot.
// usage: node see.mjs cases.json out.json   (cases: [{name, id?, start?: {viz, preset?, params?}, cmds?: [[cmd, args, waitMs]], wait}])
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8563";
const post = async (u, b) => { const r = await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) }); return [r.status, await r.json().catch(() => null)]; };
const cases = JSON.parse(fs.readFileSync(process.argv[2]));
const out = [];
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
for (const c of cases) {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const errs = [];
  page.on("pageerror", (e) => errs.push("pageerror: " + String(e.stack || e).slice(0, 400)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 300)); });
  const toasts = new Set();
  let id = c.id, start = null;
  if (c.catalog) {  // the user's path: the catalogue's form, then ▶
    await page.goto(base + "/");
    await page.waitForTimeout(1500);
    start = await page.evaluate(async (c) => {
      const r = await fetch("/api/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(c.start) });
      return [r.status, await r.json()];
    }, c);
    if (start[0] === 200) id = start[1].id;
  } else if (c.start) {
    start = await post("/api/runs", c.start);
    if (start[0] === 200) id = start[1].id;
  }
  const rec = { name: c.name, start, id };
  if (id) {
    await page.goto(base + "/run?id=" + id);
    const poll = setInterval(async () => {
      try { for (const t of await page.$$eval(".toast", (xs) => xs.map((x) => x.textContent))) toasts.add(t); } catch (e) { /* navigating */ }
    }, 300);
    await page.waitForTimeout(c.wait || 6000);
    for (const [cmd, args, w] of c.cmds || []) {
      await post(`/api/runs/${id}/command`, { cmd, args });
      await page.waitForTimeout(w || 2000);
    }
    clearInterval(poll);
    for (const t of await page.$$eval(".toast", (xs) => xs.map((x) => x.textContent))) toasts.add(t);
    rec.toasts = [...toasts];
    rec.events = await page.evaluate(() => { const b = document.querySelector(".events"); return b ? b.innerText.slice(0, 1500) : null; });
    rec.top = await page.evaluate(() => document.body.innerText.slice(0, 600));
    rec.checks = await page.evaluate(() => { const b = document.querySelector(".checks"); return b ? b.innerText.slice(0, 2500) : null; });
    rec.pageErrors = errs;
    await page.screenshot({ path: `shots/${c.name}.png` });
  }
  out.push(rec);
  fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
  console.log(JSON.stringify(rec).slice(0, 900));
  await page.close();
}
await browser.close();
