// Repeated timing of a full frame before ("orig") or after ("new") the processing: 9 timings of 5 frames each (the GPU
// waited for), median and min — for a world whose single-sample tour looked slower (v10). usage:
// node timing_ab.mjs <port> <orig|new> <viz> <preset> [playMs]
import { launch, startRun, openPage, settle, sleep } from "./lib.mjs";
const [port, variant, viz, preset, playMs] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;
const br = await launch(); const errs = [];
const id = await startRun(base, viz, { preset });
const page = await openPage(br, base, id, { errs, playMs: +(playMs || 6000), variant });
await fetch(`${base}/api/runs/${id}/command`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cmd: "pause" }) });
await sleep(1500); await settle(page);
const r = await page.evaluate(async () => {
  const a = document.querySelector(".s3d-view").__scene3d, R = a.__renderer, gl = R.getContext();
  const once = () => { const t0 = performance.now(); for (let i = 0; i < 5; i++) a.render(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); return (performance.now() - t0) / 5; };
  for (let i = 0; i < 3; i++) once();
  const xs = []; for (let i = 0; i < 9; i++) { xs.push(once()); await new Promise((r) => setTimeout(r, 50)); }
  xs.sort((p, q) => p - q);
  return { median: +xs[4].toFixed(1), min: +xs[0].toFixed(1), all: xs.map((x) => +x.toFixed(1)) };
});
console.log(JSON.stringify({ variant, viz, preset, ...r, errs: errs.slice(0, 3) }));
await br.close();
