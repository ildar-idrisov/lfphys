// C1 review, check 10: how the cost of going back grows with the record. After 15, 45 and 90 s of recording, the
// latency of ONE step back (the view rebuilt from the record when a message lies between the two frames) against one
// step forward (the view fed one frame), each measured from the timeline's input event to the second animation frame
// after it (median of 5), at 25 %, 50 % and 90 % of the history (version 1 measured at the end only, where a finished
// experiment has no messages between its last frames: out/c10_rebuild_cost_at_end.txt).
// Own server 127.0.0.1:8502 only; SwiftShader (absolute times are pessimistic for WebGL, the 2-D canvases are not).
// Output: out/c10_rebuild_cost.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8502";
const OUT = process.env.OUT || "/pw/c1rev_out";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
const SMALL = { v12_arrival_times_2d: { grid: "coarse", n_bohm: 300, n_tracks: 40, L: 40.0, sigma_z: 2.0, sigma_x: 2.0 } };
const VIZ = (process.env.VIZ || "v02_double_slit,v04_orbits,v09_thomas_3d,v12_arrival_times_2d").split(",");
const lat = (page, i) => page.evaluate((i) => new Promise((res) => {
  const t = document.getElementById("timeline"), t0 = performance.now();
  t.value = String(i); t.dispatchEvent(new Event("input"));
  requestAnimationFrame(() => requestAnimationFrame(() => res(performance.now() - t0)));
}), i);
const med = (a) => a.slice().sort((x, y) => x - y)[Math.floor(a.length / 2)];
for (const viz of VIZ) {
  const page = await browser.newPage({ viewport: { width: 1500, height: 900 } });
  const r = await post("/api/runs", { viz, params: SMALL[viz] || {}, seed: 8 });
  await page.goto(base + "/run?id=" + r.id);
  await page.waitForTimeout(4000);
  let recorded = 0;
  for (const upto of [15, 45, 90]) {
    await page.click("#rec"); await page.waitForTimeout((upto - recorded) * 1000); await page.click("#rec");
    recorded = upto;
    await page.waitForTimeout(2000);
    const max = await page.evaluate(() => +document.getElementById("timeline").max);
    const nmsg = (await (await fetch(`${base}/api/runs/${r.id}`)).json()).n_messages;
    const parts = [];
    for (const f of [0.25, 0.5, 0.9]) {
      const i = Math.max(1, Math.round(f * max));
      const back = [], fwd = [];
      for (let k = 0; k < 5; k++) {
        await lat(page, i); await page.waitForTimeout(300);
        back.push(await lat(page, i - 1)); await page.waitForTimeout(300);
        fwd.push(await lat(page, i)); await page.waitForTimeout(300);
      }
      parts.push(`at ${Math.round(100 * f)} %: back ${med(back).toFixed(0)} ms / forward ${med(fwd).toFixed(0)} ms`);
    }
    log(`${viz} after ${upto} s of recording (${max + 1} frames, ${nmsg} messages): one step ${parts.join("; ")}`);
  }
  await post(`/api/runs/${r.id}/stop`);
  await page.close();
}
fs.writeFileSync(`${OUT}/c10_rebuild_cost.txt`, lines.join("\n") + "\n");
await browser.close();
