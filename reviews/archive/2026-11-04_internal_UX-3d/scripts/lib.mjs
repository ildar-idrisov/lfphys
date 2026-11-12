// UX-3d audit helpers (review 2026-11-04_internal_UX-3d). Drives the player like a user: mouse drags, wheel, buttons.
// For MEASUREMENT ONLY the served scene3d.js is patched in the browser (page.route) to expose its camera, orbit
// controls and renderer on the scene's api; nothing in the engine is changed.
import { chromium } from "playwright";
import fs from "node:fs";

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
export function mk(base) {
  const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
  const get = async (u) => (await fetch(base + u)).json();
  return { post, get };
}

export async function launch() {
  return chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
}

export async function startRun(base, viz, body = {}, { playMs = 8000, speed = null, keepPlaying = true } = {}) {
  const { post, get } = mk(base);
  let r = null;
  for (let k = 0; k < 180; k++) {  // all workers busy with viewed runs: wait for one (another tour's page closes)
    r = await post("/api/runs", { viz, seed: 3, ...body });
    if (r.id || !/вычислител/.test(r.error || "")) break;
    await sleep(5000);
  }
  if (!r.id) throw new Error("run not started: " + JSON.stringify(r).slice(0, 400));
  const id = r.id;
  const t0 = Date.now();
  for (;;) {
    const m = await get(`/api/runs/${id}`);
    if (m.state === "running") break;
    // suspended by another run's start before it had a viewer: a "play" command resumes it (it makes room by
    // suspending a run without viewers)
    if (m.state === "suspended") await post(`/api/runs/${id}/command`, { cmd: "play" });
    if (m.state === "failed" || m.state === "error") throw new Error("run failed: " + JSON.stringify(m).slice(0, 400));
    if (Date.now() - t0 > 300000) throw new Error("timeout starting " + viz);
    await sleep(500);
  }
  if (speed) await post(`/api/runs/${id}/command`, { cmd: "speed", args: { value: speed } });
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  // the page is opened at once (a run with a viewer is never suspended to make room for another run); the caller
  // waits playMs with the page open
  return id;
}

export async function openPage(br, base, id, { width = 1600, height = 1000, errs = [], playMs = 0 } = {}) {
  const page = await br.newPage({ viewport: { width, height } });
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`console: ${m.text()}`.slice(0, 300)); });
  await page.route("**/static/js/scene3d.js", async (route) => {
    const resp = await route.fetch();
    let body = await resp.text();
    body = body.replace("root.__scene3d = api;", "api.__camera = camera; api.__orbit = orbit; api.__renderer = renderer; api.__three = scene; api.__gizmo = gizmo; root.__scene3d = api;");
    await route.fulfill({ response: resp, body });
  });
  await page.goto(`${base}/run?id=${id}`);
  { const { post, get } = mk(base);  // the same race once more, now with a viewer attached
    for (let k = 0; k < 10; k++) { const m = await get(`/api/runs/${id}`); if (m.state !== "suspended") break; await post(`/api/runs/${id}/command`, { cmd: "play" }); await sleep(2000); } }
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && document.querySelector(".s3d-view") && document.querySelector(".s3d-view").__scene3d
    && !/загрузка записи/.test((document.querySelector("#status") || {}).textContent || ""), null, { timeout: 240000 });
  if (playMs) await sleep(playMs);
  await settle(page);
  return page;
}

export const settle = (page, ms = 500) => page.evaluate((ms) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, ms)))), ms);

export async function canvasRect(page) {
  return page.evaluate(() => { const r = document.querySelector(".s3d-view canvas").getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; });
}

export async function drag(page, dx, dy, { button = "left", steps = 8, modifiers = [], at = null } = {}) {
  const r = await canvasRect(page);
  const x0 = at ? r.x + at[0] * r.w : r.x + r.w / 2, y0 = at ? r.y + at[1] * r.h : r.y + r.h / 2;
  for (const m of modifiers) await page.keyboard.down(m);
  await page.mouse.move(x0, y0);
  await page.mouse.down({ button });
  for (let i = 1; i <= steps; i++) await page.mouse.move(x0 + dx * i / steps, y0 + dy * i / steps);
  await page.mouse.up({ button });
  for (const m of modifiers) await page.keyboard.up(m);
  await settle(page, 200);
}

export async function wheel(page, dy, n = 1, { at = null } = {}) {
  const r = await canvasRect(page);
  const x0 = at ? r.x + at[0] * r.w : r.x + r.w / 2, y0 = at ? r.y + at[1] * r.h : r.y + r.h / 2;
  await page.mouse.move(x0, y0);
  for (let i = 0; i < n; i++) { await page.mouse.wheel(0, dy); await sleep(30); }
  await settle(page, 200);
}

export async function shot(page, path, { full = false, quality = 72 } = {}) {
  // a clip of the page (no element-stability wait: a slow software render must not time the shot out)
  const clip = full ? undefined : await page.evaluate(() => { const r = document.querySelector(".s3d-view").getBoundingClientRect(); return { x: r.left, y: r.top, width: r.width, height: r.height }; });
  await page.screenshot({ path, type: "jpeg", quality, clip, timeout: 180000 });
  const kb = fs.statSync(path).size / 1024;
  if (kb > 290) await page.screenshot({ path, type: "jpeg", quality: 50, clip, timeout: 180000 });
  return path;
}

// what the scene is made of, how it is drawn, where the camera is, and how much of the box is on screen
export async function diag(page) {
  return page.evaluate(() => {
    const api = document.querySelector(".s3d-view").__scene3d, S = api.state, cam = api.__camera, orbit = api.__orbit;
    const cv = document.querySelector(".s3d-view canvas").getBoundingClientRect();
    const mats = (o) => (Array.isArray(o.material) ? o.material : o.material ? [o.material] : []);
    const layers = [...S.layers.values()].map((L) => {
      const parts = {};
      L.obj.traverse((o) => {
        if (!o.isMesh && !o.isLine && !o.isPoints && !o.isSprite) return;
        for (const m of mats(o)) {
          const k = `${o.type}/${m.type}${m.transparent ? "/transp" : ""}${m.depthWrite ? "" : "/noDW"}${m.depthTest ? "" : "/noDT"}${o.renderOrder ? "/ro" + o.renderOrder : ""}${m.side === 1 ? "/back" : m.side === 2 ? "/double" : ""}${m.opacity < 1 ? "/op" + m.opacity.toFixed(2) : ""}`;
          parts[k] = (parts[k] || 0) + (o.isInstancedMesh ? o.count : 1);
        }
      });
      return { id: L.id, label: L.label, kind: L.kind, visible: L.visible, parts };
    });
    const [lo, hi] = S.box || [[0, 0, 0], [1, 1, 1]];
    const corners = [];
    for (const x of [lo[0], hi[0]]) for (const y of [lo[1], hi[1]]) for (const z of [lo[2], hi[2]]) corners.push(api.screenOf([x, y, z]));
    const inside = corners.filter(([x, y]) => x >= cv.left && x <= cv.right && y >= cv.top && y <= cv.bottom).length;
    const xs = corners.map((c) => c[0]), ys = corners.map((c) => c[1]);
    const proj = { x0: Math.min(...xs) - cv.left, x1: Math.max(...xs) - cv.left, y0: Math.min(...ys) - cv.top, y1: Math.max(...ys) - cv.top };
    const centre = api.screenOf([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2]);
    return {
      box: S.box, size: S.size, canvas: { w: cv.width, h: cv.height }, cornersInside: inside, boxOnScreen: proj,
      centreOnScreen: [centre[0] - cv.left, centre[1] - cv.top],
      camera: { pos: cam.position.toArray().map((v) => +v.toPrecision(5)), up: cam.up.toArray(), near: +cam.near.toPrecision(4), far: +cam.far.toPrecision(4), fov: cam.fov,
                dist: +cam.position.distanceTo(orbit.target).toPrecision(5), target: orbit.target.toArray().map((v) => +v.toPrecision(5)),
                zoomToCursor: orbit.zoomToCursor, enableDamping: orbit.enableDamping, minDistance: orbit.minDistance, maxDistance: orbit.maxDistance },
      lastView: S.lastView, viewDefs: (S.viewDefs || []).map((v) => v[0]),
      layers, planes: [...S.planes.values()].map((P) => ({ id: P.id, visible: P.visible, hasData: !!P.data, label: (P.meta || {}).label })),
    };
  });
}

// the render's cost: draw calls, triangles, lines, points of one frame, and the time of N renders (software GL: only
// relative numbers mean anything)
export async function perf(page, n = 10) {
  return page.evaluate((n) => {
    const api = document.querySelector(".s3d-view").__scene3d, R = api.__renderer;
    R.info.autoReset = true;
    api.render();
    const gl = R.getContext(); gl.finish();
    const info = { calls: R.info.render.calls, triangles: R.info.render.triangles, lines: R.info.render.lines, points: R.info.render.points };
    const t0 = performance.now();
    for (let i = 0; i < n; i++) { api.render(); }
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));  // wait for the GPU (software) to finish
    info.msPerRender = +((performance.now() - t0) / n).toFixed(1);
    const c = R.domElement; info.px = [c.width, c.height];
    return info;
  }, n);
}

// frames per second the page achieves over `ms` while the mouse keeps rotating the view (rAF count), and the main
// thread's script time (CDP Performance metrics)
export async function fpsWhileRotating(page, ms = 4000) {
  const r = await canvasRect(page);
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Performance.enable");
  const m0 = Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]));
  await page.evaluate(() => { window.__rafN = 0; window.__rafOn = true; const f = () => { window.__rafN++; if (window.__rafOn) requestAnimationFrame(f); }; requestAnimationFrame(f);
    // count real draws of the scene
    const api = document.querySelector(".s3d-view").__scene3d, R = api.__renderer; window.__draws = 0;
    if (!R.__wrapped) { const orig = R.render.bind(R); R.render = (...a) => { window.__draws++; return orig(...a); }; R.__wrapped = true; } });
  const x0 = r.x + r.w / 2, y0 = r.y + r.h / 2;
  await page.mouse.move(x0, y0); await page.mouse.down();
  const t0 = Date.now(); let i = 0;
  while (Date.now() - t0 < ms) { i++; await page.mouse.move(x0 + 150 * Math.sin(i / 10), y0 + 40 * Math.cos(i / 13)); await sleep(16); }
  await page.mouse.up();
  const res = await page.evaluate(() => { window.__rafOn = false; return { raf: window.__rafN, draws: window.__draws }; });
  const m1 = Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]));
  const secs = (Date.now() - t0) / 1000;
  await cdp.detach();
  return { secs: +secs.toFixed(2), rafFps: +(res.raf / secs).toFixed(1), drawsPerSec: +(res.draws / secs).toFixed(1), scriptShare: +((m1.ScriptDuration - m0.ScriptDuration) / secs).toFixed(2), taskShare: +((m1.TaskDuration - m0.TaskDuration) / secs).toFixed(2) };
}

export async function clickView(page, name) {
  return page.evaluate((name) => { document.querySelector(".s3d-view").__scene3d.view(name); }, name);
}
export async function clickToolButton(page, label) {
  const b = await page.$(`.s3d-tools button:text-is("${label}")`);
  if (b) { await b.click(); await settle(page, 200); return true; }
  return false;
}
