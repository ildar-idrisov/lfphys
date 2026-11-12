// The review's user tour (scripts/tour.mjs, copied and changed for its processing): the same steps, run with the code
// before the processing ("orig") or after it ("new") in the same environment. Steps: default view, rotate, tilt, over
// the pole, F, zoom in, F, zoom out, pan, every view button; the render's cost and the frame rate while rotating.
// usage: node tour_ab.mjs <port> <orig|new> <viz> <preset|-> <tag> [playMs] [paramsJSON|-] [outDir]
import fs from "node:fs";
import { launch, startRun, openPage, shot, diag, drag, wheel, perf, fpsWhileRotating, clickView, settle, sleep } from "./lib.mjs";

const [port, variant, viz, preset, tag, playMsS, paramsJ, outDirA] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;
const out = `${outDirA || "/pw/out"}/${tag}_${variant}`;
fs.mkdirSync(out, { recursive: true });
const body = {};
if (preset && preset !== "-") body.preset = preset;
if (paramsJ && paramsJ !== "-") body.params = JSON.parse(paramsJ);
const res = { viz, preset, tag, variant, steps: {} };
const errs = [];
const br = await launch();
try {
  const id = await startRun(base, viz, body);
  res.id = id;
  const page = await openPage(br, base, id, { errs, playMs: +(playMsS || 8000), variant });
  await sleep(1500); await settle(page);
  // the run paused: both variants are compared on the same state of the world
  await fetch(`${base}/api/runs/${id}/command`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cmd: "pause" }) });
  await sleep(800); await settle(page);
  res.steps.default = await diag(page);
  await shot(page, `${out}/0_default.jpg`);
  await drag(page, 300, 0); res.steps.rot = (await diag(page)).camera; await shot(page, `${out}/1_rot.jpg`);
  await drag(page, 0, -220); res.steps.tilt = (await diag(page)).camera; await shot(page, `${out}/2_tilt.jpg`);
  await page.keyboard.press("f"); await settle(page, 300);
  res.steps.reset = await diag(page); await shot(page, `${out}/4_F.jpg`);
  await wheel(page, -500, 5); res.steps.zin = (await diag(page)).camera; await shot(page, `${out}/5_zoomin.jpg`);
  await page.keyboard.press("f"); await settle(page, 300);
  await wheel(page, 600, 10); res.steps.zout = await diag(page); await shot(page, `${out}/6_zoomout.jpg`);
  await clickView(page, "iso"); await settle(page, 300);
  for (const v of res.steps.default.viewDefs) {
    if (v === "iso") continue;
    await clickView(page, v); await settle(page, 300);
    res.steps["view_" + v] = (await diag(page)).boxOnScreen;
    await shot(page, `${out}/v_${v}.jpg`);
  }
  await clickView(page, "iso"); await settle(page, 300);
  res.perf = await perf(page, 6);
  res.fps = await fpsWhileRotating(page, 4000);
  await shot(page, `${out}/9_after_fps.jpg`);
  res.errors = errs.slice(0, 8);
  await page.close();
} catch (e) { res.failed = String(e && e.stack || e).slice(0, 800); res.errors = errs.slice(0, 8); }
await br.close();
fs.writeFileSync(`${out}/tour.json`, JSON.stringify(res, null, 1));
const d = res.steps.default || {};
console.log(JSON.stringify({ tag, variant, id: res.id, failed: res.failed, errors: res.errors, corners: d.cornersInside, canvas: d.canvas, perf: res.perf, fps: res.fps }));
