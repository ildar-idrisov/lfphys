// Review of the B1 corrections (reviewer's script): the slice window's axis names and tick values against the true
// coordinates of the points (the window's own readout under the cursor), for planes whose in-plane axes point along
// -x or -y, and for an origin moved within the plane. The tick values the window draws are m.s / m.tt (or the depth
// o_z + t v_z) and its axis names follow slices.js draw(): hName / vName. Own server (port 8498); run stopped at the end.
import { createRequire } from "module";
import fs from "fs";
const require = createRequire("/pw/node_modules/x.js");
const { chromium } = require("playwright");
const BASE = "http://127.0.0.1:8498";
const OUT = "/rev/out";
const LOG = `${OUT}/07c_window_axes.txt`;
fs.writeFileSync(LOG, "");
const log = (...a) => { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); console.log(s); fs.appendFileSync(LOG, s + "\n"); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function api(path, body) {
  const r = await fetch(BASE + path, { method: body ? "POST" : "GET", headers: { "content-type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  return r.json();
}
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const ids = [];
try {
  const { id } = await api("/api/runs", { viz: "v08_wave_3d", preset: "double", params: { n: 128, zmax: 12 } });
  ids.push(id);
  const page = await browser.newPage({ viewport: { width: 1680, height: 1000 } });
  await page.goto(`${BASE}/run?id=${id}`);
  await page.waitForSelector(".s3d-view");
  const ready = async (tag) => {
    for (let i = 0; i < 240; i++) {
      const ok = await page.evaluate((t) => { const s = document.querySelector(".s3d-view").__scene3d; const P = s.planes()[0]; return P && P.data && P.data.meta && JSON.stringify(P.data.meta.normal) !== t && !document.querySelector(".slicewin .sw-status .warn"); }, tag);
      if (ok) return; await sleep(500);
    }
  };
  await ready("x");
  const cases = [
    ["transverse, normal -z (theta 180)", { normal: [0, 0, -1], origin: [0, 0, 6] }],
    ["tilted 17 deg from z, u = -x", { normal: [0, 0.3, 0.95], origin: [0, 0, 6] }],
    ["longitudinal y = 0, origin moved to x = 3", { normal: [0, -1, 0], origin: [3, 0, 6] }],
    ["longitudinal, normal +y (u = -x)", { normal: [0, 1, 0], origin: [0, 0, 6] }],
  ];
  let k = 0;
  for (const [label, pose] of cases) {
    const prev = await page.evaluate(() => JSON.stringify(document.querySelector(".s3d-view").__scene3d.planes()[0].data.meta.normal));
    await api(`/api/runs/${id}/command`, { cmd: "view", args: { op: "plane", id: 1, ...pose } });
    await sleep(800);
    await ready(pose.normal.join() === JSON.parse(prev).join() ? "none" : prev);
    await sleep(1200);
    const m = await page.evaluate(() => document.querySelector(".s3d-view").__scene3d.planes()[0].data.meta);
    const longi = Math.abs(m.v[2]) > 0.5;
    const axisName = (u) => (Math.abs(Math.abs(u[0]) - 1) < 1e-9 ? (u[0] > 0 ? "" : "−") + "x" : Math.abs(Math.abs(u[1]) - 1) < 1e-9 ? (u[1] > 0 ? "" : "−") + "y" : "s");
    const hName = longi ? "z" : (Math.abs(m.u[0]) > 0.999 ? "x" : axisName(m.u));
    const vName = longi ? axisName(m.u) : (Math.abs(m.v[1]) > 0.999 ? "y" : "t");
    const hR = longi ? [m.origin[2] + m.tt[0] * m.v[2], m.origin[2] + m.tt[1] * m.v[2]] : [m.s[0], m.s[1]];
    const vR = longi ? [m.s[0], m.s[1]] : [m.tt[0], m.tt[1]];
    const cv = page.locator(".slicewin").nth(0).locator("canvas");
    const b = await cv.boundingBox();
    // the image box: left 44, top 6; its size from the window's own geometry is not exposed: probe the readout
    const probe = async (x, y) => { await page.mouse.move(b.x + x, b.y + y); await sleep(120); return page.locator(".slicewin").nth(0).locator(".sw-readout").textContent(); };
    const left = await probe(46, b.height / 2), top = await probe(b.width / 3, 8);
    log(`${label}: u ${JSON.stringify(m.u)}, v ${JSON.stringify(m.v)}, origin ${JSON.stringify(m.origin)}`);
    log(`   horizontal axis named '${hName}', ticks ${hR[0].toFixed(3)} (left) .. ${hR[1].toFixed(3)} (right); readout at the left edge: ${left}`);
    log(`   vertical axis named '${vName}', ticks ${vR[0].toFixed(3)} (bottom) .. ${vR[1].toFixed(3)} (top); readout at the top edge: ${top}`);
    await page.locator(".slicewin").nth(0).screenshot({ path: `${OUT}/07o_axes_case${++k}.png` });
  }
  await api(`/api/runs/${id}/stop`, {});
} catch (e) {
  log("FAILED:", String(e && e.stack || e));
} finally {
  for (const id of ids) { try { await api(`/api/runs/${id}/stop`, {}); } catch (e) { /* stopped */ } }
  await browser.close();
  log("runs stopped:", ids);
}
