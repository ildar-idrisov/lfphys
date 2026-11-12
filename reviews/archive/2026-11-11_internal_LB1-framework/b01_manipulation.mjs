// b01: direct manipulation in Chromium against the PRIVATE server (port given; never 8479), toy section p99_toy.
// (1) a throw's units at known playback rates: the same Shift-drag (same pixels, same timing) at rate 0.5 and at rate 4
//     with the throw scale set to 1 by hand: |v| must scale as 1/rate (ratio 8), and match
//     Δx_world / (Δt_wall × rate) of the pointer's last 100 ms; the readout's unit;
// (2) a refused drag (outside the toy's ±5 m): the Russian text, the ghost snaps back, the object's state unchanged
//     (its `at` follows the unchanged straight line), the refused edit in the record;
// (3) the selection survives frames while playing (the ring follows the object);
// (4) the read-only history: Delete on a selected object while the cursor is in the past sends nothing.
// Run: docker run --rm --init --shm-size=2g --network host -v <scratch>/lbrf/pw:/pw -v <review>:/out -w /pw
//      mcr.microsoft.com/playwright:v1.58.2-jammy sh -c "cp /out/b01_manipulation.mjs /pw/ && node /pw/b01_manipulation.mjs 8601"
import { chromium } from "playwright";

const port = process.argv[2] || "8601";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cmd = (id, c, a) => post(`/api/runs/${id}/command`, { cmd: c, args: a || {} });
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
const results = [];
const check = (name, ok, detail = {}) => { results.push({ name, ok: !!ok, ...detail }); console.log(JSON.stringify({ name, ok: !!ok, ...detail })); };

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const r = await post("/api/runs", { viz: "p99_toy", preset: "two", seed: 3 });
const id = r.id;
for (let i = 0; i < 100 && (await get(`/api/runs/${id}`)).state !== "running"; i++) await sleep(200);
const page = await br.newPage({ viewport: { width: 1400, height: 900 } });
const errs = [];
page.on("pageerror", (e) => errs.push(e.message));
await page.goto(`${base}/run?id=${id}`);
await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && window.__lfManip, null, { timeout: 120000 });
await sleep(1500);
const scr3 = (oid) => page.evaluate((oid) => {
  const v = document.querySelector(".s3d-view"), sc = v.__scene3d, p = window.__lfManip.at(oid);
  const q = sc.project(p); return [q.x, q.y];
}, oid);
async function dragPath(from, to, n, dtMs, shift) {
  await page.mouse.move(from[0], from[1]); await page.mouse.down();
  if (shift) await page.keyboard.down("Shift");
  let t0 = 0; let text = "";
  for (let k = 1; k <= n; k++) {
    await page.mouse.move(from[0] + (to[0] - from[0]) * k / n, from[1] + (to[1] - from[1]) * k / n);
    if (k === 1) t0 = Date.now();
    if (k === n - 2) text = await page.evaluate(() => window.__lfManip.text());
    if (k < n) await sleep(dtMs);
  }
  const T = Date.now() - t0;
  await page.mouse.up(); if (shift) await page.keyboard.up("Shift");
  return { T, text };
}
const idle = async () => { for (let i = 0; i < 100; i++) { if (await page.evaluate(() => !window.__lfManip.pending() && !window.__lfManip.snapping() && !window.__lfManip.dragging())) return; await sleep(100); } };

// (1) throw units at two rates, scale 1
await page.fill(".pg-manip input[type=number]", "1"); await page.press(".pg-manip input[type=number]", "Enter");
const out1 = [];
for (const rate of [0.5, 4]) {
  await cmd(id, "speed", { value: rate }); await sleep(700);
  const shown = await page.evaluate(() => window.__lfPlayer && document.querySelector("#speedv").textContent);
  const p0 = await page.evaluate(() => window.__lfManip.at("o2"));
  const q = await scr3("o2");
  const n0 = edits(await record(id), "o2").length;
  const d = await dragPath(q, [q[0] + 120, q[1] - 20], 14, 16, true);
  await idle(); await sleep(500);
  const e = edits(await record(id), "o2").at(-1), v = e.args.values;
  const vel = [v.vx, v.vy, v.vz], disp = ["x", "y", "z"].map((k, i) => v[k] - p0[i]);
  // the pointer moved at a constant pace: its world velocity = the displacement of moves 1..14 over T (13 intervals)
  const handV = disp.map((x) => x * 13 / 14 / (d.T / 1000));
  const exp = handV.map((x) => x / rate);
  out1.push({ rate, speedLabel: shown, nEdits: edits(await record(id), "o2").length - n0, vel, expected: exp, readout: d.text,
              ratio: Math.hypot(...vel) / Math.hypot(...exp) });
  // put o2 back where it was, at rest along y, so that the second drag starts from the same place
  await cmd(id, "scene", { op: "edit", id: "o2", values: { x: p0[0], y: p0[1], z: p0[2], vx: -0.5, vy: 0, vz: 0 } });
  await sleep(700);
}
const s0 = Math.hypot(...out1[0].vel), s1 = Math.hypot(...out1[1].vel);
check("throw: |v| at rate 0.5 / |v| at rate 4 = 8 (velocity in world length per world time)", Math.abs(s0 / s1 / 8 - 1) < 0.25, { s0, s1, ratio: s0 / s1, runs: out1 });
check("throw: each |v| within 35 % of Δx_world/(Δt_wall·rate) of the pointer", out1.every((o) => o.ratio > 0.65 && o.ratio < 1.35), { ratios: out1.map((o) => o.ratio) });
check("throw: readout states the unit (м/с) and the scale", out1.every((o) => /м\/с/.test(o.readout) && /×1/.test(o.readout)), { readouts: out1.map((o) => o.readout) });
await cmd(id, "speed", { value: 1 }); await sleep(400);

// (2) a refused drag: o1 dragged far outside the toy's region (|x| > 5 m)
const a0 = await page.evaluate(() => window.__lfManip.at("o1"));
const st0 = (await record(id)).filter((m) => m.type === "frame").at(-1).at.o1;
const qa = await scr3("o1");
const nE = edits(await record(id), "o1").length, nErr = (await record(id)).filter((m) => m.type === "error").length;
await dragPath(qa, [qa[0] + 600, qa[1]], 10, 16, false);
await sleep(150);
const snapping = await page.evaluate(() => window.__lfManip.snapping() || window.__lfManip.pending());
await idle(); await sleep(600);
const rec2 = await record(id);
const err = rec2.filter((m) => m.type === "error").slice(nErr);
const toast = await page.evaluate(() => [...document.querySelectorAll(".toast")].map((t) => t.textContent).join(" | "));
await cmd(id, "step", { dt: 0.2 }); await sleep(800);
const fr = (await record(id)).filter((m) => m.type === "frame").at(-1);
const want = [st0[0] + 1.0 * 0.2, st0[1], st0[2]];  // o1 moves at vx = 1 m/s, unchanged by the refused drag
check("refusal: one edit sent and refused in Russian, the toast shows it, the ghost goes back",
  edits(rec2, "o1").length === nE + 1 && err.length === 1 && /вне области/.test(err[0].text) && /вне области/.test(toast) && snapping,
  { err: err.map((m) => m.text), toast: toast.slice(0, 200), snapping });
check("refusal: the object's state is unchanged (it goes on along its line)", Math.hypot(fr.at.o1[0] - want[0], fr.at.o1[1] - want[1], fr.at.o1[2] - want[2]) < 1e-9,
  { at: fr.at.o1, want, before: a0 });

// (3) the selection survives frames while playing
const q1 = await scr3("o1");
await page.mouse.click(q1[0], q1[1]); await sleep(300);
await cmd(id, "play"); await sleep(2500);
const sel = await page.evaluate(() => ({ sel: window.__lfManip.selected(), at: window.__lfManip.at("o1"),
  ring: document.querySelector(".s3d-view").__scene3d.markerSpec("sel") }));
await cmd(id, "pause"); await sleep(500);
check("selection survives frames, the ring follows the object", sel.sel === "o1" && sel.ring && Math.hypot(...sel.ring.pos.map((v, i) => v - sel.at[i])) < 0.2,
  { sel: sel.sel, ring: sel.ring && sel.ring.pos, at: sel.at });

// (4) the read-only history: Delete with the cursor in the past
await page.click("#tostart"); await sleep(800);
const q2 = await scr3("o2");
await page.mouse.click(q2[0], q2[1]); await sleep(300);
const nRem = (await record(id)).filter((m) => m.type === "command" && m.args && m.args.op === "remove").length;
await page.keyboard.press("Delete"); await sleep(800);
const nRem2 = (await record(id)).filter((m) => m.type === "command" && m.args && m.args.op === "remove").length;
const toast4 = await page.evaluate(() => [...document.querySelectorAll(".toast")].map((t) => t.textContent).join(" | "));
check("read-only history: Delete sends nothing and says why", nRem2 === nRem && /прошлое/.test(toast4), { toast: toast4.slice(0, 200) });
check("no page errors", !errs.length, { errs });
await page.screenshot({ path: "/out/b01_manipulation_end.png" });
await br.close();
const failed = results.filter((x) => !x.ok).length;
console.log(failed ? `${failed} failed` : "all passed");
