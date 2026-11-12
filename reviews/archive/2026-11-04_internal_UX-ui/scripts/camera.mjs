// U-scroll (the view): the owner zooms the scene with the mouse wheel while the world records; is the zoom kept?
// 3-D worlds: the screen distance between two physics points (scene3d.screenOf) is the zoom; sampled every second
// for 75 s (a playground's record segment is 60 s: its start re-emits the latest "box"). setBox calls are counted
// (wrapped on the scene's api object, which env3d calls). 2-D worlds (v04): Plane.prototype.fit calls are counted
// (canvas.js imported once more in the page: the same module instance) after a wheel zoom, a live change and a
// timeline scrub. Usage: node camera.mjs [case ...]
import { base, browser, newRun, play, sleep, shot, post } from "./common.mjs";
import fs from "fs";

async function open(b, id, w = 1600, h = 1000) {
  const ctx = await b.newContext({ viewport: { width: w, height: h } });
  const page = await ctx.newPage();
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка/.test(document.getElementById("status").textContent), null, { timeout: 120000 });
  return { page, ctx };
}

async function zoom3d(page) {
  return page.evaluate(() => {
    const api = document.querySelector(".s3d-view").__scene3d;
    const B = api.state.box, c = [(B[0][0] + B[1][0]) / 2, (B[0][1] + B[1][1]) / 2, (B[0][2] + B[1][2]) / 2];
    const a = api.screenOf([0, 0, 0]), q = api.screenOf([1, 0, 0]);
    return { px_per_unit: Math.hypot(q[0] - a[0], q[1] - a[1]), origin: a.map(Math.round), box: JSON.stringify(B), setBox: window.__setBox || 0 };
  });
}

async function case3d(b, name, viz, body, secs = 75, speed = null) {
  const id = await newRun(viz, body);
  const { page, ctx } = await open(b, id);
  await page.evaluate(() => {
    const api = document.querySelector(".s3d-view").__scene3d;
    const orig = api.setBox; window.__setBox = 0;
    api.setBox = (bx) => { window.__setBox++; return orig(bx); };
  });
  if (speed) await post(`/api/runs/${id}/command`, { cmd: "speed", args: { value: speed } });
  await play(page);
  await sleep(3000);
  const r0 = await zoom3d(page);
  // the owner zooms in on the middle of the scene
  const v = await page.$eval(".s3d-view", (e) => { const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; });
  await page.mouse.move(v.x, v.y);
  for (let i = 0; i < 6; i++) { await page.mouse.wheel(0, -240); await sleep(80); }
  await sleep(600);
  const r1 = await zoom3d(page);
  await shot(page, `/pw/shots/camera_${name}_zoomed.jpg`);
  const series = [];
  let shotDone = false;
  for (let s = 0; s < secs; s++) {
    await sleep(1000);
    const z = await zoom3d(page);
    series.push({ s, z: +z.px_per_unit.toFixed(1), setBox: z.setBox });
    if (!shotDone && Math.abs(z.px_per_unit - r1.px_per_unit) > 0.2 * r1.px_per_unit) { await shot(page, `/pw/shots/camera_${name}_reset.jpg`); shotDone = true; }
  }
  const out = { case: name, before_zoom: r0, after_zoom: r1, series: series.map((x) => `${x.s}:${x.z}/${x.setBox}`).join(" "),
                reset_at_s: (series.find((x) => Math.abs(x.z - r1.px_per_unit) > 0.2 * r1.px_per_unit) || {}).s ?? null };
  await ctx.close();
  await post(`/api/runs/${id}/stop`, {});
  return out;
}

async function v04(b) {
  const id = await newRun("v04_orbits", { preset: "default" });
  const { page, ctx } = await open(b, id);
  await page.evaluate(async () => {
    const m = await import("/static/js/canvas.js");
    window.__fit = []; const f = m.Plane.prototype.fit;
    m.Plane.prototype.fit = function (...a) { window.__fit.push({ t: performance.now(), stack: new Error().stack.split("\n").slice(2, 5).join(" | ") }); return f.apply(this, a); };
  });
  await play(page);
  await sleep(4000);
  const cv = await page.$eval(".center canvas", (e) => { const r = e.getBoundingClientRect(); return { x: r.left + r.width * 0.6, y: r.top + r.height * 0.4 }; });
  await page.mouse.move(cv.x, cv.y);
  for (let i = 0; i < 5; i++) { await page.mouse.wheel(0, -300); await sleep(80); }
  await sleep(500);
  await shot(page, "/pw/shots/camera_v04_zoomed.jpg");
  const steps = [];
  const nFit = () => page.evaluate(() => window.__fit.length);
  steps.push({ step: "zoomed, 8 s of recording", fit_before: await nFit() });
  await sleep(8000);
  steps[steps.length - 1].fit_after = await nFit();
  // a scrub back along the timeline (key frame restore), then back to the end
  steps.push({ step: "timeline scrub back and to the end", fit_before: await nFit() });
  await page.evaluate(() => window.__lfPlayer.goTo(Math.floor(window.__lfPlayer.frames() / 2)));
  await sleep(800);
  await page.evaluate(() => window.__lfPlayer.goTo(window.__lfPlayer.frames() - 1));
  await sleep(800);
  steps[steps.length - 1].fit_after = await nFit();
  await shot(page, "/pw/shots/camera_v04_after_scrub.jpg");
  // a live change (the world starts a new segment)
  steps.push({ step: "live change ghost on", fit_before: await nFit() });
  await post(`/api/runs/${id}/command`, { cmd: "set", args: { values: { ghost: true } } });
  await sleep(3000);
  steps[steps.length - 1].fit_after = await nFit();
  const stacks = await page.evaluate(() => [...new Set(window.__fit.map((x) => x.stack))]);
  await ctx.close();
  await post(`/api/runs/${id}/stop`, {});
  return { case: "v04_2d", steps, fit_stacks: stacks };
}

const b = await browser();
fs.mkdirSync("/pw/shots", { recursive: true });
const want = process.argv.slice(2);
const ALL = {
  p01_inner: () => case3d(b, "p01_inner", "p01_gravity", { preset: "inner" }),
  p01_hole: () => case3d(b, "p01_hole", "p01_gravity", { preset: "hole_stars" }),
  v09_lab: () => case3d(b, "v09_lab", "v09_thomas_3d", { preset: "lab", params: { ngrid: 48 } }, 40),
  p03_maxwell: () => case3d(b, "p03_maxwell", "p03_molecules", { preset: "maxwell" }, 75),
  v04: () => v04(b),
};
for (const k of (want.length ? want : Object.keys(ALL))) {
  try { const r = await ALL[k](); console.log(JSON.stringify(r)); fs.appendFileSync("/pw/out_camera.jsonl", JSON.stringify(r) + "\n"); }
  catch (e) { console.log(JSON.stringify({ case: k, error: String(e).slice(0, 600) })); }
}
await b.close();
