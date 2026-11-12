// Before/after screenshots for the leftovers of review UX-ui (U12 v11-v14, U15 p02, U19 v11/v12).
// PORT, TAG in the environment; cases as arguments (default: all). Screenshots to /pw/shots/<TAG>_<case>.jpg; one JSON
// line per case with what was measured.
import { chromium } from "playwright";
const port = process.env.PORT, tag = process.env.TAG, base = `http://127.0.0.1:${port}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const only = process.argv.slice(2);
const b = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });

async function start(viz, body) {
  let r = null;
  for (let k = 0; k < 60; k++) { r = await post("/api/runs", { viz, seed: 3, ...body }); if (r.id || !/вычислител/.test(r.error || "")) break; await sleep(3000); }
  if (!r.id) throw new Error("not started: " + JSON.stringify(r).slice(0, 300));
  return r.id;
}
async function open(id, w, h) {
  const ctx = await b.newContext({ viewport: { width: w, height: h } });
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`console: ${m.text()}`.slice(0, 300)); });
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 240000 });
  return { ctx, page, errs };
}
const stop = (id) => post(`/api/runs/${id}/stop`, {});
const cmd = (id, c, args) => post(`/api/runs/${id}/command`, { cmd: c, args });
async function sizes(page) {
  return page.evaluate(() => {
    const r = (q) => { const e = document.querySelector(q); if (!e || !e.offsetParent) return null; const b = e.getBoundingClientRect(); return [Math.round(b.width), Math.round(b.height)]; };
    return { window: r(".sw-canvas"), scene3d: r(".s3d-view canvas") };
  });
}
// the labels of the parameters as the player shows them (live panel and the new-world form)
async function labels(page) {
  return page.evaluate(() => [...document.querySelectorAll("#left label, #left .field label")].map((l) => l.textContent.trim()).filter((s) => s));
}

const CASES = {
  // U15: p02's 2-D double slit: the plane's window against the 3-D view, at both sizes
  async p02(w = 1600, h = 1000) {
    const id = await start("p02_quantum", { preset: "double_slit" });
    const { ctx, page, errs } = await open(id, w, h);
    await cmd(id, "play", {}); await sleep(6000);
    const s = await sizes(page);
    await page.screenshot({ path: `/pw/shots/${tag}_p02_double_slit_${w}.jpg`, type: "jpeg", quality: 70 });
    let toggled = null;
    const btn = await page.$("button:has-text('3D-вид')");
    if (btn) {
      await btn.click(); await sleep(1500);
      toggled = await sizes(page);
      await page.screenshot({ path: `/pw/shots/${tag}_p02_double_slit_${w}_with3d.jpg`, type: "jpeg", quality: 70 });
      await btn.click(); await sleep(500);
    }
    console.log(JSON.stringify({ tag, case: "p02", w, h, sizes: s, with3d: toggled, errs }));
    await stop(id); await ctx.close();
  },
  async p02small() { return CASES.p02(1280, 800); },
  // U15 control: p02 in space keeps its 3-D view
  async p02_3d() {
    const id = await start("p02_quantum", { preset: "ball_3d" });
    const { ctx, page, errs } = await open(id, 1600, 1000);
    await cmd(id, "play", {}); await sleep(5000);
    const s = await sizes(page);
    await page.screenshot({ path: `/pw/shots/${tag}_p02_ball_3d_1600.jpg`, type: "jpeg", quality: 70 });
    console.log(JSON.stringify({ tag, case: "p02_3d", sizes: s, button: !!(await page.$("button:has-text('3D-вид')")), errs }));
    await stop(id); await ctx.close();
  },
  // U19 + U12: v11's left column (live set-up and the new world's form) with their labels
  async v11() {
    const id = await start("v11_double_slit_2d", { params: { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 100, n_tracks: 10 } });
    const { ctx, page, errs } = await open(id, 1600, 1000);
    await sleep(1500);
    const L = await labels(page);
    await page.screenshot({ path: `/pw/shots/${tag}_v11_left.jpg`, type: "jpeg", quality: 75, clip: { x: 0, y: 0, width: 520, height: 1000 } });
    // a live change of the slit width (after: applied in this world; before: not a live parameter)
    const r = await cmd(id, "set", { values: { a: 2.5 } });
    await sleep(4000);
    const run = await get(`/api/runs/${id}`);
    await cmd(id, "play", {}); await sleep(5000);
    await page.screenshot({ path: `/pw/shots/${tag}_v11_live_a.jpg`, type: "jpeg", quality: 70 });
    console.log(JSON.stringify({ tag, case: "v11", labels: L, set: r, worlds: (run.worlds || []).length, errs }));
    await stop(id); await ctx.close();
  },
  async v12() {
    const id = await start("v12_arrival_times_2d", { params: { grid: "coarse", n_bohm: 100, n_tracks: 10, L: 12.0, sigma_z: 2.0, sigma_x: 2.0 } });
    const { ctx, page, errs } = await open(id, 1600, 1000);
    await sleep(1500);
    const L = await labels(page);
    await page.screenshot({ path: `/pw/shots/${tag}_v12_left.jpg`, type: "jpeg", quality: 75, clip: { x: 0, y: 0, width: 520, height: 1000 } });
    console.log(JSON.stringify({ tag, case: "v12", labels: L, errs }));
    await stop(id); await ctx.close();
  },
  // U12: v13's state changed in the same world (after) or refused (before)
  async v13() {
    const id = await start("v13_hydrogen_3d", { preset: "2pz", params: { ng: 64 } });
    const { ctx, page, errs } = await open(id, 1600, 1000);
    await cmd(id, "play", {}); await sleep(3000);
    await page.screenshot({ path: `/pw/shots/${tag}_v13_2pz.jpg`, type: "jpeg", quality: 70 });
    const r = await cmd(id, "set", { values: { n: 3, l: 2, m: 0 } });
    await sleep(6000);
    const run = await get(`/api/runs/${id}`);
    await page.screenshot({ path: `/pw/shots/${tag}_v13_after_set.jpg`, type: "jpeg", quality: 70 });
    const r2 = await cmd(id, "set", { values: { mode: "super", n: 1, l: 0, m: 0, n2: 2, l2: 1, m2: 0 } });
    await sleep(8000);
    await page.screenshot({ path: `/pw/shots/${tag}_v13_super.jpg`, type: "jpeg", quality: 70 });
    const st = await page.evaluate(() => document.querySelector("#right") ? document.querySelector("#right").innerText.slice(0, 600) : "");
    console.log(JSON.stringify({ tag, case: "v13", set: r, set2: r2, worlds: (run.worlds || []).length, state: st, errs }));
    await stop(id); await ctx.close();
  },
  async v14() {
    const id = await start("v14_quarkonium_3d", { params: { ng: 64 } });
    const { ctx, page, errs } = await open(id, 1600, 1000);
    await cmd(id, "play", {}); await sleep(3000);
    const r = await cmd(id, "set", { values: { l: 1 } });
    await sleep(5000);
    const run = await get(`/api/runs/${id}`);
    await page.screenshot({ path: `/pw/shots/${tag}_v14_after_set.jpg`, type: "jpeg", quality: 70 });
    console.log(JSON.stringify({ tag, case: "v14", set: r, worlds: (run.worlds || []).length, errs }));
    await stop(id); await ctx.close();
  },
};
for (const k of Object.keys(CASES)) {
  if (only.length && !only.includes(k)) continue;
  try { await CASES[k](); } catch (e) { console.log(JSON.stringify({ tag, case: k, error: String(e).slice(0, 400) })); }
}
await b.close();
