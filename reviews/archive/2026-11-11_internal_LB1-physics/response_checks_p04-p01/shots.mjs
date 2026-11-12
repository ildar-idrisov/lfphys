// Review LB1 processing (p04/p01): the visible fixes in the browser — p04's transfer event (P7, X14), the body-force
// Poiseuille reference, a new nx's height (P14), a new world keeping the flow (F5); p01's «what if» by the engine's rule
// (P5, P6). Private server only. Prints JSON; screenshots into /pw/shots_lpl/.
import { chromium } from "playwright";
import fs from "fs";
const port = process.argv[2] || "8615";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cmd = (id, c, a) => post(`/api/runs/${id}/command`, { cmd: c, args: a || {} });
async function waitRun(id) { for (let k = 0; k < 600; k++) { const m = await get(`/api/runs/${id}`); if (m.state === "running") return m; await sleep(500); } throw new Error("timeout"); }
fs.mkdirSync("/pw/shots_lpl", { recursive: true });
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const out = [];
async function open(id) {
  const page = await br.newPage({ viewport: { width: 1600, height: 1000 } });
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message));
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
  await sleep(2500);
  return { page, errs };
}
async function waitText(page, re, what) {
  const t0 = Date.now();
  const ok = await page.waitForFunction((s) => new RegExp(s).test(document.body.innerText), re, { timeout: 60000 }).then(() => true).catch(() => false);
  out.push({ what, ok, ms: Date.now() - t0 });
  return ok;
}
const scene = { format: "lfscene", version: 1, objects: [
  { type: "periodic", label: "Периодичность по x", values: { axis: "x" } },
  { type: "gravity", label: "Сила вдоль канала", values: { gx: 1.0, gy: 0.0 } }] };
if (process.argv[3] !== "p01") {
{
  const params = { fluid: "custom", rho: 1.0, nu: 1e-3, Lx: 0.016, Ly: 0.016, nx: 16, u_max: 0.05, dye: "off", scene };
  const r = await post("/api/runs", { viz: "p04_fluids", params, seed: 1 });
  await waitRun(r.id);
  await cmd(r.id, "speed", { value: 1.0 });
  await cmd(r.id, "play");
  await sleep(6000);
  const { page, errs } = await open(r.id);
  await waitText(page, "Пуазейль под объёмной силой", "p04: the body-force Poiseuille reference in «Эталоны»");
  await cmd(r.id, "set", { values: { nx: 32 } });
  await waitText(page, "сходятся по построению", "p04: nx 16 -> 32, the event says the balances cannot see the transfer");
  await sleep(3000);
  await page.screenshot({ path: "/pw/shots_lpl/p04_force_poiseuille_nx32.png" });
  await cmd(r.id, "set", { values: { u_max: 0.1 } });
  await waitText(page, "сжимаемость схемы, не жидкости", "p04: u_max 0.05 -> 0.1, the mass change attributed to the scheme");
  await sleep(3000);
  await page.screenshot({ path: "/pw/shots_lpl/p04_umax_compressibility.png" });
  const kept = { ...params, fluid: "custom", rho: 1.0, nu: 1.2e-3 };
  delete kept.scene;
  await cmd(r.id, "new_world", { params: { ...kept, nx: 24, u_max: 0.1 }, carry: true });
  await waitText(page, "течение перенесено с сетки", "p04: a new world keeps the flow (another grid: by the engine's transfer)");
  await sleep(3000);
  await page.screenshot({ path: "/pw/shots_lpl/p04_new_world_keeps_flow.png" });
  out.push({ run: r.id, errors: errs.slice(0, 5) });
  await page.close();
  await cmd(r.id, "pause");
}
{
  const r = await post("/api/runs", { viz: "p04_fluids", preset: "cylinder_re20", seed: 1 });
  await waitRun(r.id);
  await cmd(r.id, "play");
  await sleep(5000);
  const { page, errs } = await open(r.id);
  await cmd(r.id, "set", { values: { nx: 333 } });
  await waitText(page, "высота области 0,41 → 0,40961", "p04: nx 333 states the new height and the nx keeping both lengths");
  await sleep(3000);
  await page.screenshot({ path: "/pw/shots_lpl/p04_nx333_height.png" });
  out.push({ run: r.id, errors: errs.slice(0, 5) });
  await page.close();
  await cmd(r.id, "pause");
}
}
{
  const r = await post("/api/runs", { viz: "p01_gravity", preset: "kerr_orbits", seed: 1 });
  await waitRun(r.id);
  await cmd(r.id, "play");
  await sleep(5000);
  const { page, errs } = await open(r.id);
  const hole = (await get(`/api/runs/${r.id}`));
  await cmd(r.id, "scene", { op: "set", id: "o8", values: { spin: 0.95 } });
  await waitText(page, "kn_change_whatif", "p01: the «what if» names the engine's rule");
  await waitText(page, "длина окружности", "p01: the event gives the circumferential radius's change");
  await sleep(3000);
  await page.screenshot({ path: "/pw/shots_lpl/p01_whatif_event.png" });
  out.push({ run: r.id, errors: errs.slice(0, 5), meta_state: hole.state });
  await page.close();
  await cmd(r.id, "pause");
}
await br.close();
console.log(JSON.stringify(out, null, 1));
