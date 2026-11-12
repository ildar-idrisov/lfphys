// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Direct manipulation in the playground (plan P16.2; the integrator's API of 2026-11-11), in a browser, with the edits
// checked in the run's record (its stream): on the toy section (tests/playgrounds/p99_toy, LFVIZ_EXTRA) at every
// viewport size given — select by a click (the marker and the inspector follow), drag in the 3-D scene (the object lands
// under the pointer; the camera does not move; a drag on empty space turns the camera and edits nothing), throw with
// Shift (the velocity in world length per world time: the pointer's world displacement over its last 100 ms ÷ (that
// time × the playback rate) × the throw scale; shown next to the cursor while throwing), a refusal of the world (its
// Russian text shown, the ghost snaps back, nothing changed), Esc (no edit), Delete (removed), a drag in the window of
// the plane z = 0 (the object lands under the pointer), the axis-bound handles in their three spellings ("y", 2, "0":
// along the axis only, Shift ignored, an axis across the window's plane refused there), and the read-only history (no
// edit); then, in each world p01–p04 whose palette declares handles, one drag of an object with a position handle
// (applied or refused, with the ghost snapping back) and one throw where a velocity handle exists. Before/after
// screenshots per viewport go to the output folder.
//
// Run against a PRIVATE server (never the shared one on 8479):
//   docker run -d --name lf-lbf-srv --memory=12g -p 8591:8479 -v <engine>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
//     -e LFPHYS_NO_GPU=1 -e LFVIZ_PLAYGROUND_CKPT=6 -e LFVIZ_EXTRA=/lf/visualizations/tests/playgrounds \
//     -w /lf/visualizations lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
//   docker run --rm --init --shm-size=2g --network host -v <a scratch dir with node_modules/playwright@1.58.2>:/pw \
//     -v <engine>/visualizations/tests/browser:/t:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     -e LFVIZ_LANG=en|ru sh -c "cp /t/*.mjs /pw/ && node /pw/manipulation.mjs 8591 [1600x1000,1280x800] [p99_toy,p01_gravity,...]"
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { LANG, esc, hasMsgid, inLang, loadI18n } from "./lfi18n.mjs";

const port = process.argv[2] || "8591";
const SIZES = (process.argv[3] || "1600x1000,1280x800").split(",").map((s) => s.split("x").map(Number));
const WORLDS = (process.argv[4] || "p99_toy,p01_gravity,p02_quantum,p03_molecules,p04_fluids").split(",");
const OUT = process.env.SHOTS || "/pw";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cmd = (id, c, a) => post(`/api/runs/${id}/command`, { cmd: c, args: a || {} });
// the language under test (LFVIZ_LANG, en by default): what the page shows is the player's own rendering of a msgid
const { t: tr } = await loadI18n(base);

// the run's record: every message's JSON part (u32 length | message; a message: u32 json length | JSON | blobs)
async function record(id) {
  const buf = new Uint8Array(await (await fetch(`${base}/api/runs/${id}/stream`)).arrayBuffer());
  const dv = new DataView(buf.buffer), out = [], dec = new TextDecoder();
  for (let off = 8; off + 4 <= buf.length;) {
    const n = dv.getUint32(off, true), m = off + 4, jl = dv.getUint32(m, true);
    out.push(JSON.parse(dec.decode(buf.subarray(m + 4, m + 4 + jl))));
    off = m + n;
  }
  return out;
}
const edits = (rec, id) => rec.filter((m) => m.type === "command" && m.cmd === "scene" && m.args.op === "edit" && (!id || m.args.id === id));
async function waitFor(fn, ms = 20000, step = 150) {
  const t0 = Date.now();
  for (;;) { const v = await fn(); if (v) return v; if (Date.now() - t0 > ms) return null; await sleep(step); }
}

const checks = [];
function check(name, ok, detail = {}) {
  checks.push({ name, ok: !!ok, ...detail });
  console.log(JSON.stringify({ name, ok: !!ok, ...detail }));
}

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });

// --- page helpers -----------------------------------------------------------------------------------------------------
async function openRun(page, id) {
  await page.goto(inLang(`${base}/run?id=${id}`));
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && window.__lfManip, null, { timeout: 120000 });
  await sleep(1500);
}
// the client point of an object in the 3-D view (null when not visible there)
const scr3 = (page, oid) => page.evaluate((id) => {
  const v = document.querySelector(".s3d-view"), sc = v && v.__scene3d, p = window.__lfManip.at(id);
  if (!sc || !p || !v.offsetParent) return null;
  const q = sc.project(p), r = v.querySelector("canvas").getBoundingClientRect();
  return q.inside && q.x > r.left + 4 && q.x < r.right - 4 && q.y > r.top + 4 && q.y < r.bottom - 4 ? [q.x, q.y] : null;
}, oid);
// the client point of an object in slice window k (null when the window does not show it)
const scrWin = (page, oid, k = 1) => page.evaluate(([id, k]) => {
  const ws = [...document.querySelectorAll(".s3d-windows")].map((e) => e.__slices).filter(Boolean);
  const p = window.__lfManip.at(id);
  for (const W of ws) {
    const h = W.helper(k); if (!h || !p) continue;
    const [x, y] = h.toCanvas(p), r = h.el.getBoundingClientRect();
    if (x > 2 && y > 2 && x < r.width - 2 && y < r.height - 2) return [r.left + x, r.top + y];
  }
  return null;
}, [oid, k]);
const winPoint = (page, x, y, k = 1) => page.evaluate(([x, y, k]) => {
  const W = [...document.querySelectorAll(".s3d-windows")].map((e) => e.__slices).filter(Boolean).find((w) => w.helper(k));
  return W ? W.helper(k).point({ clientX: x, clientY: y }) : null;
}, [x, y, k]);
const camera = (page) => page.evaluate(() => document.querySelector(".s3d-view").__scene3d.cameraState());
const sameCam = (a, b) => ["pos", "target"].every((k) => a[k].every((v, i) => Math.abs(v - b[k][i]) <= 1e-9 * (1 + Math.abs(v))));
// a drag with the mouse in `n` steps `dtMs` apart (the throw's timing is the pointer's)
async function dragPath(page, from, to, { n = 10, dtMs = 16, shift = false, before = null } = {}) {
  await page.mouse.move(from[0], from[1]);
  await page.mouse.down();
  if (shift) await page.keyboard.down("Shift");
  let t0 = 0, mid = null;
  for (let k = 1; k <= n; k++) {
    await page.mouse.move(from[0] + (to[0] - from[0]) * k / n, from[1] + (to[1] - from[1]) * k / n);
    if (k === 1) t0 = Date.now();
    if (k === n - 3 && before) mid = await before();  // what the page shows in the middle of the gesture
    if (dtMs && k < n) await sleep(dtMs);
  }
  const T = Date.now() - t0;  // from the first move to the last (the release follows at once: a throw's timing)
  if (before && mid === null) mid = await before();
  await page.mouse.up();
  if (shift) await page.keyboard.up("Shift");
  return { T, mid };
}
const toastText = (page) => page.evaluate(() => [...document.querySelectorAll(".toast")].map((t) => t.textContent).join(" | "));
const idle = (page) => waitFor(() => page.evaluate(() => !window.__lfManip.pending() && !window.__lfManip.snapping() && !window.__lfManip.dragging()), 15000);

// --- the toy section --------------------------------------------------------------------------------------------------
async function toy([W, H]) {
  const tag = `${W}x${H}`;
  const errs = [];
  const r = await post("/api/runs", { viz: "p99_toy", preset: "two", seed: 3 });
  const id = r.id;
  await waitFor(async () => (await get(`/api/runs/${id}`)).state === "running");
  await sleep(800);
  for (const [type, axis, position] of [["wall", "y", 3.5], ["mirror", 2, 0.1], ["screen", "0", 2.5]]) {
    await cmd(id, "scene", { op: "add", type, values: { axis, position } });
    await sleep(300);
  }
  const page = await br.newPage({ viewport: { width: W, height: H } });
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message} ${(e.stack || "").split("\n").slice(1, 3).join(" ")}`.slice(0, 400)));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`console: ${m.text()}`.slice(0, 300)); });
  await openRun(page, id);
  await page.screenshot({ path: `${OUT}/manip_toy_${tag}_before.png` });

  // 1. select by a click: the marker with the name, the inspector, the list
  const p2 = await scr3(page, "o2");
  await page.mouse.click(p2[0], p2[1]);
  await sleep(300);
  const sel = await page.evaluate(() => ({ sel: window.__lfManip.selected(), markers: document.querySelector(".s3d-view").__scene3d.markers(),
    spec: document.querySelector(".s3d-view").__scene3d.markerSpec("sel"),
    insp: document.querySelector(".pg-insp-name")?.value }));
  const name2 = tr({ $t: "{type} {n:d}", a: { type: { $t: "Particle" }, n: 2 } });
  check(`${tag} select: click picks the object, marker with its name, inspector follows`, sel.sel === "o2" && sel.markers.includes("sel") && sel.spec.text === name2 && sel.insp === name2, sel);

  // 2. drag in the 3-D view: lands under the pointer, one edit with the position only, the camera unmoved
  const cam0 = await camera(page);
  const p1 = await scr3(page, "o1"), to1 = [p1[0] + 110, p1[1] - 70];
  const n0 = edits(await record(id), "o1").length;
  const d1 = await dragPath(page, p1, to1, { before: () => page.evaluate(() => ({ dragging: window.__lfManip.dragging(), ghost: document.querySelector(".s3d-view").__scene3d.markerSpec("ghost") })) });
  await idle(page);
  await sleep(500);
  const rec1 = await record(id), e1 = edits(rec1, "o1");
  const land = await scr3(page, "o1"), cam1 = await camera(page);
  check(`${tag} drag 3-D: ghost while dragging`, d1.mid.dragging && d1.mid.ghost && d1.mid.ghost.ghost, { ghost: !!d1.mid.ghost });
  check(`${tag} drag 3-D: one edit, position only, applied`, e1.length === n0 + 1 && Object.keys(e1.at(-1).args.values).sort().join() === "x,y,z"
    && rec1.some((m) => m.type === "event" && m.name === "edit" && m.args.id === "o1"), { values: e1.at(-1)?.args.values });
  check(`${tag} drag 3-D: the object lands under the pointer`, land && Math.hypot(land[0] - to1[0], land[1] - to1[1]) < 2.5, { land, to1 });
  check(`${tag} drag 3-D: the camera does not fight the drag`, sameCam(cam0, cam1));
  await page.screenshot({ path: `${OUT}/manip_toy_${tag}_dragged.png` });

  // 3. negative control: a drag on empty space turns the camera and edits nothing
  const cv = await page.evaluate(() => { const r = document.querySelector(".s3d-view canvas").getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; });
  const empty = [cv[0] + 30, cv[1] + cv[3] - 60];
  const nAll = edits(await record(id)).length;
  await dragPath(page, empty, [empty[0] + 80, empty[1] - 20]);
  await sleep(500);
  check(`${tag} negative control: a drag on empty space turns the camera, no edit`, !sameCam(cam1, await camera(page)) && edits(await record(id)).length === nAll);

  // 4. a throw with Shift: velocity = world displacement / (wall time × rate) × scale; shown while throwing
  await cmd(id, "speed", { value: 2.0 });
  await page.fill(".pg-manip input[type=number]", "1.5");
  await page.press(".pg-manip input[type=number]", "Enter");
  await sleep(600);
  const rate = await page.evaluate(() => Number(document.querySelector("#speedv")?.textContent?.replace(",", ".")) || null);
  const pa = await page.evaluate(() => window.__lfManip.at("o2"));
  const q2 = await scr3(page, "o2");
  const n2 = edits(await record(id), "o2").length;
  const d2 = await dragPath(page, q2, [q2[0] + 140, q2[1] + 30], { n: 14, dtMs: 16, shift: true,
    before: () => page.evaluate(() => ({ text: window.__lfManip.text(), vel: document.querySelector(".s3d-view").__scene3d.markerSpec("ghost")?.vel })) });
  await idle(page);
  await sleep(400);
  const e2 = edits(await record(id), "o2").at(-1), v2 = e2 ? e2.args.values : {};
  const disp = ["x", "y", "z"].map((k, i) => (v2[k] - pa[i]) * (14 - 1) / 14), vel = [v2.vx, v2.vy, v2.vz];  // moves 2..14
  const exp = disp.map((d) => d / (d2.T / 1000) / 2.0 * 1.5);
  const cos = (exp[0] * vel[0] + exp[1] * vel[1] + exp[2] * vel[2]) / (Math.hypot(...exp) * Math.hypot(...vel));
  const ratio = Math.hypot(...vel) / Math.hypot(...exp);
  check(`${tag} throw: velocity shown next to the cursor while throwing`, (d2.mid.text || "").startsWith(tr("throw: v = {v} {unit} (×{k:.3g}{auto})", { v: "", unit: "", k: 1, auto: "" }).split(" ")[0]) && (d2.mid.text || "").includes("×" + tr({ $t: "{k:.3g}", a: { k: 1.5 } })) && d2.mid.vel, { text: d2.mid.text });
  check(`${tag} throw: one edit with position and velocity in world units per world time (rate 2, scale 1.5)`,
    edits(await record(id), "o2").length === n2 + 1 && vel.every(Number.isFinite) && cos > 0.97 && ratio > 0.6 && ratio < 1.6,
    { vel, expected: exp, cos, ratio, T: d2.T, rate });
  await cmd(id, "speed", { value: 1.0 });
  await sleep(500);
  // 4b. the automatic scale (reviews LB1-F14, LB1-p02-ux X4): from the world's own scale — a flick of the view's width
  //     per wall second throws across the region (10 m) in 2 wall seconds at the playback rate (1), never above half the
  //     largest speed (the toy particle's vmax, 12 m/s) — so |v| = min(10 / (2 × 1), 12 / 2) × (px per s) / (view px)
  await page.click(".pg-manip .pg-auto");
  const vmax = 12, W3 = await page.evaluate(() => document.querySelector(".s3d-view canvas").clientWidth);
  const vAuto = Math.min(10 / (2 * 1.0), vmax / 2);
  const qa = await scr3(page, "o1");
  const na = edits(await record(id), "o1").length;
  const da = await dragPath(page, qa, [qa[0] - 130, qa[1] + 40], { n: 14, dtMs: 16, shift: true, before: () => page.evaluate(() => window.__lfManip.text()) });
  await idle(page); await sleep(400);
  const ea = edits(await record(id), "o1").at(-1), va = ea ? [ea.args.values.vx, ea.args.values.vy, ea.args.values.vz] : [NaN];
  const pxs = Math.hypot(130, 40) * 13 / 14 / (da.T / 1000), expA = vAuto * pxs / W3, ratioA = Math.hypot(...va) / expA;
  check(`${tag} throw, automatic scale from the region and the rate: |v| ≈ min(R/(2 s·rate), vmax/2) × (px/s) / (view width px)`,
    edits(await record(id), "o1").length === na + 1 && (da.mid || "").includes(", " + tr("auto") + ")") && ratioA > 0.6 && ratioA < 1.6 && !("asked" in (ea?.args || {})),
    { v: va, expected: expA, ratio: ratioA, text: da.mid });
  // 4c. a throw faster than the world carries is clamped to velocity_max and says so (readout and log)
  await page.fill(".pg-manip input[type=number]", "200");
  await page.press(".pg-manip input[type=number]", "Enter");
  const qb = await scr3(page, "o2");
  await dragPath(page, qb, [qb[0] + 40, qb[1] - 20], { n: 8, dtMs: 16, shift: true });
  const db = { mid: await page.evaluate(() => window.__lfManip.released()) };  // the readout as it stood at the release
  await idle(page); await sleep(400);
  const rb = await record(id), eb = edits(rb, "o2").at(-1), vb = [eb.args.values.vx, eb.args.values.vy, eb.args.values.vz];
  const evb = rb.filter((m) => m.type === "event" && m.name === "edit" && m.args.id === "o2").at(-1);
  const clampTxt = tr("clamped to {vmax:.3g} {unit}: reduce the throw scale", { vmax: 12, unit: tr("m/s") });
  check(`${tag} throw clamped to velocity_max: |v| = 12 m/s, "clamped to … reduce the throw scale" in the readout and the log`,
    Math.abs(Math.hypot(...vb) - vmax) < 0.01 && eb.args.asked > vmax && (db.mid || "").includes(clampTxt)
      && hasMsgid(evb?.text, "— clamped to the largest speed {vmax:.4g} {unit} (the hand gave {gave:.4g}")
      && Number((/"gave":([-\d.e+]+)/.exec(JSON.stringify(evb?.text)) || [])[1]) > 12,
    { v: vb, asked: eb.args.asked, text: db.mid, log: tr(evb?.text) });
  // 4d. review LB1-F13: the hand stops before the release — the readout follows it while the pointer rests (no stale
  //     «ограничено»), the throw sent is slow and unclamped, and the log says no clamp
  {
    await cmd(id, "scene", { op: "edit", id: "o2", values: { x: 1, y: 0, z: 0, vx: 0, vy: 0, vz: 0 } });  // at rest in view
    await sleep(800);
    const q = await scr3(page, "o2"), nd = edits(await record(id), "o2").length;
    const clampWord = tr("clamped to {vmax:.3g} {unit}: reduce the throw scale", { vmax: 0, unit: "" }).split(" ")[0];
    await page.mouse.move(q[0], q[1]); await page.mouse.down(); await page.keyboard.down("Shift");
    for (let k = 1; k <= 8; k++) { await page.mouse.move(q[0] + 6 * k, q[1] - 3 * k); await sleep(16); }
    const during = await page.evaluate(() => window.__lfManip.text());
    await sleep(350);  // the pointer rests: the last 100 ms are still
    const rest = await page.evaluate(() => window.__lfManip.text());
    await page.mouse.up(); await page.keyboard.up("Shift");
    await idle(page); await sleep(400);
    const rd = await record(id), ed = edits(rd, "o2").at(-1), vd = [ed.args.values.vx, ed.args.values.vy, ed.args.values.vz];
    const evd = rd.filter((m) => m.type === "event" && m.name === "edit" && m.args.id === "o2" && m.t >= ed.t).at(-1);
    check(`${tag} F13: a resting pointer clears the clamp in the readout; the throw sent is not clamped, the log says none`,
      edits(rd, "o2").length === nd + 1 && during.includes(clampWord) && !rest.includes(clampWord) && Math.hypot(...vd) < vmax
        && !("asked" in ed.args) && !!evd && !hasMsgid(evd.text, "clamped"),
      { during, rest, v: vd, log: tr(evd?.text) });
  }
  // 4e. a type that shows its throws in another unit (velocity_display; integrator, 2026-11-12): the toy's cloud, in
  //     cm/s (factor 100) while its parameters and the edit are in m/s — the readout at the release and the log in cm/s,
  //     the edit sent in m/s (readout = 100 × sent)
  {
    await page.fill(".pg-manip input[type=number]", "1");
    await page.press(".pg-manip input[type=number]", "Enter");
    await cmd(id, "scene", { op: "add", type: "cloud", values: { x: -2, y: -2, n: 12, spread: 0.4 } });
    await sleep(1200);
    const cl = await page.evaluate(() => window.__lfManip.objects().filter((o) => o.type === "cloud").at(-1)?.id);
    const q = cl ? await scr3(page, cl) : null;
    if (!q) check(`${tag} velocity_display: the cloud is on the screen`, false, { cl });
    else {
      const nc = edits(await record(id), cl).length;
      await dragPath(page, q, [q[0] + 60, q[1] - 25], { n: 10, dtMs: 16, shift: true });
      const shown = await page.evaluate(() => window.__lfManip.released());
      await idle(page); await sleep(400);
      const rc = await record(id), ec = edits(rc, cl).at(-1), sent = ec ? [ec.args.values.vx, ec.args.values.vy] : [];
      const evc = rc.filter((m) => m.type === "event" && m.name === "edit" && m.args.id === cl).at(-1);
      const cms = tr("cm/s"), ms = tr("m/s");
      const nums = (new RegExp(`v = \\(([^)]*)\\) ${esc(cms)}`).exec(shown) || [, ""])[1].split(";").map((x) => Number(x.trim().replace(/[\s\u202f]/g, "").replace("−", "-").replace(",", ".")));
      const okNums = nums.length === 2 && sent.length === 2 && nums.every((x, i) => Math.abs(x - 100 * sent[i]) <= 0.01 * Math.max(1, Math.abs(x)) + 0.06);
      check(`${tag} velocity_display: readout and log in cm/s, the edit in m/s (readout = 100 × sent)`,
        edits(rc, cl).length === nc + 1 && okNums && hasMsgid(evc?.text, "throw: v = {vec}") && JSON.stringify(evc?.text).includes('"cm/s"')
          && !shown.replace(cms, "").includes(ms),
        { shown, sent, log: tr(evc?.text) });
    }
  }
  await page.click(".pg-manip .pg-auto");
  // a throw seen in the middle (for the screenshot), then cancelled with Esc
  {
    const q = await scr3(page, "o1");
    await page.mouse.move(q[0], q[1]); await page.mouse.down(); await page.keyboard.down("Shift");
    for (let k = 1; k <= 8; k++) { await page.mouse.move(q[0] - 9 * k, q[1] + 6 * k); await sleep(12); }
    await page.screenshot({ path: `${OUT}/manip_toy_${tag}_throwing.png` });
    await page.keyboard.press("Escape"); await page.mouse.up(); await page.keyboard.up("Shift");
    await idle(page);
  }

  // 5. a refusal: dragged out of the region — the world's text, the ghost snaps back, nothing changed
  const pBefore = await page.evaluate(() => window.__lfManip.at("o1"));
  const s1 = await scr3(page, "o1");
  const target = await page.evaluate(([x0, y0]) => {  // a screen point whose drag-plane point is outside |c| <= 5
    const sc = document.querySelector(".s3d-view").__scene3d, p0 = window.__lfManip.at("o1"), n = sc.viewDir();
    const r = sc.el.querySelector("canvas").getBoundingClientRect();
    for (let k = 10; k < 2000; k += 10) {
      const x = x0 + k, y = y0;
      if (x > r.right - 6) break;
      const ray = sc.rayAt(x, y), den = ray.dir[0] * n[0] + ray.dir[1] * n[1] + ray.dir[2] * n[2];
      const t = ((p0[0] - ray.origin[0]) * n[0] + (p0[1] - ray.origin[1]) * n[1] + (p0[2] - ray.origin[2]) * n[2]) / den;
      const q = ray.origin.map((o, i) => o + t * ray.dir[i]);
      if (Math.max(...q.map(Math.abs)) > 5.4) return [x, y];
    }
    return null;
  }, s1);
  const nErr0 = (await record(id)).filter((m) => m.type === "error").length;
  await dragPath(page, s1, target);
  const snapped = await waitFor(() => page.evaluate(() => window.__lfManip.snapping()), 8000, 30);
  const toast = await toastText(page);
  await idle(page);
  await sleep(400);
  const rec5 = await record(id), err5 = rec5.filter((m) => m.type === "error");
  const pAfter = await page.evaluate(() => window.__lfManip.at("o1"));
  const outside = tr("“{label}”: the point is outside the toy's region (|{axes}| > {half:g} m)", { label: "", axes: "", half: 5 }).split(":")[1].split("(")[0].trim();
  check(`${tag} refusal: the world's text shown, ghost snaps back, object unchanged`, target && err5.length === nErr0 + 1 && hasMsgid(err5.at(-1).text, "the point is outside the toy's region")
    && toast.includes(outside) && snapped && pAfter.every((v, i) => Math.abs(v - pBefore[i]) < 1e-12)
    && !(await page.evaluate(() => document.querySelector(".s3d-view").__scene3d.markers().includes("ghost"))),
  { error: tr(err5.at(-1)?.text), toast: toast.slice(0, 160) });

  // 6. Esc cancels a drag: no edit
  const s3p = await scr3(page, "o3");
  const n6 = edits(await record(id), "o3").length;
  await page.mouse.move(s3p[0], s3p[1]); await page.mouse.down();
  for (let k = 1; k <= 6; k++) { await page.mouse.move(s3p[0] + 8 * k, s3p[1] + 5 * k); await sleep(16); }
  await page.keyboard.press("Escape");
  await page.mouse.up();
  await idle(page); await sleep(500);
  check(`${tag} Esc cancels: no edit`, edits(await record(id), "o3").length === n6);

  // 7. a drag in the window of the plane z = 0: the probe lands under the pointer (x, y only)
  const w3 = await scrWin(page, "o3");
  const tw = [w3[0] + 45, w3[1] + 30];
  const n7 = edits(await record(id), "o3").length;
  await dragPath(page, w3, tw);
  await idle(page); await sleep(500);
  const e7 = edits(await record(id), "o3"), P7 = await winPoint(page, tw[0], tw[1]), at7 = await page.evaluate(() => window.__lfManip.at("o3"));
  const unit = await page.evaluate(() => [...document.querySelectorAll(".s3d-windows")].map((e) => e.__slices).filter(Boolean).find((w) => w.helper(1)).helper(1).unitPx);
  check(`${tag} window drag: one edit {x, y}, lands under the pointer`, e7.length === n7 + 1 && Object.keys(e7.at(-1).args.values).sort().join() === "x,y"
    && Math.hypot(at7[0] - P7[0], at7[1] - P7[1]) * unit < 2.5, { values: e7.at(-1)?.args.values, P7, at7 });
  const ring7 = await page.evaluate(() => window.__lfManip.ringInWindow(1)), r7 = await page.evaluate(() => [...document.querySelectorAll(".s3d-windows")].map((e) => e.__slices).filter(Boolean).find((w) => w.helper(1)).helper(1).el.getBoundingClientRect().toJSON());
  check(`${tag} window drag: the selection ring follows the object`, ring7 && Math.hypot(r7.left + ring7[0] - tw[0], r7.top + ring7[1] - tw[1]) < 2.5, { ring7, tw });

  // 8. axis-bound handles: "y" (wall) in 3-D along y only, Shift ignored; 2 (mirror) across the window's plane refused
  //    there and moved along z in 3-D; "0" (screen) in the window along x
  const objs = await page.evaluate(() => window.__lfManip.objects());
  const wall = objs.find((o) => o.type === "wall").id, mirror = objs.find((o) => o.type === "mirror").id, screen = objs.find((o) => o.type === "screen").id;
  const aw0 = await page.evaluate((i) => window.__lfManip.at(i), wall);
  const sw = await scr3(page, wall);
  const d8 = await dragPath(page, sw, [sw[0] + 30, sw[1] + 45], { shift: true,
    before: () => page.evaluate(() => ({ axis: document.querySelector(".s3d-view").__scene3d.markerSpec("ghost")?.axis, text: window.__lfManip.text() })) });
  await idle(page); await sleep(500);
  const e8 = edits(await record(id), wall).at(-1), aw1 = await page.evaluate((i) => window.__lfManip.at(i), wall);
  check(`${tag} axis "y": only the coordinate sent, moved along y, Shift ignored, axis shown`, e8 && Object.keys(e8.args.values).join() === "position"
    && aw1[0] === aw0[0] && aw1[2] === aw0[2] && Math.abs(aw1[1] - e8.args.values.position) < 1e-12 && aw1[1] !== aw0[1] && d8.mid.axis && d8.mid.text.includes(tr("(there is no throw along an axis)")),
  { values: e8?.args.values, text: d8.mid.text });
  const mw = await scrWin(page, mirror);
  const nm = edits(await record(id), mirror).length;
  if (mw) {
    await dragPath(page, mw, [mw[0] + 40, mw[1] - 20]);
    await sleep(400);
    check(`${tag} axis 2 across the window's plane: refused there with the reason, no edit`, edits(await record(id), mirror).length === nm && (await toastText(page)).toLowerCase().includes(tr("the axis {axis} crosses the plane of this window: drag “{label}” in the 3-D scene or in another window", { axis: "z", label: "" }).split(":")[0].toLowerCase()));
  } else check(`${tag} axis 2 across the window's plane: the mirror is in the window`, false);
  const sm = await scr3(page, mirror), am0 = await page.evaluate((i) => window.__lfManip.at(i), mirror);
  await dragPath(page, sm, [sm[0] + 60, sm[1] + 10]);
  await idle(page); await sleep(500);
  const em = edits(await record(id), mirror).at(-1), am1 = await page.evaluate((i) => window.__lfManip.at(i), mirror);
  check(`${tag} axis 2 (number) in 3-D: along z only`, em && Object.keys(em.args.values).join() === "position" && am1[0] === am0[0] && am1[1] === am0[1] && am1[2] !== am0[2], { values: em?.args.values });
  const ws = await scrWin(page, screen), as0 = await page.evaluate((i) => window.__lfManip.at(i), screen);
  await dragPath(page, ws, [ws[0] + 35, ws[1] + 25]);
  await idle(page); await sleep(500);
  const es = edits(await record(id), screen).at(-1), as1 = await page.evaluate((i) => window.__lfManip.at(i), screen), Ps = await winPoint(page, ws[0] + 35, ws[1] + 25);
  check(`${tag} axis "0" (number as text) in the window: along x only, under the pointer`, es && Object.keys(es.args.values).join() === "position"
    && as1[1] === as0[1] && as1[2] === as0[2] && Math.abs(as1[0] - Ps[0]) * unit < 2.5, { values: es?.args.values, Ps });

  // 9. Delete removes the selected object
  const q9 = await scr3(page, "o2");
  await page.mouse.click(q9[0], q9[1]); await sleep(300);
  await page.keyboard.press("Delete");
  const gone = await waitFor(async () => (await record(id)).some((m) => m.type === "command" && m.cmd === "scene" && m.args.op === "remove" && m.args.id === "o2")
    && !(await page.evaluate(() => window.__lfManip.objects().some((o) => o.id === "o2"))), 15000);
  check(`${tag} Delete removes the selected object`, !!gone);

  // 10. the read-only history: a drag there edits nothing and says why
  await cmd(id, "play"); await sleep(1500); await cmd(id, "pause"); await sleep(800);
  await page.evaluate(() => window.__lfPlayer.goTo(1)); await sleep(800);
  const q10 = await scr3(page, "o1");
  const n10 = edits(await record(id)).length;
  if (q10) await dragPath(page, q10, [q10[0] + 50, q10[1] + 40]);
  await sleep(600);
  check(`${tag} read-only history: no edit, the reason shown`, q10 && edits(await record(id)).length === n10 && (await toastText(page)).includes(tr("You are looking at the experiment's past: slices and the scene are changed at the end of the record (⏭).")), { toast: (await toastText(page)).slice(0, 120) });
  await page.evaluate(() => window.__lfPlayer.goTo(1e9)); await sleep(800);
  await page.screenshot({ path: `${OUT}/manip_toy_${tag}_after.png` });

  // 11. "New world" with "carry the scene over" (on by default): the plane z = 0 world takes what it can and names the rest
  const before11 = await page.evaluate(() => window.__lfManip.objects());
  await page.click(`h4:has-text("${tr("New world: laws and initial conditions").split(":")[0]}")`);
  await sleep(300);
  const box = await page.evaluate(() => { const c = document.querySelector(".pg-carry input"); return c ? { checked: c.checked, disabled: c.disabled } : null; });
  await page.evaluate(() => {
    const sel = [...document.querySelectorAll(".field[data-pid=ndim] select")][0];
    sel.value = "2";
    sel.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await page.click(`button:has-text("${tr("▶ Start a new world").replace("▶ ", "")}")`);
  const w2 = await waitFor(async () => (await record(id)).filter((m) => m.type === "header").length >= 2, 30000);
  await sleep(1500);
  const rec11 = await record(id), note = rec11.filter((m) => m.type === "notice" && hasMsgid(m.text, "The scene was carried into the new world")).at(-1);
  const head2 = rec11.filter((m) => m.type === "header").at(-1);
  const after11 = await page.evaluate(() => window.__lfManip.objects());
  const expectGone = before11.filter((o) => o.type === "mirror" || (o.type === "particle" && o.values.z)).map((o) => o.label);
  const noteText = note ? tr(note.text) : "";
  check(`${tag} "carry the scene over": on by default, the 2-D world takes the rest and names what it refuses`,
    box && box.checked && !box.disabled && w2 && head2.params.scene.carry === true && note && hasMsgid(note.text, "not carried: {items}")
    // what went how (review LB1-F5): the particles with their state, the probe by its parameters, the world's own state
    && (!after11.some((o) => o.type === "particle") || hasMsgid(note.text, "with their state — {names}"))
    && hasMsgid(note.text, "by their parameters (no state of their own) — {names}")
    && hasMsgid(note.text, "the world's state carried over") && Array.isArray(note.carry?.objects)
    && expectGone.every((l) => noteText.includes(tr(l))) && after11.length === before11.length - expectGone.length
    && (await toastText(page)).toLowerCase().includes(tr("not carried: {items}", { items: "" }).trim().slice(0, -1).toLowerCase()),
  { note: noteText.slice(0, 300), before: before11.map((o) => tr(o.label)), after: after11.map((o) => tr(o.label)) });
  await page.screenshot({ path: `${OUT}/manip_toy_${tag}_carried.png` });
  check(`${tag} no page errors`, !errs.length, { errs: errs.slice(0, 5) });
  await page.close();
  await post(`/api/runs/${id}/stop`, {});
}

// --- the worlds p01–p04: a drag and a throw of objects with handles ---------------------------------------------------
const PRESET = { p01_gravity: "inner", p02_quantum: "trap", p03_molecules: "piston", p04_fluids: "cavity" };
async function world(viz, [W, H]) {
  const tag = `${viz} ${W}x${H}`, errs = [];
  const r = await post("/api/runs", { viz, preset: PRESET[viz], seed: 3 });
  if (!r.id) { check(`${tag}: run started`, false, { r }); return; }
  const id = r.id;
  await waitFor(async () => (await get(`/api/runs/${id}`)).state === "running", 120000);
  await sleep(1500);
  const page = await br.newPage({ viewport: { width: W, height: H } });
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message} ${(e.stack || "").split("\n").slice(1, 3).join(" ")}`.slice(0, 400)));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`console: ${m.text()}`.slice(0, 300)); });
  await openRun(page, id);
  await page.screenshot({ path: `${OUT}/manip_${viz}_${W}x${H}_before.png` });
  const objs = await page.evaluate(() => window.__lfManip.objects().map((o) => ({ ...o, h: window.__lfManip.handles(o.type), at: window.__lfManip.at(o.id) })));
  const movable = objs.filter((o) => o.h && o.h.position && o.at);
  if (!objs.some((o) => o.h)) {
    console.log(JSON.stringify({ name: `${tag}: no handles declared in this world's palette (yet)`, skipped: true }));
    await page.close(); await post(`/api/runs/${id}/stop`, {});
    return;
  }
  check(`${tag}: objects with a position handle report at[id]`, movable.length > 0, { types: [...new Set(objs.map((o) => `${o.type}:${!!o.h}:${!!o.at}`))] });
  let did = 0;
  for (const o of movable.slice(0, 3)) {
    let from = await scr3(page, o.id), where = "3d";
    if (!from) { from = await scrWin(page, o.id); where = "window"; }
    if (!from) continue;
    const throwIt = Array.isArray(o.h.position) && Array.isArray(o.h.velocity) && did === 1;
    const n0 = edits(await record(id), o.id).length, nErr = (await record(id)).filter((m) => m.type === "error").length;
    const d = await dragPath(page, from, [from[0] + 40, from[1] + 25], { shift: throwIt, before: () => page.evaluate(() => window.__lfManip.text()) });
    const snapped = await waitFor(() => page.evaluate(() => window.__lfManip.snapping()), 6000, 30);
    await idle(page); await sleep(600);
    const rec = await record(id), e = edits(rec, o.id);
    const applied = rec.some((m) => m.type === "event" && m.name === "edit" && m.args.id === o.id && e.length > n0);
    const refused = rec.filter((m) => m.type === "error").length > nErr;
    const vals = e.at(-1)?.args.values || {};
    const keys = Array.isArray(o.h.position) ? o.h.position : [o.h.position.param];
    if (applied && where === "window") {  // the window's selection ring follows the object to where it was put
      const ring = await page.evaluate(() => window.__lfManip.ringInWindow(1)), now = await scrWin(page, o.id);
      const r = await page.evaluate(() => { const c = [...document.querySelectorAll(".s3d-windows")].map((e) => e.__slices).filter(Boolean).find((w) => w.helper(1)); return c ? c.helper(1).el.getBoundingClientRect().toJSON() : null; });
      check(`${tag}: the window's selection ring follows "${tr(o.label)}"`, ring && now && Math.hypot(r.left + ring[0] - now[0], r.top + ring[1] - now[1]) < 1.5, { ring, now });
    }
    check(`${tag}: ${throwIt ? "throw" : "drag"} "${tr(o.label)}" (${o.type}) in the ${where}: one edit, ${applied ? "applied" : refused ? "refused (ghost snapped back)" : "?"}`,
      e.length === n0 + 1 && keys.every((k) => k in vals) && (applied || (refused && snapped)) && (!throwIt || o.h.velocity.every((k) => k in vals)),
      { values: vals, text: d.mid, error: refused ? tr(rec.filter((m) => m.type === "error").at(-1).text).slice(0, 200) : undefined });
    did++;
  }
  if (!did) check(`${tag}: an object with a handle could be reached on the screen`, false);
  await page.screenshot({ path: `${OUT}/manip_${viz}_${W}x${H}_after.png` });
  check(`${tag}: no page errors`, !errs.length, { errs: errs.slice(0, 5) });
  await page.close();
  await post(`/api/runs/${id}/stop`, {});
}

for (const size of SIZES) {
  for (const w of WORLDS) {
    try { if (w === "p99_toy") await toy(size); else await world(w, size); }
    catch (e) { check(`${w} ${size.join("x")}: script error`, false, { error: String(e.stack || e).slice(0, 400) }); }
  }
}
await br.close();
const failed = checks.filter((c) => !c.ok).length;
console.log(failed ? `${failed} of ${checks.length} failed` : `all passed (${checks.length})`);
process.exit(failed ? 1 : 0);
