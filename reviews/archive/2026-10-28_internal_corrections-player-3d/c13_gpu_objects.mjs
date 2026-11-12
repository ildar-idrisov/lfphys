// C1 review, check 13: GPU objects alive (scene3d.gpuInfo(), three.js renderer.info.memory) across repeated rebuilds
// of the 3-D scene (the cursor toggled between the end and the middle: every return to the middle rebuilds the view
// from the record). A count that grows with the number of rebuilds is a leak.
// Own server 127.0.0.1:8502. Output: out/c13_gpu_objects.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8502";
const OUT = process.env.OUT || "/pw/c1rev_out";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
const SMALL = { v09_thomas_3d: { ngrid: 48 }, v11_double_slit_2d: { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 200, n_tracks: 20 } };
const VIZ = (process.env.VIZ || "v10_fast_observer,v09_thomas_3d,v13_hydrogen_3d,v11_double_slit_2d").split(",");
const setTL = (page, i) => page.evaluate((i) => { const t = document.getElementById("timeline"); t.value = String(i); t.dispatchEvent(new Event("input")); }, i);
const gpu = (page) => page.evaluate(() => document.querySelector(".s3d-view").__scene3d.gpuInfo());
for (const viz of VIZ) {
  const page = await browser.newPage({ viewport: { width: 1500, height: 900 } });
  const r = await post("/api/runs", { viz, params: SMALL[viz] || {}, seed: 3 });
  await page.goto(base + "/run?id=" + r.id);
  await page.waitForTimeout(4000);
  await page.click("#rec"); await page.waitForTimeout(15000); await page.click("#rec"); await page.waitForTimeout(2000);
  const max = await page.evaluate(() => +document.getElementById("timeline").max);
  const samples = [];
  for (let k = 0; k <= 40; k++) {
    if (k % 10 === 0) samples.push(`${k}: ${JSON.stringify(await gpu(page))}`);
    await setTL(page, max); await page.waitForTimeout(250);
    await setTL(page, Math.floor(max / 2)); await page.waitForTimeout(250);
  }
  log(`${viz} (${max + 1} frames), rebuilds → GPU objects: ${samples.join("  ")}`);
  await post(`/api/runs/${r.id}/stop`);
  await page.close();
}
fs.writeFileSync(`${OUT}/c13_gpu_objects.txt`, lines.join("\n") + "\n");
await browser.close();
