// C1 review, check 07: slice planes edited while the cursor is in the history (a time-evolving 3-D world, v13).
// The `view` command is applied by the run at the END of its record (the world's current time) and its answers
// (`planes`, `slice`) carry that time; the player feeds the view only messages up to the cursor. What does the owner
// see after «＋ Срез» in the middle of the history — and on a suspended run (a `view` resumes it)?
// Own server 127.0.0.1:8502 only. Output: out/c07_planes_in_history.txt (+ c07_*.png)
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8502";
const OUT = process.env.OUT || "/pw/c1rev_out";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const getj = async (u) => (await fetch(base + u)).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
const state = () => page.evaluate(() => {
  const sc = document.querySelector(".s3d-view").__scene3d;
  return {
    timeline: `${document.getElementById("timeline").value}/${document.getElementById("timeline").max}`,
    time: document.getElementById("time").textContent,
    status: document.getElementById("status").textContent,
    busy: document.getElementById("busy").style.display !== "none" ? document.getElementById("busy").textContent : "",
    planes3d: sc.planes().map((P) => P.id),
    windows: [...document.querySelectorAll(".slicewin")].map((w) => w.querySelector(".sw-title").textContent.slice(0, 40) + " [" + w.querySelector(".sw-status").textContent.slice(0, 60) + "]"),
  };
});
const setTL = (i) => page.evaluate((i) => { const t = document.getElementById("timeline"); t.value = String(i); t.dispatchEvent(new Event("input")); }, i);
const r = await post("/api/runs", { viz: "v13_hydrogen_3d", seed: 1 });
await page.goto(base + "/run?id=" + r.id);
await page.waitForTimeout(5000);
await page.click("#rec"); await page.waitForTimeout(10000); await page.click("#rec"); await page.waitForTimeout(1500);
log(`v13 run ${r.id}, recorded: ${JSON.stringify(await state())}`);
const max = await page.evaluate(() => +document.getElementById("timeline").max);
await setTL(Math.floor(max / 2)); await page.waitForTimeout(2000);
log(`cursor in the middle: ${JSON.stringify(await state())}`);
await page.click("text=＋ Срез"); await page.waitForTimeout(6000);
log(`6 s after «＋ Срез» in the middle: ${JSON.stringify(await state())}`);
await page.screenshot({ path: `${OUT}/c07_v13_middle_after_add.png` });
await page.click("#toend"); await page.waitForTimeout(2500);
log(`after ⏭ (the end): ${JSON.stringify(await state())}`);
// suspended: release the worker, then «＋ Срез» in the middle again
await post(`/api/runs/${r.id}/stop`);
await page.waitForTimeout(3000);
const m0 = await getj(`/api/runs/${r.id}`);
await setTL(Math.floor(max / 3)); await page.waitForTimeout(1500);
log(`suspended (${m0.state}), cursor at 1/3: ${JSON.stringify(await state())}`);
await page.click("text=＋ Срез"); await page.waitForTimeout(8000);
const m1 = await getj(`/api/runs/${r.id}`);
log(`8 s after «＋ Срез» on the suspended run: server state ${m1.state}, resumed ${m1.resumed}; ${JSON.stringify(await state())}`);
await post(`/api/runs/${r.id}/stop`);
fs.writeFileSync(`${OUT}/c07_planes_in_history.txt`, lines.join("\n") + "\n");
await browser.close();
