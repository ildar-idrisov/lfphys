// p04: the u_max event's text (X14, P7) and the «Эталоны» row of the body-force Poiseuille channel, made visible.
import { chromium } from "playwright";
const port = process.argv[2] || "8615";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cmd = (id, c, a) => post(`/api/runs/${id}/command`, { cmd: c, args: a || {} });
async function waitRun(id) { for (let k = 0; k < 600; k++) { const m = await get(`/api/runs/${id}`); if (m.state === "running") return m; await sleep(500); } throw new Error("timeout"); }
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const out = [];
const scene = { format: "lfscene", version: 1, objects: [
  { type: "periodic", label: "Периодичность по x", values: { axis: "x" } },
  { type: "gravity", label: "Сила вдоль канала", values: { gx: 1.0, gy: 0.0 } }] };
const r = await post("/api/runs", { viz: "p04_fluids", params: { fluid: "custom", rho: 1.0, nu: 1e-3, Lx: 0.016, Ly: 0.016, nx: 16, u_max: 0.05, dye: "off", scene }, seed: 1 });
await waitRun(r.id);
await cmd(r.id, "play");
await sleep(6000);
const page = await br.newPage({ viewport: { width: 1600, height: 1000 } });
const errs = [];
page.on("pageerror", (e) => errs.push(e.message));
await page.goto(`${base}/run?id=${r.id}`);
await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
await sleep(2000);
await cmd(r.id, "set", { values: { nx: 32 } });
await sleep(1500);
await cmd(r.id, "set", { values: { u_max: 0.1 } });
await page.waitForFunction(() => /сжимаемость схемы, не жидкости/.test(document.body.innerText), null, { timeout: 60000 });
await sleep(2000);
await page.getByText("Эталоны", { exact: false }).first().click().catch(() => null);
await sleep(800);
await page.screenshot({ path: "/pw/shots_lpl/p04_etalons_open.png" });
const ev = page.getByText("сжимаемость схемы, не жидкости", { exact: false }).last();
await ev.scrollIntoViewIfNeeded().catch(() => null);
await sleep(500);
await page.screenshot({ path: "/pw/shots_lpl/p04_event_umax.png" });
out.push({ run: r.id, errors: errs.slice(0, 5), pois: await page.evaluate(() => /Пуазейль под объёмной силой/.test(document.body.innerText)) });
await page.close();
await cmd(r.id, "pause");
await br.close();
console.log(JSON.stringify(out));
