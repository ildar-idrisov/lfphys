// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The 3-D view's rendering contract (review 2026-11-04_internal_UX-3d; RULES.md §2.10), in a browser, on real runs:
//   depth    the volume in front of an object covers it, behind it is hidden (A1)
//   planes   crossing slice planes are right at every pixel; the cloud in front of a plane is drawn over it (A2)
//   views    a 2-D world opens from above; «Сверху» looks along "up" with the slice window's axes (A3, A14)
//   fit      the box's 8 corners are on screen as opened and after a resize; a moved camera is kept (A4)
//   box      a wider or repeated box never moves a camera the experimenter moved (A7, UX-ui U1)
//   clip     zoomed far out the scene is still inside near/far (A8)
//   labels   labels have a size in pixels, are hidden behind solids and do not overlap (A9)
//   lit      spheres are shaded (brighter in the middle than at the rim) (A5)
//   pivot    a double click puts the centre of rotation on the object under the pointer (A6)
//   quality  while the camera moves a volume is drawn at half the pixels, at full quality when it stops (A11)
//   panel    the panel «Слои сцены» is not rebuilt while a world plays (A17)
//   keys     Backspace does not remove the selected slice, Delete does (A16); no preserved drawing buffer (A18)
// Run against a PRIVATE server (never the shared one on 8479), with Playwright's image and a playwright package:
//   docker run -d --name lf-s3-srv -v <engine>:/lf:ro -v <tmp runs>:/lf/visualizations/runs -e LFPHYS_NO_GPU=1 \
//     -w /lf/visualizations -p 8508:8479 lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
//   docker run --rm --init --shm-size=2g --network host -v <a scratch dir with node_modules/playwright@1.58.2>:/pw \
//     -v <engine>/visualizations/tests/browser:/t:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     sh -c "cp /t/scene3d_checks.mjs /pw/ && node /pw/scene3d_checks.mjs 8508 [case,...]"
// Prints one JSON line per case and exits with code 1 when a check fails.
import { chromium } from "playwright";

const port = process.argv[2] || "8508";
const base = `http://127.0.0.1:${port}`;
const only = process.argv[3] ? process.argv[3].split(",") : null;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const settle = (page, ms = 400) => page.evaluate((ms) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, ms)))), ms);
const cmd = (id, c, args) => post(`/api/runs/${id}/command`, { cmd: c, args });

async function start(viz, body = {}) {
  let r = null;
  for (let k = 0; k < 60; k++) { r = await post("/api/runs", { viz, seed: 3, ...body }); if (r.id || !/вычислител/.test(r.error || "")) break; await sleep(3000); }
  if (!r.id) throw new Error("run not started: " + JSON.stringify(r).slice(0, 300));
  const t0 = Date.now();
  for (;;) {
    const m = await get(`/api/runs/${r.id}`);
    if (m.state === "running") break;
    if (m.state === "suspended") await cmd(r.id, "play");
    if (Date.now() - t0 > 240000) throw new Error("timeout starting " + viz);
    await sleep(500);
  }
  await cmd(r.id, "play");
  return r.id;
}
async function open(br, id, errs, { playMs = 4000, width = 1600, height = 1000, storage = null } = {}) {
  const page = await br.newPage({ viewport: { width, height } });
  // per-viewer layout choices kept in localStorage (e.g. p04/p02 in a plane hide the 3-D view by default, review UX-ui U15)
  if (storage) await page.addInitScript((kv) => { for (const [k, v] of Object.entries(kv)) { try { localStorage.setItem(k, v); } catch (e) { /* storage off */ } } }, storage);
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`console: ${m.text()}`.slice(0, 300)); });
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && document.querySelector(".s3d-view")?.__scene3d
    && !/загрузка записи/.test((document.querySelector("#status") || {}).textContent || ""), null, { timeout: 180000 });
  await sleep(playMs); await settle(page);
  return page;
}
const api = (page, f, arg) => page.evaluate(([f, arg]) => (0, eval)(f)(document.querySelector(".s3d-view").__scene3d, arg), [f.toString(), arg]);
const dist = (a, b) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) + Math.abs(a[2] - b[2]);
async function rect(page) { return page.evaluate(() => { const r = document.querySelector(".s3d-view canvas").getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; }); }
async function drag(page, dx, dy, { button = "left" } = {}) {
  const r = await rect(page), x0 = r.x + r.w / 2, y0 = r.y + r.h / 2;
  await page.mouse.move(x0, y0); await page.mouse.down({ button });
  for (let i = 1; i <= 8; i++) await page.mouse.move(x0 + dx * i / 8, y0 + dy * i / 8);
  await page.mouse.up({ button }); await settle(page, 300);
}
async function cornersOnScreen(page) {
  return api(page, (a) => {
    const [lo, hi] = a.state.box, cv = a.el.querySelector("canvas").getBoundingClientRect(); let n = 0;
    for (const x of [lo[0], hi[0]]) for (const y of [lo[1], hi[1]]) for (const z of [lo[2], hi[2]]) {
      const [sx, sy] = a.screenOf([x, y, z]); if (sx >= cv.left && sx <= cv.right && sy >= cv.top && sy <= cv.bottom) n++;
    }
    return n;
  });
}

const CASES = {
  async depth(br) {
    const errs = [], id = await start("v13_hydrogen_3d", { preset: "2pz" }), page = await open(br, id, errs);
    const g = await api(page, (a) => {
      a.view("iso"); for (const P of a.planes()) a.setPlaneVisible(P.id, false);
      const S = a.state, [nz, nx, ny] = S.vol.dims, d = S.vol.data, [lo, hi] = S.box; let best = -1, bi = 0;
      for (let i = 0; i < d.length; i++) if (d[i] > best) { best = d[i]; bi = i; }
      const iz = Math.floor(bi / (nx * ny)), ix = Math.floor((bi % (nx * ny)) / ny), iy = bi % ny;
      const pk = [lo[0] + (hi[0] - lo[0]) * (ix + 0.5) / nx, lo[1] + (hi[1] - lo[1]) * (iy + 0.5) / ny, lo[2] + (hi[2] - lo[2]) * (iz + 0.5) / nz];
      const cam = a.cameraState().pos, size = S.size;
      const toward = (p, s) => { const v = p.map((c, k) => c - cam[k]), L = Math.hypot(...v); return p.map((c, k) => c + s * v[k] / L); };
      return { back: toward(pk, 0.15 * size), front: toward(pk.map((q) => -q), -0.15 * size), r: 0.03 * size };
    });
    const px = (p) => api(page, (a, p) => a.pixelAt(p), p);
    const cloudBack = await px(g.back);
    await api(page, (a, g) => a.setSpheres("probe", new Float32Array([...g.front, ...g.back]), new Float32Array([g.r, g.r]), new Float32Array([0.2, 1, 0.3, 0.2, 1, 0.3]), { label: "probe", minFrac: 0 }), g);
    const withFront = await px(g.front), withBack = await px(g.back);
    await api(page, (a) => a.setLayerVisible("cloud", false));
    const aloneFront = await px(g.front), aloneBack = await px(g.back);
    await page.close();
    // the sphere in front: as without the cloud; the sphere behind the lobe: covered by the cloud (not its own colour)
    const ok = dist(withFront, aloneFront) <= 30 && dist(withBack, aloneBack) >= 60;
    return { ok, cloudBack, withFront, aloneFront, withBack, aloneBack, errs };
  },
  async planes(br) {
    const errs = [], id = await start("v13_hydrogen_3d", { preset: "1s" }), page = await open(br, id, errs, { playMs: 2000 });
    await cmd(id, "view", { op: "plane", id: 2, origin: [0, 0, 0], normal: [1, 0, 0] });
    await page.waitForFunction(() => document.querySelector(".s3d-view").__scene3d.planes().length >= 2, null, { timeout: 60000 });
    await sleep(3000); await settle(page);
    // the cloud in front of plane 1 is drawn over it: plane 1 painted one flat colour, a point above its middle (between
    // it and the camera), the cloud on and off
    const above = await api(page, (a) => {
      a.view("iso");
      const P1 = a.planes().find((p) => p.id === 1); P1.mat.uniforms.uMode.value = 2; P1.mat.uniforms.uColor.value.setRGB(0, 0.6, 0.2); P1.mat.uniforms.uDim.value = 1 / 0.3;
      const [lo, hi] = a.state.box; return [0, 0.06 * (hi[1] - lo[1]), 0];
    });
    const onA = await api(page, (a, p) => a.pixelAt(p), above);
    await api(page, (a) => a.setLayerVisible("cloud", false));
    const offA = await api(page, (a, p) => a.pixelAt(p), above);
    // crossing planes painted flat (1 red, 2 green): at points of plane 2 whose line of sight crosses plane 1 inside the
    // box, the plane nearer the camera is seen
    const res = await api(page, (a) => {
      const cols = { 1: [1, 0, 0], 2: [0, 1, 0], 3: [0, 0, 1] };
      for (const P of a.planes()) { P.mat.uniforms.uMode.value = 2; P.mat.uniforms.uColor.value.setRGB(...cols[P.id]); P.mat.uniforms.uDim.value = 1 / 0.3; }
      const S = a.state, [lo, hi] = S.box, P1 = a.planes().find((p) => p.id === 1), n1 = P1.n, o1 = P1.origin, c = a.cameraState().pos;
      const dot = (u, v) => u[0] * v[0] + u[1] * v[1] + u[2] * v[2], inside = (q) => q.every((x, i) => x >= lo[i] && x <= hi[i]);
      const out = [];
      for (const sy of [-0.15, -0.08, 0.08, 0.15]) for (const sz of [-0.1, 0.1]) {
        const p = [0, sy * (hi[1] - lo[1]), sz * (hi[2] - lo[2])];
        const dc = dot(c.map((x, i) => x - o1[i]), n1), dp = dot(p.map((x, i) => x - o1[i]), n1);
        let expect = "plane2";
        if (dc * dp < 0) {  // the camera and the point on opposite sides of plane 1: where does the sight line cross it?
          const t = dc / (dc - dp), q = c.map((x, i) => x + t * (p[i] - x));
          if (inside(q)) expect = "plane1";
        }
        const rgb = a.pixelAt(p);
        out.push({ p, expect, rgb, ok: expect === "plane2" ? rgb[1] > 2 * rgb[0] : rgb[0] > 2 * rgb[1] });
      }
      return out;
    });
    await page.close();
    const ok = dist(onA, offA) >= 20 && res.every((r) => r.ok);
    return { ok, cloudOverPlane: [onA, offA], crossing: res, errs };
  },
  async views(br) {
    const errs = [];
    const id = await start("p04_fluids", { preset: "cylinder_re20" }), page = await open(br, id, errs, { playMs: 2000, storage: { "p04.show3d": "1" } });
    const p04 = await api(page, (a) => {
      const [lo, hi] = a.state.box, c = a.cameraState(), out = { opened: c.pos[2] > hi[2] + 0.5 * (hi[0] - lo[0]) };
      a.view("top"); a.render();
      const m = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0], dx = 0.1 * (hi[0] - lo[0]), dy = 0.1 * (hi[1] - lo[1]);
      const s0 = a.screenOf(m), sx = a.screenOf([m[0] + dx, m[1], 0]), sy = a.screenOf([m[0], m[1] + dy, 0]);
      out.top = { xRight: sx[0] - s0[0] > 0.9 * Math.hypot(sx[0] - s0[0], sx[1] - s0[1]), yUp: s0[1] - sy[1] > 0.9 * Math.hypot(sy[0] - s0[0], sy[1] - s0[1]) };
      return out;
    });
    await page.close();
    const id2 = await start("v08_wave_3d", { preset: "double", params: { n: 128, zmax: 10.0 } }), page2 = await open(br, id2, errs, { playMs: 3000 });
    const v08 = await api(page2, (a) => {
      a.view("top"); a.render();
      const [lo, hi] = a.state.box, m = [0, 0, (lo[2] + hi[2]) / 2], d = 0.1 * (hi[2] - lo[2]);
      const s0 = a.screenOf(m), sz = a.screenOf([0, 0, m[2] + d]), sx = a.screenOf([d, 0, m[2]]);
      return { zRight: sz[0] - s0[0] > 0.9 * Math.hypot(sz[0] - s0[0], sz[1] - s0[1]), xUp: s0[1] - sx[1] > 0.9 * Math.hypot(sx[0] - s0[0], sx[1] - s0[1]) };
    });
    await page2.close();
    const ok = p04.opened && p04.top.xRight && p04.top.yUp && v08.zRight && v08.xUp;
    return { ok, p04, v08, errs };
  },
  async fit(br) {
    const errs = [], id = await start("v08_wave_3d", { preset: "double", params: { n: 128, zmax: 10.0 } });
    const page = await open(br, id, errs, { playMs: 6000 });
    const opened = await cornersOnScreen(page);
    await page.setViewportSize({ width: 1280, height: 800 }); await sleep(800); await settle(page);
    const resized = await cornersOnScreen(page);
    await drag(page, 120, 0);
    const before = await api(page, (a) => a.cameraState());
    await page.setViewportSize({ width: 1500, height: 950 }); await sleep(800); await settle(page);
    const after = await api(page, (a) => a.cameraState());
    await page.close();
    const kept = dist(before.pos, after.pos) < 1e-6 * (1 + Math.hypot(...before.pos));
    return { ok: opened === 8 && resized === 8 && kept, opened, resized, movedCameraKept: kept, errs };
  },
  async box(br) {
    const errs = [], id = await start("p01_gravity", { preset: "pythagorean" }), page = await open(br, id, errs, { playMs: 1500 });
    await cmd(id, "pause"); await sleep(500);
    await drag(page, 200, -90);
    const r = await rect(page); await page.mouse.move(r.x + r.w / 2, r.y + r.h / 2);
    for (let i = 0; i < 4; i++) { await page.mouse.wheel(0, -100); await sleep(40); }
    await settle(page, 500);
    const res = await api(page, (a) => {
      const c0 = a.cameraState(), box = a.state.box, wide = [box[0].map((x) => 4 * x), box[1].map((x) => 4 * x)];
      a.setBox(box); const c1 = a.cameraState();
      a.setBox(wide); const c2 = a.cameraState();
      const d = (p, q) => Math.hypot(...p.map((x, i) => x - q[i]));
      const same = d(c0.pos, c1.pos) < 1e-9 && d(c0.pos, c2.pos) < 1e-9 && d(c0.target, c2.target) < 1e-9;
      a.view("iso"); const c3 = a.cameraState();
      a.setBox([wide[0].map((x) => 2 * x), wide[1].map((x) => 2 * x)]); const c4 = a.cameraState();  // not moved: refitted
      return { userMoved: c0.userMoved, keptOnRepeatAndGrow: same, refitWhenNotMoved: d(c3.pos, c4.pos) > 1e-6, note: a.el.querySelector(".s3d-note").style.display !== "none" };
    });
    await page.close();
    return { ok: res.userMoved && res.keptOnRepeatAndGrow && res.refitWhenNotMoved, ...res, errs };
  },
  async clip(br) {
    const errs = [], id = await start("v08_wave_3d", { preset: "double", params: { n: 128, zmax: 10.0 } }), page = await open(br, id, errs);
    const r = await rect(page); await page.mouse.move(r.x + r.w / 2, r.y + r.h / 2);
    for (let i = 0; i < 60; i++) { await page.mouse.wheel(0, 100); await sleep(20); }
    await settle(page, 500);
    const c = await api(page, (a) => { const s = a.cameraState(), S = a.state, [lo, hi] = S.box, cen = [0, 1, 2].map((i) => (lo[i] + hi[i]) / 2);
      return { ...s, dc: Math.hypot(...s.pos.map((x, i) => x - cen[i])), R: 0.5 * Math.hypot(...[0, 1, 2].map((i) => hi[i] - lo[i])) }; });
    await page.close();
    return { ok: c.far >= c.dc + c.R && c.near <= Math.max(c.dc - c.R, 0) + 1e-9 + 0.01 * c.dc, ...c, errs };
  },
  async labels(br) {
    const errs = [], id = await start("v13_hydrogen_3d", { preset: "1s" }), page = await open(br, id, errs, { playMs: 2000 });
    const res = await api(page, (a) => {
      a.render();
      const S = a.state, H = a.el.clientHeight, fov = 38 * Math.PI / 180;
      const L = S.frameLabels, shown = L.filter((s) => s.visible);
      const px = L.map((s) => s.scale.y * H / (2 * Math.tan(fov / 2)) / s.userData.label.px);
      const flags = L.every((s) => s.material.depthTest === true && s.material.sizeAttenuation === false && s.material.depthWrite === false);
      // the shown labels' rectangles do not overlap
      const W = a.el.clientWidth, rects = shown.map((s) => { const v = s.position.clone().applyMatrix4(s.parent.matrixWorld); const [x, y] = a.screenOf([-v.z, v.y, v.x]);
        const w = s.userData.label.px * s.userData.label.aspect, h = s.userData.label.px; return [x - s.center.x * w + 0.12 * h, y - (1 - s.center.y) * h + 0.2 * h, x + (1 - s.center.x) * w - 0.12 * h, y + s.center.y * h - 0.2 * h]; });
      let overlaps = 0;
      for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) { const p = rects[i], q = rects[j]; if (p[0] < q[2] && q[0] < p[2] && p[1] < q[3] && q[1] < p[3]) overlaps++; }
      return { n: L.length, shown: shown.length, pxRatio: [Math.min(...px), Math.max(...px)], flags, overlaps };
    });
    await page.close();
    return { ok: res.flags && res.pxRatio[0] > 0.97 && res.pxRatio[1] < 1.03 && res.overlaps === 0 && res.shown >= 6, ...res, errs };
  },
  async lit(br) {
    const errs = [], id = await start("p03_molecules", { preset: "liquid_vapour" }), page = await open(br, id, errs, { playMs: 3000 });
    await cmd(id, "pause"); await sleep(800); await settle(page);
    const res = await api(page, (a) => {
      const L = a.layers().find((q) => q.kind === "spheres"), mesh = L.obj, m = mesh.matrixWorld.clone(), M = new mesh.matrixWorld.constructor();
      const cam = a.cameraState().pos;
      // the atom nearest to the camera
      let best = null;
      for (let i = 0; i < mesh.count; i++) {
        mesh.getMatrixAt(i, M); const e = M.elements, p = [-e[14], e[13], e[12]], r = Math.hypot(e[0], e[1], e[2]);
        const d = Math.hypot(...p.map((x, k) => x - cam[k]));
        if (!best || d < best.d) best = { p, r, d };
      }
      // a point on the rim: the centre moved by 0.85 r perpendicular to the line of sight
      const v = best.p.map((x, k) => x - cam[k]), up = [0, 0, 1], side = [v[1] * up[2] - v[2] * up[1], v[2] * up[0] - v[0] * up[2], v[0] * up[1] - v[1] * up[0]];
      const sl = Math.hypot(...side), rim = best.p.map((x, k) => x + 0.85 * best.r * side[k] / sl);
      const lum = (c) => 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2];
      const cc = a.pixelAt(best.p), cr = a.pixelAt(rim);
      return { centre: cc, rim: cr, ratio: lum(cr) / Math.max(1, lum(cc)), material: mesh.material.type };
    });
    await page.close();
    return { ok: res.ratio < 0.85, ...res, errs };
  },
  async pivot(br) {
    const errs = [], id = await start("p03_molecules", { preset: "maxwell" }), page = await open(br, id, errs, { playMs: 2000 });
    await cmd(id, "pause"); await sleep(800); await settle(page);
    const t = await api(page, (a) => {
      const mesh = a.layers().find((q) => q.kind === "spheres").obj, M = new mesh.matrixWorld.constructor(), cv = a.el.querySelector("canvas").getBoundingClientRect();
      const cx = cv.left + cv.width * 0.3, cy = cv.top + cv.height * 0.6; let best = null;
      for (let i = 0; i < mesh.count; i++) { mesh.getMatrixAt(i, M); const e = M.elements, p = [-e[14], e[13], e[12]], [x, y] = a.screenOf(p), d = Math.hypot(x - cx, y - cy); if (!best || d < best.d) best = { p, x, y, d, r: Math.hypot(e[0], e[1], e[2]) }; }
      return best;
    });
    await page.mouse.dblclick(t.x, t.y); await settle(page, 300);
    const c = await api(page, (a) => a.cameraState());
    await page.close();
    const d = Math.hypot(...c.target.map((x, i) => x - t.p[i]));
    return { ok: d <= 1.05 * t.r, atom: t.p, radius: t.r, target: c.target, distance: d, errs };
  },
  async quality(br) {
    const errs = [], id = await start("v13_hydrogen_3d", { preset: "1s" }), page = await open(br, id, errs, { playMs: 2000 });
    const r = await rect(page), x0 = r.x + r.w / 2, y0 = r.y + r.h / 2;
    await page.mouse.move(x0, y0); await page.mouse.down();
    for (let i = 1; i <= 6; i++) { await page.mouse.move(x0 + 20 * i, y0); await sleep(60); }
    const during = await api(page, (a) => a.frameStats().quality);
    await page.mouse.up(); await sleep(600); await settle(page);
    const after = await api(page, (a) => a.frameStats().quality);
    await page.close();
    return { ok: during === 0.5 && after === 1, during, after, errs };
  },
  async panel(br) {
    const errs = [], id = await start("p01_gravity", { preset: "sun_earth" }), page = await open(br, id, errs, { playMs: 2500 });
    const res = await page.evaluate(() => new Promise((done) => {
      const cb = [...document.querySelectorAll("label.s3d-layer input[type=checkbox]")][0];
      const box = cb ? cb.closest("label").parentElement.parentElement : null;
      if (!box) { done({ error: "no layers panel" }); return; }
      let muts = 0; const first = box.querySelector("input");
      const mo = new MutationObserver((l) => { muts += l.filter((m) => m.type === "childList").length; });
      mo.observe(box, { childList: true, subtree: true });
      setTimeout(() => { mo.disconnect(); done({ childListMutations: muts, firstInputReplaced: !first.isConnected }); }, 8000);
    }));
    await page.close();
    return { ok: !res.error && res.childListMutations === 0 && !res.firstInputReplaced, ...res, errs };
  },
  async keys(br) {
    const errs = [], id = await start("v13_hydrogen_3d", { preset: "1s" }), page = await open(br, id, errs, { playMs: 2000 });
    const pdb = await page.evaluate(() => { const c = document.querySelector(".s3d-view canvas"); const gl = c.getContext("webgl2"); return gl.getContextAttributes().preserveDrawingBuffer; });
    const n0 = await api(page, (a) => { a.select(1); return a.planes().length; });
    await page.locator("body").press("Backspace"); await sleep(2500); await settle(page);
    const n1 = await api(page, (a) => a.planes().length);
    await api(page, (a) => a.select(1));
    await page.locator("body").press("Delete");
    await page.waitForFunction(() => document.querySelector(".s3d-view").__scene3d.planes().length === 0, null, { timeout: 30000 }).catch(() => {});
    const n2 = await api(page, (a) => a.planes().length);
    await page.close();
    return { ok: pdb === false && n0 === 1 && n1 === 1 && n2 === 0, preserveDrawingBuffer: pdb, planes: [n0, n1, n2], errs };
  },
};

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
let failed = 0;
for (const [name, f] of Object.entries(CASES)) {
  if (only && !only.includes(name)) continue;
  let res;
  try { res = await f(br); } catch (e) { res = { ok: false, failed: String(e && e.stack || e).slice(0, 500) }; }
  if (res.errs && res.errs.length) res.ok = false;
  if (!res.ok) failed++;
  console.log(JSON.stringify({ case: name, ...res }));
}
await br.close();
console.log(failed ? `FAILED: ${failed}` : "all passed");
process.exit(failed ? 1 : 0);
