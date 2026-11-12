// Review 2026-10-29, check k05: a negative control of the browser check. Two servers: the code as it is (port A) and
// the same code with v04's restore() not restoring its live values (port B, neg/v04_view_restore_without_liveVals.js
// mounted over v04_orbits/web/view.js). The author's check (dev_keyframes.mjs: play, pause, step back, no live change)
// cannot tell them apart; this scenario (a live change of the time units in the middle of the record, then a step back
// to before it) can.
//   node k05_live_change_control.mjs <portA> <portB>
import { writeFileSync } from "fs";
import { chromium } from "playwright";

const ports = [process.argv[2] || "8510", process.argv[3] || "8511"];
const out = [];
const log = (...a) => { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); out.push(s); console.log(s); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const settle = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 400)))));
const panels = (page) => page.evaluate(() => [...document.querySelectorAll(".panel")].map((p) => (p.innerText || "").replace(/\s+/g, " ")));
for (const port of ports) {
  const base = `http://127.0.0.1:${port}`;
  const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
  const r = await post("/api/runs", { viz: "v04_orbits", seed: 3 });
  await sleep(3000);
  await post(`/api/runs/${r.id}/command`, { cmd: "play" });
  await sleep(10000);
  await post(`/api/runs/${r.id}/command`, { cmd: "set", args: { values: { time_units: "geo" } } });
  await sleep(10000);
  await post(`/api/runs/${r.id}/command`, { cmd: "pause" });
  await sleep(1500);
  const page = await br.newPage({ viewport: { width: 1600, height: 1000 } });
  await page.goto(`${base}/run?id=${r.id}&key_every=5`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка записи/.test(document.querySelector("#status").textContent || ""), null, { timeout: 120000 });
  await settle(page);
  const nf = await page.evaluate(() => window.__lfPlayer.frames());
  const res = { port, run: r.id, frames: nf, steps: [] };
  for (const p of [0.2, 0.35]) {
    await page.evaluate((i) => window.__lfPlayer.goTo(i), Math.round(p * (nf - 1)));
    await settle(page);
    const how = await page.evaluate(() => ({ ...window.__lfPlayer.dbg }));
    const A = await panels(page);
    await page.evaluate(() => window.__lfPlayer.rebuildFromRecord());
    await settle(page);
    const B = await panels(page);
    const diff = A.map((x, k) => (x !== B[k] ? [x.slice(0, 160), B[k].slice(0, 160)] : null)).filter(Boolean);
    res.steps.push({ p, fromKey: how.fromKey, same: diff.length === 0, diff: diff.slice(0, 2) });
    await page.evaluate(() => window.__lfPlayer.goTo(1e9));
    await settle(page);
  }
  log(JSON.stringify(res));
  await page.close();
}
writeFileSync("out/k05_live_change_control.txt", out.join("\n") + "\n");
await br.close();
