// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Key frames of the player (owner, 2026-10-29), in a browser: for every visualization a run is recorded with changes in
// the middle (live set-up, actions, slice planes added and removed; v09 also in ordinary space, where the scene's box
// grows), the page is opened at the end of the record, and at cursors going backwards the view brought back through a
// key frame (key frames every 3 messages) is compared with the view rebuilt from the record at the same cursor: the 2-D
// canvases' pixels (drawn in software, each view drawn once more before it is read), the 3-D scene's layers (geometry,
// sphere radii, children), the slice planes with or without their image, the scene's box, the panels' and overlays'
// texts (review 2026-10-29, record-checkpoints-keyframes, CK-6).
//
// Run against a PRIVATE server (never the shared one on 8479), with Playwright's image and a playwright package; the
// playgrounds' records cross segments only with short ones (-e LFVIZ_PLAYGROUND_CKPT=6; review B6-F23):
//   docker run -d --name lf-kf-srv -v <engine>:/lf:ro -v <tmp runs>:/lf/visualizations/runs -e LFPHYS_NO_GPU=1 \
//     -e LFVIZ_PLAYGROUND_CKPT=6 \
//     -w /lf/visualizations -p 8507:8479 light-funnel-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
//   docker run --rm --init --shm-size=2g --network host -v <a scratch dir with node_modules/playwright@1.58.2>:/pw \
//     -v <engine>/visualizations/tests/browser:/t:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     sh -c "cp /t/keyframes.mjs /pw/ && node /pw/keyframes.mjs 8507 [viz,...]"
// (the script runs next to its node_modules: ES modules resolve packages from the script's folder)
// VARIANT (review UX-ui leftovers, U12): the changes in the middle are the new live parameters.
// Prints one JSON line per visualization and exits with code 1 when a comparison differs.
import { chromium } from "playwright";

const port = process.argv[2] || "8507";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const settle = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 400)))));
// the view drawn once more at the same cursor before it is compared: the browser's first drawing of a canvas just
// resized (the cursor's set-up changes the toolbar, and so the canvas's size) may differ by a few levels in
// antialiased pixels from any later drawing of the same commands (measured 2026-10-29: v06, v07)
const steady = async (page) => { await settle(page); await page.evaluate(() => window.__lfPlayer.redraw()); await settle(page); };

const SMALL = {
  v08_wave_3d: { n: 128, zmax: 10.0 },
  v09_thomas_3d: { ngrid: 48 },
  v11_double_slit_2d: { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 100, n_tracks: 10 },
  v12_arrival_times_2d: { grid: "coarse", n_bohm: 100, n_tracks: 10, L: 12.0, sigma_z: 2.0, sigma_x: 2.0 },
  v15_kerr_shadow: { res: "s" },
  v17_mie_scattering: { radius_um: 1.0, width: 0.05, n_lam: 8 },
};
// what changes in the middle of the record: two commands (set values, an action, or a view request)
const PLAN = {
  v01_light_travel: [{ action: ["flash", { obj: "earth" }] }, { action: ["flash", { obj: "rocket" }] }],
  v02_double_slit: [{ set: { lam_nm: 500.0 } }, { action: ["clear", {}] }],
  v03_quantum_1d: [{ set: { energy: 1.2 } }, { action: ["clear", {}] }],
  v04_orbits: [{ set: { ghost: true } }, { set: { ghost: false, time_units: "geo" } }],
  v05_optics_bench: [{ set: { theta_deg: 30.0 } }, { set: { pol: "s" } }],
  v06_qcd: [{ set: { mu: 100.0 } }, { set: { system: "bottom" } }],
  v07_bell_test: [{ set: { switch: "fixed" } }, { set: { b_deg: 30.0 } }],
  v08_wave_3d: [{ view: { op: "plane", id: 2, origin: [0, 0, 5], normal: [1, 0, 0] } }, { view: { op: "remove", id: 2 } }],
  v09_thomas_3d: [{ view: { op: "plane", id: 2, origin: [0, 0, 0], normal: [1, 0, 0] } }, { view: { op: "remove", id: 2 } }],
  v10_fast_observer: [{ set: { obs_beta: 0.5 } }, { set: { yaw: 30.0 } }],
  v11_double_slit_2d: [{ set: { a: 2.0 } }, { set: { w: 1.5, V0: 5.0 } }],
  v12_arrival_times_2d: [{ set: { mu_w: 3.0 } }, { set: { W0: 2.0 } }],
  v13_hydrogen_3d: [{ set: { n: 3, l: 2, m: 0 } }, { set: { mode: "super", n: 1, l: 0, m: 0, n2: 2, l2: 1, m2: 0, ng: "64" } }],
  v14_quarkonium_3d: [{ set: { l: 1 } }, { set: { ng: "64" } }],
  v15_kerr_shadow: [{ set: { incl: 60.0 } }, { set: { retro: true } }],
  v16_optical_vortices: [{ set: { f_rot: 8.0 } }, { view: { op: "plane", id: 2, origin: [0, 0, 0], normal: [1, 0, 0] } }],
  v17_mie_scattering: [{ view: { op: "plane", id: 2, origin: [0, 0, 0], normal: [1, 0, 0] } }, { set: { lam_nm: 480.0 } }],
};
// extra runs: v09 in ordinary space, where the box grows as the path is revealed (the craft's size: CK-1)
const EXTRA = [// v02 with the conducting screen (B8): vector hits, the other model's curve, TE/TM and the difference strip
               { name: "v02_vector", viz: "v02_double_slit", body: { preset: "vector_narrow" },
                 plan: [{ set: { pol_state: "H" } }, { action: ["clear", {}] }] },
               { name: "v09_lab", viz: "v09_thomas_3d", body: { preset: "lab", params: { loop: "circle", rho: 2.0 } }, speed: 1e9,
                 plan: [{ view: { op: "plane", id: 2, origin: [0, 0, 0], normal: [1, 0, 0] } }, { view: { op: "remove", id: 2 } }] },
               // the playgrounds (B6): scene changes and an action in the middle of the record (their trails, waves, Bohm
               // points, shapes and measured positions are brought back by key frames)
               { name: "p01_gravity", viz: "p01_gravity", body: { preset: "inner" },
                 plan: [{ scene: { op: "add", type: "star", values: { x: 3.0, vmode: "manual", vy: 10.0 } } }, { scene: { op: "remove", id: "o2" } }] },
               { name: "p02_quantum", viz: "p02_quantum", body: { preset: "trap" },
                 plan: [{ action: ["measure", { particle: "o2", sigma: 1.0 }] },
                        { scene: { op: "add", type: "packet", values: { x: -8.0, wavelength: 4.0, sx: 1.5, sy: 1.5, bohm: 20 } } }] },
               { name: "p03_molecules", viz: "p03_molecules", body: { preset: "piston" },
                 plan: [{ scene: { op: "add", type: "thermostat", values: { T: 200.0, tau: 1.0 } } }, { scene: { op: "add", type: "atom", values: { x: 3.0, y: 2.0 } } }] },
               { name: "p04_fluids", viz: "p04_fluids", body: { preset: "cavity" },
                 plan: [{ scene: { op: "add", type: "disk", values: { x: 0.5, y: 0.5, radius: 0.08 } } }, { view: { op: "field", field: "vorticity" } }] }];

async function fingerprint(page) {
  return page.evaluate(() => {
    const out = [];
    const h = (s) => { let x = 2166136261; for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 16777619) >>> 0; } return x; };
    // the 2-D canvases' own pixels (not screenshots: the page's compositor changes single pixels by one level between
    // two screenshots of an unchanged canvas, measured 2026-10-29); the 3-D view's WebGL canvas through its layers
    for (const c of document.querySelectorAll("canvas")) {
      if ((c.closest(".s3d-view") && !c.closest(".s3d-win")) || !c.offsetParent || !c.width) continue;
      let x = 2166136261;
      try { const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data; for (let i = 0; i < d.length; i++) { x ^= d[i]; x = Math.imul(x, 16777619) >>> 0; } } catch (e) { x = -1; }
      out.push(`c${c.width}x${c.height}:${x}`);
    }
    const sc = document.querySelector(".s3d-view");
    if (sc && sc.__scene3d) {
      const S = sc.__scene3d.state;
      for (const L of [...S.layers.values()].sort((a, b) => (a.id < b.id ? -1 : 1))) {
        let acc = 0, n = 0, radius = null;
        L.obj.traverse((o) => {
          if (!o.geometry) return;
          if (radius === null && o.geometry.parameters && o.geometry.parameters.radius) radius = o.geometry.parameters.radius;
          const g = o.geometry, cnt = Number.isFinite(g.drawRange.count) ? g.drawRange.count : Infinity;
          for (const name of ["position", "color"]) {
            const a = g.attributes[name]; if (!a) continue;
            const m = Math.min(a.array.length, cnt === Infinity ? a.array.length : cnt * a.itemSize);
            for (let i = 0; i < m; i++) { const v = a.array[i]; if (Number.isFinite(v)) acc += v * ((i % 97) + 1); }
            n += m;
          }
        });
        out.push(`L${L.id}:${L.visible ? 1 : 0}:${n}:${acc.toPrecision(8)}:${radius}:${L.obj.children.length}`);
      }
      for (const [id, P] of [...S.planes].sort()) out.push(`P${id}:${!!P.data}`);
      out.push(`B${JSON.stringify(S.box)}`);
    }
    for (const w of document.querySelectorAll(".slicewin")) {
      const c = w.querySelector("canvas.sw-canvas");
      let sum = 0;
      try { const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data; for (let i = 0; i < d.length; i += 4) sum += d[i] + 2 * d[i + 1] + 3 * d[i + 2]; } catch (e) { sum = -1; }
      out.push(`W${sum}`);
    }
    for (const p of document.querySelectorAll(".panel, .overlay")) out.push(`T${h(p.innerText || "")}`);
    return out;
  });
}

async function waitRun(id, pred, timeout = 300000) {
  const t0 = Date.now();
  for (;;) {
    const m = await get(`/api/runs/${id}`);
    if (pred(m)) return m;
    if (Date.now() - t0 > timeout) throw new Error(`timeout: run ${id}`);
    await sleep(500);
  }
}

const only = process.argv[3] ? process.argv[3].split(",") : null;
const jobs = Object.keys(PLAN).map((viz) => ({ name: viz, viz, body: SMALL[viz] ? { params: SMALL[viz] } : {}, plan: PLAN[viz] }))
  .concat(EXTRA).filter((j) => !only || only.includes(j.name) || only.includes(j.viz));
// 2-D canvases rasterized in software: the GPU path (swiftshader here) antialiases the same commands differently from
// one drawing to the next (measured 2026-10-29), which would hide or fake a difference of the views' data; reading their
// pixels back then changes nothing either
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist",
                                          "--disable-accelerated-2d-canvas"] });
let failed = 0;
for (const job of jobs) {
  const errs = [];
  try {
    const r = await post("/api/runs", { viz: job.viz, seed: 3, ...job.body });
    const id = r.id;
    await waitRun(id, (m) => m.state === "running");
    const doIt = (c) => (c.set ? post(`/api/runs/${id}/command`, { cmd: "set", args: { values: c.set } })
      : c.action ? post(`/api/runs/${id}/command`, { cmd: "action", args: { name: c.action[0], args: c.action[1] } })
        : c.scene ? post(`/api/runs/${id}/command`, { cmd: "scene", args: c.scene })
          : post(`/api/runs/${id}/command`, { cmd: "view", args: c.view }));
    if (job.speed) await post(`/api/runs/${id}/command`, { cmd: "speed", args: { value: job.speed } });
    await post(`/api/runs/${id}/command`, { cmd: "play" });
    await sleep(7000); await doIt(job.plan[0]);
    await sleep(7000); await doIt(job.plan[1]);
    await sleep(7000);
    await post(`/api/runs/${id}/command`, { cmd: "pause" });
    await sleep(1500);
    const page = await br.newPage({ viewport: { width: 1600, height: 1000 } });
    page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`));
    page.on("console", (m) => { if (m.type() === "error" && !/key frame not restored/.test(m.text())) errs.push(`console: ${m.text()}`.slice(0, 300)); });
    await page.goto(`${base}/run?id=${id}&key_every=3`);  // opened at the end of the record
    await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка записи/.test(document.querySelector("#status").textContent || ""), null, { timeout: 180000 });
    await settle(page);
    const nf = await page.evaluate(() => window.__lfPlayer.frames());
    const res = { run: job.name, frames: nf, keys: await page.evaluate(() => window.__lfPlayer.keys()), steps: [] };
    for (const p of [0.9, 0.6, 0.45, 0.3, 0.15, 0.05]) {  // backwards, as ◀ goes
      const before = await page.evaluate(() => ({ ...window.__lfPlayer.dbg }));
      await page.evaluate((i) => window.__lfPlayer.goTo(i), Math.round(p * (nf - 1)));
      await steady(page);
      const after = await page.evaluate(() => ({ ...window.__lfPlayer.dbg }));
      const A = await fingerprint(page);
      await page.evaluate(() => window.__lfPlayer.rebuildFromRecord());
      await steady(page);
      const B = await fingerprint(page);
      const diffs = A.map((x, k) => (x !== B[k] ? [x, B[k]] : null)).filter(Boolean);
      const same = diffs.length === 0 && A.length === B.length;
      if (!same) failed++;
      res.steps.push({ p, how: after.fromKey > before.fromKey ? "key" : after.full > before.full ? "full" : "feed",
                       keyFailed: after.keyFailed - before.keyFailed, same,
                       diffs: diffs.slice(0, 3).map(([a, b]) => [String(a).slice(0, 90), String(b).slice(0, 90)]) });
    }
    res.errors = errs.slice(0, 5);
    if (errs.length) failed++;
    console.log(JSON.stringify(res));
    await page.close();
  } catch (e) { failed++; console.log(JSON.stringify({ run: job.name, failed: e.message })); }
}
await br.close();
console.log(failed ? `FAILED: ${failed}` : "all equal");
process.exit(failed ? 1 : 0);
