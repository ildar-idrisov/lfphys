// A user's tour of one world's 3-D view: start a run (preset or params) on the PRIVATE server, open the page, look at
// it from the default camera, rotate, tilt over the pole, reset (F), zoom in and out, pan, every view button; measure
// the camera, the box on screen, the layers' materials, the render cost and the frame rate while rotating.
// usage: node tour.mjs <port> <viz> <preset|-> <tag> [playMs] [paramsJSON] [outDir]
import fs from "node:fs";
import { launch, startRun, openPage, shot, diag, drag, wheel, perf, fpsWhileRotating, clickView, settle, sleep } from "./lib.mjs";

const [port, viz, preset, tag, playMsS, paramsJ, outDirA] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;
const out = `${outDirA || "/pw/out"}/${tag}`;
fs.mkdirSync(out, { recursive: true });
const body = {};
if (preset && preset !== "-") body.preset = preset;
if (paramsJ && paramsJ !== "-") body.params = JSON.parse(paramsJ);
const res = { viz, preset, tag, steps: {} };
const errs = [];
const br = await launch();
try {
  const t0 = Date.now();
  const id = await startRun(base, viz, body);
  res.id = id;
  const page = await openPage(br, base, id, { errs, playMs: +(playMsS || 8000) });
  res.openSecs = (Date.now() - t0) / 1000;
  await sleep(1500); await settle(page);
  await shot(page, `${out}/page.jpg`, { full: true });
  res.steps.default = await diag(page);
  await shot(page, `${out}/0_default.jpg`);
  await drag(page, 300, 0); res.steps.rot = (await diag(page)).camera; await shot(page, `${out}/1_rot.jpg`);
  await drag(page, 0, -220); res.steps.tilt = (await diag(page)).camera; await shot(page, `${out}/2_tilt.jpg`);
  await drag(page, 0, 700); res.steps.pole = (await diag(page)).camera; await shot(page, `${out}/3_pole.jpg`);
  await page.keyboard.press("f"); await settle(page, 200);
  res.steps.reset = (await diag(page)).camera; await shot(page, `${out}/4_reset.jpg`);
  await wheel(page, -500, 5); res.steps.zin = (await diag(page)).camera; await shot(page, `${out}/5_zoomin.jpg`);
  await page.keyboard.press("f"); await settle(page, 200);
  await wheel(page, 600, 10); res.steps.zout = (await diag(page)); await shot(page, `${out}/6_zoomout.jpg`);
  await page.keyboard.press("f"); await settle(page, 200);
  await drag(page, 200, 120, { button: "right" }); res.steps.pan = (await diag(page)).camera; await shot(page, `${out}/7_pan.jpg`);
  await page.keyboard.press("f"); await settle(page, 200);
  for (const v of res.steps.default.viewDefs) {
    if (v === "iso") continue;
    await clickView(page, v); await settle(page, 200);
    res.steps["view_" + v] = (await diag(page)).boxOnScreen;
    await shot(page, `${out}/v_${v}.jpg`);
  }
  await page.keyboard.press("f"); await settle(page, 200);
  res.perf = await perf(page, 6);
  res.fps = await fpsWhileRotating(page, 4000);
  await shot(page, `${out}/9_after_fps.jpg`);
  res.errors = errs.slice(0, 8);
  await page.close();
} catch (e) { res.failed = String(e && e.stack || e).slice(0, 800); res.errors = errs.slice(0, 8); }
await br.close();
fs.writeFileSync(`${out}/tour.json`, JSON.stringify(res, null, 1));
console.log(JSON.stringify({ tag, id: res.id, failed: res.failed, errors: res.errors, perf: res.perf, fps: res.fps, openSecs: res.openSecs }));
