// The render's cost before ("orig") and after ("new") the processing, in one environment: the world paused at the same
// moment, its default view; "msPerRender" = a full-quality frame (N frames drawn one after another, the GPU waited
// for); "rotate" = 4 s of the mouse turning the view: the page's animation frames and the scene's frames per second,
// and the main thread's script share (CDP); "play" (optional) = 6 s of the world playing with the view still: the
// script share (A17: v13's superposition repaints its cloud every phase). Software GL: compare ratios only.
// usage: node perf_ab.mjs <port> <orig|new> <viz> <preset|-> <tag> [playMs] [play] [outDir]
import fs from "node:fs";
import { launch, startRun, openPage, perf, fpsWhileRotating, settle, sleep, shot, diag } from "./lib.mjs";
const [port, variant, viz, preset, tag, playMsS, playS, outDirA] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;
const out = `${outDirA || "/pw/out"}/perf_${tag}_${variant}`;
fs.mkdirSync(out, { recursive: true });
const body = {}; if (preset && preset !== "-") body.preset = preset;
const cmd = (id, c) => fetch(`${base}/api/runs/${id}/command`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cmd: c }) });
const errs = [], res = { viz, preset, tag, variant };
const br = await launch();
try {
  const id = await startRun(base, viz, body);
  const page = await openPage(br, base, id, { errs, playMs: +(playMsS || 6000), variant });
  if (playS === "play") {
    const cdp = await page.context().newCDPSession(page);
    await cdp.send("Performance.enable");
    const m0 = Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]));
    const t0 = Date.now(); await sleep(6000);
    const m1 = Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]));
    const secs = (Date.now() - t0) / 1000;
    res.play = { secs, scriptShare: +((m1.ScriptDuration - m0.ScriptDuration) / secs).toFixed(3), taskShare: +((m1.TaskDuration - m0.TaskDuration) / secs).toFixed(3) };
    await cdp.detach();
  }
  await cmd(id, "pause"); await sleep(1000); await settle(page);
  res.canvas = (await diag(page)).canvas;
  await shot(page, `${out}/view.jpg`);
  res.perf = await perf(page, 6);
  res.rotate = await fpsWhileRotating(page, 4000);
  await page.close();
} catch (e) { res.failed = String(e && e.stack || e).slice(0, 600); }
res.errors = errs.slice(0, 6);
await br.close();
fs.writeFileSync(`${out}/perf.json`, JSON.stringify(res, null, 1));
console.log(JSON.stringify(res));
