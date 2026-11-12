// Review 2026-10-29, check k04: the memory the key frames take. scene3d.snapshotAppends copies, for every key frame, the
// colours of ALL track segments drawn so far (T.col.slice(0, 6 * segs): 24 bytes per segment), so the key frames of a
// view with tracks (v11, v12) take a sum over keys of the segments drawn by then — quadratic in the record's length up
// to the cap. Measured as the JS heap of the same record opened with key frames (default ?key_every, 100) and without
// (?key_every=1e9), after a forced GC, with the size the copies imply.
import { writeFileSync } from "fs";
import { browser, dbg, open, post, scene, settle, sleep, waitRun } from "./k_common.mjs";

const viz = process.argv[3] || "v11_double_slit_2d";
const secs = Number(process.argv[4] || 120);
const params = process.argv[5] ? JSON.parse(process.argv[5]) : {};
const out = [], errs = [];
const log = (...a) => { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); out.push(s); console.log(s); };
const br = await browser();
const r = await post("/api/runs", { viz, params, seed: 3 });
log("run", r.id, viz, JSON.stringify(params));
await waitRun(r.id, (m) => m.state === "running", 600000);
await post(`/api/runs/${r.id}/command`, { cmd: "speed", args: { value: 1e9 } });
await post(`/api/runs/${r.id}/command`, { cmd: "play" });
await sleep(secs * 1000);
await post(`/api/runs/${r.id}/command`, { cmd: "pause" });
await sleep(2000);
for (const ke of [1e9, 100]) {
  const page = await open(br, r.id, ke, errs);
  await settle(page);
  const heap = await page.evaluate(() => { if (window.gc) { window.gc(); window.gc(); } return performance.memory ? performance.memory.usedJSHeapSize : null; });
  const s = await scene(page), d = await dbg(page);
  const segs = await page.evaluate(() => { const S = document.querySelector(".s3d-view").__scene3d.state; const T = S.tracks.get("bohm"); return T ? T.segs : null; });
  log(JSON.stringify({ key_every: ke, heap_MB: heap && +(heap / 2 ** 20).toFixed(1), keys: d.keys, frames: d.frames, segs_at_end: segs,
                       last_rebuild_ms: +d.lastMs.toFixed(1) }));
  // a step back to the middle: through a key frame (key_every 100) or by a rebuild (1e9)
  await page.evaluate((i) => window.__lfPlayer.goTo(i), Math.round(0.5 * (d.frames - 1)));
  await settle(page);
  const d2 = await dbg(page);
  log(JSON.stringify({ key_every: ke, step_back_to_middle: { fromKey: d2.fromKey, full: d2.full, ms: +d2.lastMs.toFixed(1), fed: d2.lastFed } }));
  await page.close();
}
log("errors", errs.slice(0, 10));
writeFileSync(`out/k04_key_memory_${viz}.txt`, out.join("\n") + "\n");
await br.close();
