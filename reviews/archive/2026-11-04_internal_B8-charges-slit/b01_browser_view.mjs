// Review B8 (v02 vector mode) in a browser against a PRIVATE server: three worlds, screenshots and panel texts.
import { chromium } from "playwright";
import fs from "fs";

const port = process.argv[2] || "8533";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const settle = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 600)))));

const jobs = [
  { name: "vector_narrow", body: { viz: "v02_double_slit", preset: "vector_narrow", seed: 3 } },
  { name: "vector_eff_dark", body: { viz: "v02_double_slit", preset: "vector_narrow", seed: 3, params: { eff: 0.2, dark_rate: 300 } } },
  { name: "eraser_pec", body: { viz: "v02_double_slit", preset: "photon_eraser", seed: 3, params: { screen_model: "pec", a_um: 2.0, d_um: 10.0, L2_m: 0.1 } } },
  { name: "default_switch", body: { viz: "v02_double_slit", preset: "photon_young", seed: 3 }, set: { screen_model: "pec" } },
];
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-accelerated-2d-canvas"] });
const out = {};
for (const job of jobs) {
  const errs = [];
  const r = await post("/api/runs", job.body);
  const id = r.id;
  if (!id) { out[job.name] = { error: r }; continue; }
  for (let i = 0; i < 120; i++) { const m = await get(`/api/runs/${id}`); if (m.state === "running") break; await sleep(500); }
  await post(`/api/runs/${id}/command`, { cmd: "speed", args: { value: 3 } });
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  await sleep(4000);
  let setResp = null;
  if (job.set) setResp = await post(`/api/runs/${id}/command`, { cmd: "set", args: { values: job.set } });
  await sleep(12000);
  await post(`/api/runs/${id}/command`, { cmd: "pause" });
  await sleep(1500);
  const page = await br.newPage({ viewport: { width: 1600, height: 1100 } });
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`console: ${m.text()}`.slice(0, 300)); });
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
  await settle(page);
  await page.screenshot({ path: `/out/b8rc_${job.name}.png`, fullPage: true });
  const texts = await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll("*")).filter((e) => e.children.length === 0 && /Модель экрана|Экран:|Попадания|T_TM|разность|Изменение не применено|шире/.test(e.textContent || ""));
    return all.map((e) => e.textContent.trim().slice(0, 600));
  });
  out[job.name] = { id, setResp, errs, texts: texts.slice(0, 30) };
  await page.close();
}
fs.writeFileSync("/out/b8rc_view.json", JSON.stringify(out, null, 1));
console.log(JSON.stringify(out, null, 1).slice(0, 6000));
await br.close();
