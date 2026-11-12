// p03 after processing LB1 reviews (proc_p03): a throw by Shift+drag (X4), a box changed over a time (P3), a scene carried
// into a new world with its atoms (F5). Screenshots and the texts the page shows; one JSON line per check.
import { chromium } from "playwright";
const port = process.argv[2] || "8614";
const base = `http://127.0.0.1:${port}`;
const OUT = "/pw/shots";
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
async function waitFor(fn, ms = 20000, step = 150) { const t0 = Date.now(); for (;;) { const v = await fn(); if (v) return v; if (Date.now() - t0 > ms) return null; await sleep(step); } }
const check = (name, ok, d = {}) => console.log(JSON.stringify({ name, ok: !!ok, ...d }));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const errs = [];
async function open(id) {
  const page = await br.newPage({ viewport: { width: 1600, height: 1000 } });
  page.on("pageerror", (e) => errs.push(String(e)));
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && window.__lfManip, null, { timeout: 120000 });
  await sleep(1500);
  return page;
}
const scr3 = (page, oid) => page.evaluate((id) => {
  const v = document.querySelector(".s3d-view"), sc = v && v.__scene3d, p = window.__lfManip.at(id);
  if (!sc || !p) return null;
  const q = sc.project(p);
  return [q.x, q.y];
}, oid);
const eventsText = (page) => page.evaluate(() => document.body.innerText);

// A. the throw (X4)
{
  const scene = { format: "lfscene", version: 1, objects: [{ type: "gas", label: "Аргон", values: { n: 60, T: 300.0, x: 10, y: 10, sx: 5, sy: 5 } }] };
  const r = await post("/api/runs", { viz: "p03_molecules", params: { dim: "2d", Lx: 20.0, Ly: 20.0, boundary: "periodic", scene }, seed: 3 });
  const id = r.id;
  await waitFor(async () => (await get(`/api/runs/${id}`)).state === "running", 120000);
  const page = await open(id);
  const oid = (await page.evaluate(() => window.__lfManip.objects()))[0].id;
  const q = await scr3(page, oid);
  await page.mouse.move(q[0], q[1]); await page.mouse.down(); await page.keyboard.down("Shift");
  let mid = null;
  for (let k = 1; k <= 14; k++) { await page.mouse.move(q[0] + 10 * k, q[1] + 3 * k); if (k === 11) mid = await page.evaluate(() => window.__lfManip.text()); if (k < 14) await sleep(16); }
  await page.mouse.up(); await page.keyboard.up("Shift");
  await page.screenshot({ path: `${OUT}/x4_throw_mid.png` });
  await sleep(2500);
  const rec = await record(id);
  const ed = rec.filter((m) => m.type === "command" && m.cmd === "scene" && m.args.op === "edit").at(-1);
  const error = rec.filter((m) => m.type === "error").at(-1);
  const sc = rec.filter((m) => m.type === "scene").at(-1);
  const vx = sc.objects[0].values.vx, vy = sc.objects[0].values.vy;
  const ev = rec.filter((m) => m.type === "event" && m.name === "edit").at(-1);
  await page.screenshot({ path: `${OUT}/x4_throw_after.png` });
  const sp = Math.hypot(vx, vy);
  check("X4: a flick throws within 500 m/s, in m/s in the object, no refusal", ed && !error && sp > 0 && sp <= 500.0001,
        { readout: mid, sent: ed && ed.args.values, vx, vy, event: ev && ev.text, error: error && error.text });
  await page.close(); await post(`/api/runs/${id}/stop`, {});
}

// B. the box over a time (P3)
{
  const scene = { format: "lfscene", version: 1, objects: [{ type: "gas", label: "Аргон", values: { n: 200, T: 300.0 } }] };
  const r = await post("/api/runs", { viz: "p03_molecules", params: { dim: "2d", Lx: 12.0, Ly: 12.0, boundary: "walls", scene }, seed: 4 });
  const id = r.id;
  await waitFor(async () => (await get(`/api/runs/${id}`)).state === "running", 120000);
  const page = await open(id);
  await cmd(id, "step", { dt: 2e-12 });
  await sleep(1000);
  await page.screenshot({ path: `${OUT}/p3_box_before.png` });
  await cmd(id, "set", { values: { box_time_ps: 20.0, Lx: 8.0 } });
  await cmd(id, "step", { dt: 10e-12 });
  await sleep(2000);
  const midBox = await page.evaluate(() => window.__lfPlayer.frames && document.body.innerText.includes("аффинно за 20 пс"));
  await page.screenshot({ path: `${OUT}/p3_box_mid.png` });
  await cmd(id, "step", { dt: 12e-12 });
  await sleep(2500);
  await page.screenshot({ path: `${OUT}/p3_box_end.png` });
  const rec = await record(id);
  const fr = rec.filter((m) => m.type === "frame");
  const boxes = fr.map((m) => m.box_nm[0]);
  const evs = rec.filter((m) => m.type === "event" && m.text).map((m) => m.text);
  const start = evs.find((t) => t.includes("аффинно за 20 пс")), end = evs.find((t) => t.includes("изменение ящика закончено"));
  const txt = await eventsText(page);
  check("P3: the box goes 12 → 8 nm over 20 ps, frames in between, start and end said, shown on the page",
        start && end && boxes.some((b) => b > 8.01 && b < 11.99) && Math.abs(boxes.at(-1) - 8.0) < 1e-9 && txt.includes("изменение ящика закончено"),
        { start, end, intermediate: boxes.filter((b) => b > 8.01 && b < 11.99).length, last: boxes.at(-1), midShown: midBox });
  await page.close(); await post(`/api/runs/${id}/stop`, {});
}

// C. the scene carried with its atoms (F5)
{
  const scene = { format: "lfscene", version: 1, objects: [{ type: "gas", label: "Аргон", values: { n: 3000, T: 300.0 } }] };
  const r = await post("/api/runs", { viz: "p03_molecules", params: { dim: "3d", Lx: 20.0, Ly: 20.0, Lz: 20.0, boundary: "periodic", scene }, seed: 5 });
  const id = r.id;
  await waitFor(async () => (await get(`/api/runs/${id}`)).state === "running", 120000);
  const page = await open(id);
  await cmd(id, "step", { dt: 1e-13 });
  await sleep(1500);
  let rec = await record(id);
  const before = rec.filter((m) => m.type === "frame").at(-1);
  const hdr = rec.filter((m) => m.type === "header").at(-1);
  await cmd(id, "new_world", { params: { dim: "3d", Lx: 20.0, Ly: 20.0, Lz: 20.0, boundary: "walls" }, carry: true });
  await waitFor(async () => (await record(id)).filter((m) => m.type === "header").length > 1, 60000);
  await sleep(3000);
  rec = await record(id);
  const note = rec.filter((m) => m.type === "notice" && m.carry).at(-1);
  const first = rec.filter((m) => m.type === "frame" && m.t >= before.t).at(-1);
  await page.screenshot({ path: `${OUT}/f5_carry_notice.png` });
  // the kinetic energy kept: T changes only by the degrees of freedom (periodic: 3N - 3, walls: 3N); e changes by the pairs
  // across the periodic faces that the walls cut
  const N = 3000, Texp = before.meas.T * (3 * N - 3) / (3 * N);
  check("F5: the gas carried with its atoms: the notice says «с состоянием», the same kinetic energy at the same t",
        note && note.carry.objects[0].how === "state" && first && first.t === before.t && Math.abs(first.meas.T - Texp) < 1e-9 * Texp,
        { notice: note && note.text.slice(0, 400), e: [before.meas.e, first && first.meas.e], T: [before.meas.T, first && first.meas.T], Texp, t: [before.t, first && first.t] });
  await page.close(); await post(`/api/runs/${id}/stop`, {});
}
check("no page errors", !errs.length, { errs });
await br.close();
