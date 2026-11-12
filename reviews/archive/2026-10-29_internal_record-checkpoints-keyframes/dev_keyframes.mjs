// A verbatim copy of the browser check the author used (scratchpad pw/keyframes.mjs), kept here to run it as a negative control (k05); only this line and the output path changed.
// Key frames of the player (owner 2026-10-29): for every visualization, the view brought back to a cursor through a key
// frame must equal the view rebuilt from the record at the same cursor. Private server (port from argv), CPU.
import { chromium } from "playwright";
import { writeFileSync } from "fs";
const port = process.argv[2] || "8507";
const only = process.argv[3] ? process.argv[3].split(",") : null;
const base = `http://127.0.0.1:${port}`;
const SMALL = {
  v08_wave_3d: { n: 128, zmax: 10.0 },
  v09_thomas_3d: { ngrid: 48 },
  v11_double_slit_2d: { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 100, n_tracks: 10 },
  v12_arrival_times_2d: { grid: "coarse", n_bohm: 100, n_tracks: 10, L: 12.0, sigma_z: 2.0, sigma_x: 2.0 },
};
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const out = [], errs = [];
const log = (...a) => { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); out.push(s); console.log(s); };
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const ids = (await (await fetch(base + "/api/viz")).json()).map((v) => v.id).filter((id) => !only || only.includes(id));

async function fingerprint(page) {
  const { createHash } = await import("crypto");
  const parts = [];
  // the 2-D canvases as the viewer sees them (element screenshots; the WebGL scene is compared by its state below)
  const handles = await page.$$("canvas");
  for (const hdl of handles) {
    const skip = await hdl.evaluate((c) => !!(c.closest(".s3d-view") && !c.closest(".s3d-win")) || !c.offsetParent || !c.width);
    if (skip) continue;
    try { parts.push("c" + createHash("sha1").update(await hdl.screenshot()).digest("hex").slice(0, 12)); } catch (e) { /* off-screen */ }
  }
  const rest = await page.evaluate(() => {
    const h = (str) => { let x = 2166136261; for (let i = 0; i < str.length; i++) { x ^= str.charCodeAt(i); x = Math.imul(x, 16777619) >>> 0; } return x; };
    const parts = [];
    const sc = document.querySelector(".s3d-view");
    if (sc && sc.__scene3d) {
      const S = sc.__scene3d.state;
      for (const L of [...S.layers.values()].sort((a, b) => (a.id < b.id ? -1 : 1))) {
        let acc = 0, n = 0;
        L.obj.traverse((o) => {
          if (!o.geometry) return;
          const g = o.geometry, cnt = Number.isFinite(g.drawRange.count) ? g.drawRange.count : Infinity;
          for (const name of ["position", "color"]) {
            const a = g.attributes[name]; if (!a) continue;
            const m = Math.min(a.array.length, cnt === Infinity ? a.array.length : cnt * a.itemSize);
            for (let i = 0; i < m; i++) { const v = a.array[i]; if (Number.isFinite(v)) acc += v * ((i % 97) + 1); }
            n += m;
          }
        });
        parts.push(`L${L.id}:${L.visible ? 1 : 0}:${n}:${acc.toPrecision(10)}`);
      }
      parts.push(`P${[...S.planes.keys()].sort().join(",")}`);
    }
    for (const p of document.querySelectorAll(".panel")) parts.push(`T${h(p.innerText)}`);
    return parts;
  });
  return parts.concat(rest);
}
const settle = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 400)))));

for (const viz of ids) {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  page.on("pageerror", (e) => errs.push(`${viz} pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`${viz} console: ${m.text()}`.slice(0, 400)); });
  try {
    const r = await post("/api/runs", SMALL[viz] ? { viz, params: SMALL[viz], seed: 3 } : { viz, seed: 3 });
    await page.goto(`${base}/run?id=${r.id}&key_every=5`);
    await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
    await post(`/api/runs/${r.id}/command`, { cmd: "play" });
    const t0 = Date.now();
    await page.waitForTimeout(25000);
    await post(`/api/runs/${r.id}/command`, { cmd: "pause" });
    await page.waitForTimeout(1500);
    const nf = await page.evaluate(() => window.__lfPlayer.frames());
    const keys = await page.evaluate(() => window.__lfPlayer.keys());
    const res = { viz, frames: nf, keys, steps: [] };
    for (const p of [0.85, 0.5, 0.15, 0.65, 0.3]) {
      const i = Math.round(p * (nf - 1));
      const before = await page.evaluate(() => ({ ...window.__lfPlayer.dbg }));
      await page.evaluate((i) => window.__lfPlayer.goTo(i), i);
      await settle(page);
      const after = await page.evaluate(() => ({ ...window.__lfPlayer.dbg }));
      const A = await fingerprint(page);
      await page.evaluate(() => window.__lfPlayer.rebuildFromRecord());
      await settle(page);
      const fullMs = await page.evaluate(() => window.__lfPlayer.dbg.lastMs);
      const fullFed = await page.evaluate(() => window.__lfPlayer.dbg.lastFed);
      const B = await fingerprint(page);
      const diff = A.filter((x, k) => x !== B[k]).length + Math.abs(A.length - B.length);
      res.steps.push({ p, how: after.fromKey > before.fromKey ? "key" : after.full > before.full ? "full" : "feed",
                       keyFailed: after.keyFailed - before.keyFailed, ms: +after.lastMs.toFixed(1), fed: after.lastFed,
                       fullMs: +fullMs.toFixed(1), fullFed, same: diff === 0, ndiff: diff,
                       diffs: diff ? A.map((x, k) => (x !== B[k] ? [x, B[k]] : null)).filter(Boolean).slice(0, 3) : undefined });
    }
    log(JSON.stringify(res));
  } catch (e) { log(`${viz} FAILED: ${e.message}`); }
  await page.close();
}
log("errors:", JSON.stringify(errs.slice(0, 30)));
writeFileSync(`out/dev_keyframes_out_${port}.txt`, out.join("\n") + "\n");
await browser.close();
