// C1 review, check 15: (1) what the player says for a run whose rebuild failed (RUN from c14); (2) the catalogue's
// row of a run that computes but has no viewer (its tab was just closed): can the owner delete it? Own server only.
// Output: out/c15_catalogue_and_failed.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8502";
const OUT = process.env.OUT || "/pw/c1rev_out";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
const page = await browser.newPage({ viewport: { width: 1500, height: 900 } });
if (process.env.RUN) {
  await page.goto(`${base}/run?id=${process.env.RUN}`); await page.waitForTimeout(4000);
  const st = await page.evaluate(() => ({ status: document.getElementById("status").textContent, rec: document.getElementById("rec").disabled ? "⏺ disabled" : "⏺ enabled",
    errors: [...document.querySelectorAll(".events .ev.err")].map((e) => e.textContent.slice(0, 120)) }));
  log(`(1) failed run ${process.env.RUN}: status «${st.status}», ${st.rec}; error events ${JSON.stringify(st.errors)}`);
}
const r = await post("/api/runs", { viz: "v01_light_travel", seed: 12 });
const p2 = await browser.newPage(); await p2.goto(`${base}/run?id=${r.id}`); await p2.waitForTimeout(3000);
await p2.click("#rec"); await p2.waitForTimeout(2000); await p2.close();  // the owner records, then closes the tab
await page.goto(base + "/"); await page.waitForTimeout(3000);
const row = async () => page.evaluate((id) => { const tr = [...document.querySelectorAll("tr")].find((t) => t.textContent.includes(id)); return tr ? { text: tr.innerText.replace(/\s+/g, " ").slice(0, 200), buttons: [...tr.querySelectorAll("button")].map((b) => `${b.textContent}${b.title ? " («" + b.title + "»)" : ""}`) } : null; }, r.id);
log(`(2) run ${r.id} just recorded, tab closed: catalogue row ${JSON.stringify(await row())}`);
const del = await fetch(`${base}/api/runs/${r.id}`, { method: "DELETE" });
log(`    DELETE: ${del.status} ${JSON.stringify(await del.json())}`);
await post(`/api/runs/${r.id}/stop`);
fs.writeFileSync(`${OUT}/c15_catalogue_and_failed.txt`, lines.join("\n") + "\n");
await browser.close();
