// Review LB1-p02-ux, Part B: shared helpers of the browser tours (Playwright 1.58.2, Chromium with SwiftShader).
// Against the PRIVATE server only (port given on the command line; never the shared one on 8479).
import { chromium } from "playwright";
import { mkdirSync, writeFileSync, appendFileSync } from "node:fs";

export const port = process.env.PORT || "8603";
export const OUT = process.env.OUT || "/out";
mkdirSync(OUT, { recursive: true });
export const base = `http://127.0.0.1:${port}`;
export const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
export const get = async (u) => (await fetch(base + u)).json();
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
export const cmd = (id, c, a) => post(`/api/runs/${id}/command`, { cmd: c, args: a || {} });
export const LOG = process.env.LOG || `${OUT}/b_log.txt`;
export function log(...a) { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); console.log(s); appendFileSync(LOG, s + "\n"); }

export async function record(id) {
  const buf = new Uint8Array(await (await fetch(`${base}/api/runs/${id}/stream`)).arrayBuffer());
  const dv = new DataView(buf.buffer), out = [], dec = new TextDecoder();
  for (let off = 8; off + 4 <= buf.length;) {
    const n = dv.getUint32(off, true), m = off + 4, jl = dv.getUint32(m, true);
    out.push(JSON.parse(dec.decode(buf.subarray(m + 4, m + 4 + jl))));
    off = m + n;
  }
  return out;
}
export async function waitFor(fn, ms = 20000, step = 150) {
  const t0 = Date.now();
  for (;;) { const v = await fn(); if (v) return v; if (Date.now() - t0 > ms) return null; await sleep(step); }
}
export async function browser() {
  return chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
}
export async function newRun(viz, preset, params) {
  const r = await post("/api/runs", { viz, preset, params, seed: 3 });
  if (!r.id) { log("newRun failed", r); return null; }
  await waitFor(async () => (await get(`/api/runs/${r.id}`)).state === "running", 120000, 300);
  return r.id;
}
export async function openRun(page, id) {
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && window.__lfManip, null, { timeout: 180000 });
  await sleep(1500);
}
export const scr3 = (page, oid) => page.evaluate((id) => {
  const v = document.querySelector(".s3d-view"), sc = v && v.__scene3d, p = window.__lfManip.at(id);
  if (!sc || !p || !v.offsetParent) return null;
  const q = sc.project(p), r = v.querySelector("canvas").getBoundingClientRect();
  return q.inside && q.x > r.left + 4 && q.x < r.right - 4 && q.y > r.top + 4 && q.y < r.bottom - 4 ? [q.x, q.y] : null;
}, oid);
export const scrWin = (page, oid, k = 1) => page.evaluate(([id, k]) => {
  const ws = [...document.querySelectorAll(".s3d-windows")].map((e) => e.__slices).filter(Boolean);
  const p = window.__lfManip.at(id);
  for (const W of ws) {
    const h = W.helper(k); if (!h || !p) continue;
    const [x, y] = h.toCanvas(p), r = h.el.getBoundingClientRect();
    if (x > 2 && y > 2 && x < r.width - 2 && y < r.height - 2) return [r.left + x, r.top + y];
  }
  return null;
}, [oid, k]);
export const camera = (page) => page.evaluate(() => document.querySelector(".s3d-view").__scene3d.cameraState());
export async function dragPath(page, from, to, { n = 10, dtMs = 16, shift = false, before = null } = {}) {
  await page.mouse.move(from[0], from[1]);
  await page.mouse.down();
  if (shift) await page.keyboard.down("Shift");
  let mid = null;
  for (let k = 1; k <= n; k++) {
    await page.mouse.move(from[0] + (to[0] - from[0]) * k / n, from[1] + (to[1] - from[1]) * k / n);
    if (k === n - 3 && before) mid = await before();
    if (dtMs && k < n) await sleep(dtMs);
  }
  await page.mouse.up();
  if (shift) await page.keyboard.up("Shift");
  return mid;
}
export const toasts = (page) => page.evaluate(() => [...document.querySelectorAll(".toast")].map((t) => t.textContent));
export const idle = (page) => waitFor(() => page.evaluate(() => !window.__lfManip.pending() && !window.__lfManip.snapping() && !window.__lfManip.dragging()), 30000);
export const lastOf = (rec, type, n = 3) => rec.filter((m) => m.type === type).slice(-n).map((m) => m.text || m);
export async function shot(page, name, el = null) {
  const path = `${OUT}/${name}.jpg`;
  if (el) await page.locator(el).first().screenshot({ path, type: "jpeg", quality: 70 });
  else await page.screenshot({ path, type: "jpeg", quality: 70 });
  return path;
}
export function attachErrors(page, errs) {
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`console: ${m.text()}`.slice(0, 300)); });
}
