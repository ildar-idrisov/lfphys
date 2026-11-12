// Review B5, check c08b (browser): v15's brightness scale when the history cursor goes back (keyframe restore vs
// rebuild). Root and run as c08 (port 8520); output to <review>/out/c08b_browser.txt.
import { chromium } from "playwright";
const base = "http://127.0.0.1:8520";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const log = (...a) => console.log(...a);
const S = (page, f, a) => page.evaluate(f, a);
const status = (page) => S(page, () => { const s = document.querySelector(".imgwin .sw-status"); return s ? s.textContent : ""; });
const sample = (page, pts) => S(page, (pts) => {
  const w = document.querySelector(".imgwin").closest(".s3d-windows").__imagewin;
  const g = w.geometry(), cv = document.querySelector(".imgwin canvas"), ctx = cv.getContext("2d");
  const dpr = cv.width / cv.clientWidth;
  return pts.map(([i, j]) => { const x = Math.round((g.left + (i + 0.5) / g.W * g.pw) * dpr), y = Math.round((g.top + (j + 0.5) / g.H * g.ph) * dpr);
    return Array.from(ctx.getImageData(x, y, 1, 1).data.slice(0, 3)); });
}, pts);
const dataMax = (page, rows) => S(page, (rows) => {
  const f = document.querySelector(".imgwin").closest(".s3d-windows").__imagewin.current().fields;
  const W = 192, H = 192; let all = 0, upto = 0;
  for (let n = 0; n <= f.nmax; n++) for (let k = 0; k < W * H; k++) { const v = f.I[n * W * H + k]; if (v > all) all = v; if (Math.floor(k / W) < rows && v > upto) upto = v; }
  return { max_all_held: all, max_rows_shown: upto };
}, rows);
for (const [preset, frac, params] of [["m87", 0.12, {}], ["edge_on", 0.3, {}], ["ring", 0.5, {}]]) {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
  const r = await post("/api/runs", { viz: "v15_kerr_shadow", preset, params, seed: 3 });
  await page.goto(base + "/run?id=" + r.id); await page.waitForTimeout(4000);
  await post(`/api/runs/${r.id}/command`, { cmd: "speed", args: { value: 0.25 } });
  await post(`/api/runs/${r.id}/command`, { cmd: "play", args: {} });
  let rows = 0; const t0 = Date.now();
  while (Date.now() - t0 < 40000) { const m = (await status(page)).match(/считается: (\d+) из (\d+)/); if (m && Number(m[1]) >= frac * Number(m[2])) break; await page.waitForTimeout(30); }
  await post(`/api/runs/${r.id}/command`, { cmd: "pause", args: {} });
  await page.waitForTimeout(1500);
  rows = Number(((await status(page)).match(/считается: (\d+)/) || [0, 0])[1]);
  const n1 = await S(page, () => window.__lfPlayer.frames()), t1 = await S(page, () => window.__lfPlayer.t());
  const pts = []; for (let j = 1; j < rows - 1; j += 2) for (let i = 0; i < 192; i += 2) pts.push([i, j]);
  const live = await sample(page, pts), mlive = await dataMax(page, rows);
  await post(`/api/runs/${r.id}/command`, { cmd: "speed", args: { value: 1.0 } });
  await post(`/api/runs/${r.id}/command`, { cmd: "play", args: {} });
  const t2 = Date.now(); while (Date.now() - t2 < 30000) { if ((await status(page)).startsWith("готово")) break; await page.waitForTimeout(200); }
  await post(`/api/runs/${r.id}/command`, { cmd: "pause", args: {} });
  await page.waitForTimeout(1000);
  const dbg0 = await S(page, () => JSON.stringify(window.__lfPlayer.dbg));
  let idx = n1 - 1, tt;
  for (let k = 0; k < 60; k++) { await S(page, (i) => window.__lfPlayer.goTo(i), idx); await page.waitForTimeout(120); tt = await S(page, () => window.__lfPlayer.t()); if (Math.abs(tt - t1) < 1e-9) break; idx += tt < t1 ? 1 : -1; }
  await page.waitForTimeout(1500);
  const dbg1 = await S(page, () => JSON.stringify(window.__lfPlayer.dbg));
  const back = await sample(page, pts), mback = await dataMax(page, rows);
  let diff = 0, dim = 0; pts.forEach((_, k) => { const d = Math.max(...[0, 1, 2].map((c) => Math.abs(live[k][c] - back[k][c]))); if (d > 2) { diff++; if (back[k][0] + back[k][1] + back[k][2] < live[k][0] + live[k][1] + live[k][2]) dim++; } });
  log(`${preset}: paused at t=${t1} with ${rows} rows shown; back at t=${tt}, status «${await status(page)}»`);
  log(`   held data live ${JSON.stringify(mlive)}; after going back ${JSON.stringify(mback)}`);
  log(`   ${diff} of ${pts.length} sampled pixels drawn differently (${dim} dimmer); player dbg before ${dbg0} after ${dbg1}`);
  await page.locator(".imgwin").screenshot({ path: `rev15_shots/B2_${preset}_back.png` });
  await page.close();
}
await browser.close();
