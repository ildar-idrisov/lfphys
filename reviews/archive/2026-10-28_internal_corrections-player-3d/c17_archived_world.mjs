// C1 review, check 17: an archived world (world 1 of 2) in the player: the timeline is that world's, ◀ / ⏮ / ⏭ move in
// it, ⏺ is refused, and a recording of the current world going on meanwhile does not move its view. Own server only.
// Output: out/c17_archived_world.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8502";
const OUT = process.env.OUT || "/pw/c1rev_out";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
const page = await browser.newPage({ viewport: { width: 1500, height: 900 } });
const errs = [];
page.on("pageerror", (e) => errs.push(e.message));
const ui = () => page.evaluate(() => ({ tl: `${document.getElementById("timeline").value}/${document.getElementById("timeline").max}`, time: document.getElementById("time").textContent,
  status: document.getElementById("status").textContent, rec: document.getElementById("rec").disabled ? "⏺ off" : "⏺ on", world: document.getElementById("world").value,
  banner: (document.querySelector(".banner") || {}).textContent || "" }));
const r = await post("/api/runs", { viz: "v04_orbits", seed: 4 });
await page.goto(`${base}/run?id=${r.id}`); await page.waitForTimeout(3000);
await page.click("#rec"); await page.waitForTimeout(5000);
await post(`/api/runs/${r.id}/command`, { cmd: "new_world", args: { params: { r0: 30 } } });
await page.waitForTimeout(2000);
await page.click("#rec").catch(() => {}); await page.waitForTimeout(500);
if (!(await page.evaluate(() => document.getElementById("rec").textContent.includes("⏸")))) await page.click("#rec");
await page.waitForTimeout(4000);  // world 2 records
log(`world 2 recording: ${JSON.stringify(await ui())}`);
await page.selectOption("#world", "0"); await page.waitForTimeout(1500);
const a = await ui(); log(`world 1 selected while world 2 records: ${JSON.stringify(a)}`);
await page.waitForTimeout(3000);
const b = await ui(); log(`3 s later (world 2 still recording): ${JSON.stringify(b)} -> world 1's timeline ${a.tl === b.tl ? "unchanged" : "CHANGED"}`);
await page.click("#tostart"); await page.waitForTimeout(1000); log(`⏮: ${JSON.stringify(await ui())}`);
await page.click("#toend"); await page.waitForTimeout(1000); await page.click("#back"); await page.waitForTimeout(2000); await page.click("#back");
log(`⏭ then ◀ for 2 s: ${JSON.stringify(await ui())}`);
await page.keyboard.press("Space"); await page.waitForTimeout(800);
log(`Space (⏺) in world 1: toasts ${JSON.stringify(await page.evaluate(() => [...document.querySelectorAll(".toast")].map((t) => t.textContent)))}`);
await page.selectOption("#world", "1"); await page.waitForTimeout(1500);
log(`back to world 2: ${JSON.stringify(await ui())}`);
log(errs.length ? "page errors: " + errs.join(" | ") : "no page errors");
await post(`/api/runs/${r.id}/stop`);
fs.writeFileSync(`${OUT}/c17_archived_world.txt`, lines.join("\n") + "\n");
await browser.close();
