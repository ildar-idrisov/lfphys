// Response to the C1 review: a smoke check of the processed player on every visualization (own server 127.0.0.1:8501):
// start a run (default scenario), ⏺ for 5 s, pause, the cursor to the middle, then ⏭; page errors, console errors, the
// status and the time at each step; then the page reloaded (the record replayed): the status after loading.
// Output: out/r00_smoke_all_worlds.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8501";
const OUT = process.env.OUT || "/pw/c1proc_out";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const ids = (await (await fetch(base + "/api/viz")).json()).map((v) => v.id);
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const lines = [];
for (const viz of ids) {
  const errs = [];
  const r = await post("/api/runs", { viz, seed: 1 });
  if (!r.id) { lines.push(`${viz}: start refused: ${JSON.stringify(r)}`); continue; }
  const page = await browser.newPage({ viewport: { width: 1600, height: 950 } });
  page.on("pageerror", (e) => errs.push("pageerror " + String(e).slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console " + m.text().slice(0, 160)); });
  const st = () => page.evaluate(() => `${document.getElementById("status").textContent} | ${document.getElementById("time").textContent} | ${document.getElementById("timeline").value}/${document.getElementById("timeline").max}`);
  await page.goto(`${base}/run?id=${r.id}`);
  await page.waitForTimeout(3000);
  await page.click("#rec"); await page.waitForTimeout(5000);
  const a = await st();
  await page.click("#rec"); await page.waitForTimeout(1500);
  const max = await page.evaluate(() => +document.getElementById("timeline").max);
  await page.evaluate((i) => { const t = document.getElementById("timeline"); t.value = String(i); t.dispatchEvent(new Event("input")); }, Math.floor(max / 2));
  await page.waitForTimeout(2500);
  const b = await st();
  await page.click("#toend"); await page.waitForTimeout(2000);
  const c = await st();
  await page.reload(); await page.waitForTimeout(5000);
  const d = await st();
  lines.push(`${viz}: recording [${a}] · middle [${b}] · end [${c}] · reloaded [${d}] · errors: ${errs.length ? errs.join("; ") : "none"}`);
  console.log(lines[lines.length - 1]);
  await page.close();
  await post(`/api/runs/${r.id}/stop`);
}
fs.writeFileSync(`${OUT}/r00_smoke_all_worlds.txt`, lines.join("\n") + "\n");
await browser.close();
