// Review 2026-10-29, check k06: the author's comparison (a view brought back through a key frame against the view
// rebuilt from the record at the same cursor), with what it leaves out: live changes and actions in the middle of the
// record, slice planes added, moved and removed, the page opened at the END of the record (the usual way to look at a
// suspended run), and a richer fingerprint (the author's canvases, 3-D layers and panels, plus each plane's image, the
// slice windows' pixels, the layers' sphere radii and child counts, the scene's box).
//   node k06_scenarios.mjs <port> [viz,...]
import { createHash } from "crypto";
import { writeFileSync } from "fs";
import { browser, dbg, get, post, scene, settle, sleep, waitRun } from "./k_common.mjs";

const SMALL = {
  v08_wave_3d: { n: 128, zmax: 10.0 },
  v09_thomas_3d: { ngrid: 48 },
  v11_double_slit_2d: { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 100, n_tracks: 10 },
  v12_arrival_times_2d: { grid: "coarse", n_bohm: 100, n_tracks: 10, L: 12.0, sigma_z: 2.0, sigma_x: 2.0 },
};
// what is changed in the middle of the record: [first, second] (set values, an action, or a view request)
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
  v11_double_slit_2d: [{ set: { slit_b: false } }, { set: { slit_b: true } }],
  v12_arrival_times_2d: [{ set: { slit_b: false } }, { set: { slit_a: false } }],
};
const port = process.argv[2] || "8510";
const only = process.argv[3] ? process.argv[3].split(",") : Object.keys(PLAN);
const out = [], errs = [];
const log = (...a) => { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); out.push(s); console.log(s); };

async function fingerprint(page) {  // the author's (dev_keyframes.mjs), verbatim in substance
  const parts = [];
  for (const hdl of await page.$$("canvas")) {
    const skip = await hdl.evaluate((c) => !!(c.closest(".s3d-view") && !c.closest(".s3d-win")) || !c.offsetParent || !c.width);
    if (skip) continue;
    try { parts.push("c" + createHash("sha1").update(await hdl.screenshot()).digest("hex").slice(0, 12)); } catch (e) { /* off-screen */ }
  }
  const rest = await page.evaluate(() => [...document.querySelectorAll(".panel")].map((p) => {
    const s = p.innerText || ""; let x = 2166136261; for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 16777619) >>> 0; } return `T${x}`;
  }));
  const sc = await scene(page);
  if (sc) {
    for (const [id, L] of Object.entries(sc.layers).sort()) parts.push(`L${id}:${L.n}:${L.acc}:${L.radius}:${L.children}`);
    for (const [id, P] of Object.entries(sc.planes).sort()) parts.push(`P${id}:${P.hasImage}`);
    for (const w of sc.wins) parts.push(`W${w.id}:${w.pix}`);
    parts.push(`B${JSON.stringify(sc.box)}`);
  }
  return parts.concat(rest);
}

const br = await browser();
for (const viz of only) {
  try {
    const r = await post("/api/runs", SMALL[viz] ? { viz, params: SMALL[viz], seed: 3 } : { viz, seed: 3 });
    const id = r.id;
    await waitRun(id, (m) => m.state === "running", 300000);
    const doIt = async (c) => {
      if (c.set) return post(`/api/runs/${id}/command`, { cmd: "set", args: { values: c.set } });
      if (c.action) return post(`/api/runs/${id}/command`, { cmd: "action", args: { name: c.action[0], args: c.action[1] } });
      return post(`/api/runs/${id}/command`, { cmd: "view", args: c.view });
    };
    await post(`/api/runs/${id}/command`, { cmd: "play" });
    await sleep(8000); await doIt(PLAN[viz][0]);
    await sleep(8000); await doIt(PLAN[viz][1]);
    await sleep(8000);
    await post(`/api/runs/${id}/command`, { cmd: "pause" });
    await sleep(1500);
    const page = await br.newPage({ viewport: { width: 1600, height: 1000 } });
    page.on("pageerror", (e) => errs.push(`${viz} pageerror: ${e.message}`));
    page.on("console", (m) => { if (m.type() === "error") errs.push(`${viz} console: ${m.text()}`.slice(0, 300)); });
    await page.goto(`http://127.0.0.1:${port}/run?id=${id}&key_every=3`);
    await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка записи/.test(document.querySelector("#status").textContent || ""), null, { timeout: 180000 });
    await settle(page);
    const nf = (await dbg(page)).frames;
    const res = { viz, run: id, frames: nf, keys: (await dbg(page)).keys, steps: [] };
    for (const p of [0.9, 0.6, 0.45, 0.3, 0.15, 0.05]) {  // backwards, as ◀ goes
      const before = await dbg(page);
      await page.evaluate((i) => window.__lfPlayer.goTo(i), Math.round(p * (nf - 1)));
      await settle(page);
      const after = await dbg(page);
      const A = await fingerprint(page);
      await page.evaluate(() => window.__lfPlayer.rebuildFromRecord());
      await settle(page);
      const B = await fingerprint(page);
      const diffs = A.map((x, k) => (x !== B[k] ? [x, B[k]] : null)).filter(Boolean);
      res.steps.push({ p, how: after.fromKey > before.fromKey ? "key" : after.full > before.full ? "full" : "feed",
                       keyFailed: after.keyFailed - before.keyFailed, same: diffs.length === 0 && A.length === B.length,
                       diffs: diffs.slice(0, 3).map(([a, b]) => [String(a).slice(0, 90), String(b).slice(0, 90)]) });
    }
    log(JSON.stringify(res));
    await page.close();
  } catch (e) { log(`${viz} FAILED: ${e.message}`); }
}
log("errors:", JSON.stringify(errs.slice(0, 30)));
writeFileSync(`out/k06_scenarios_${port}.txt`, out.join("\n") + "\n");
await br.close();
