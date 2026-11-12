// B3 review, check 9: v10 and v11 in headless Chromium (WebGL by SwiftShader) against the reviewer's own server on
// port 8503 (engine mounted read-only, runs in the reviewer's scratchpad), started from engine/ with
//   docker run -d --name b3rev-viz8503 --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf:ro \
//     -v <scratchpad>/b3rev_runs:/lf/visualizations/runs -p 8503:8479 -w /lf/visualizations light-funnel-viz \
//     python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 3
// and stopped with `docker stop b3rev-viz8503 && docker rm b3rev-viz8503`. Then, from this review folder, with a
// node_modules holding playwright@1.58.2 mounted beside it:
//   docker run --rm --init --shm-size=2g --network host --user "$(id -u):$(id -g)" \
//     -v <node_modules>:/w/node_modules:ro -v "$PWD":/w/src:ro -v "$PWD/out/browser":/o -w /w -e HOME=/tmp \
//     mcr.microsoft.com/playwright:v1.58.2-jammy node /w/src/c09_browser.mjs /o > out/c09_browser.txt
// (run of 2026-10-28: out/c09_browser.txt and the screenshots out/browser/c09_*.png)
// (A) v11 "narrow" at t = 0 and at its end: the panels' texts, the plane's window (fixed: no ✕), the scene's layers,
//     the checks; the timeline moved back: what the wave window and the screen panel show then;
// (B) v11 small geometry with a live change (slit B closed in flight) and a refused one (a mark without spin);
// (C) v10 "terrell": the camera window, its readout under the cursor, a live boost, the comparison modes; the other
//     presets: page errors and failed checks.
import { chromium } from "playwright";
const OUT = process.argv[2] || ".";
const base = "http://127.0.0.1:8503";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const errs = [], out = {};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function open(viz, preset, wait = 8000, params) {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
  page.on("pageerror", (e) => errs.push(`${viz}/${preset} pageerror: ${e.stack}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`${viz}/${preset} console: ${m.text()}`); });
  const r = await post("/api/runs", { viz, preset, params, seed: 5 });
  if (!r.id) throw new Error(JSON.stringify(r));
  await page.goto(base + "/run?id=" + r.id);
  await page.waitForTimeout(wait);
  return [page, r.id];
}
const cmd = (id, c, args) => post(`/api/runs/${id}/command`, { cmd: c, args });
const S = (page, f, a) => page.evaluate(f, a);
const panels = (page) => S(page, () => [...document.querySelectorAll(".panel")].map((p) => p.innerText.replace(/\n+/g, " | ").slice(0, 900)));
const failedChecks = (page) => S(page, () => [...document.querySelectorAll("tr")].filter((tr) => tr.querySelector(".st-bad")).map((tr) => tr.innerText.replace(/\s+/g, " ").slice(0, 300)));
const allChecks = (page) => S(page, () => [...document.querySelectorAll("tr")].filter((tr) => tr.querySelector(".st-ok,.st-bad,.st-na")).map((tr) => tr.innerText.replace(/\s+/g, " ").slice(0, 220)));
const layers = (page) => S(page, () => { const v = document.querySelector(".s3d-view"); return v && v.__scene3d ? v.__scene3d.layers().map((L) => `${L.id}${L.visible ? "" : " (off)"}: ${L.label}`) : null; });
const sliceWins = (page) => S(page, () => [...document.querySelectorAll(".slicewin")].map((b) => ({ title: (b.querySelector(".sw-title") || {}).innerText, status: (b.querySelector(".sw-status") || {}).innerText, delVisible: [...b.querySelectorAll("button")].some((x) => x.textContent === "✕" && x.offsetParent !== null) })));
const topbar = (page) => S(page, () => ({ title: document.getElementById("title").innerText, scene: document.getElementById("scene").innerText, physics: document.getElementById("physics").innerText.slice(0, 600), time: document.getElementById("time").innerText }));

async function waitFor(page, f, ms) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { if (await S(page, f)) return true; await sleep(1000); }
  return false;
}

// (A) v11 narrow
{
  const [page, id] = await open("v11_double_slit_2d", "narrow", 10000);
  out.v11_t0 = { top: await topbar(page), panels: await panels(page), windows: await sliceWins(page), layers: await layers(page), checks: await allChecks(page) };
  await page.screenshot({ path: `${OUT}/c09_v11_narrow_t0.png` });
  await cmd(id, "speed", { value: 1 }); await cmd(id, "play", {});
  await page.waitForTimeout(12000);
  out.v11_mid = { top: await topbar(page), panels: await panels(page) };
  await page.screenshot({ path: `${OUT}/c09_v11_narrow_mid.png` });
  const done = await waitFor(page, () => /на экран\s/.test([...document.querySelectorAll(".panel")].map((p) => p.innerText).join(" ")) && /частиц Бома на экране/.test(document.body.innerText), 240000);
  await page.waitForTimeout(3000);
  out.v11_end = { done, top: await topbar(page), panels: await panels(page), windows: await sliceWins(page), layers: await layers(page), failed: await failedChecks(page), checks: await allChecks(page) };
  await page.screenshot({ path: `${OUT}/c09_v11_narrow_end.png` });
  // the timeline moved back to a third of the history: the wave window rewinds; what does the screen panel show?
  await S(page, () => { const tl = document.getElementById("timeline"); tl.value = String(Math.floor(Number(tl.max) / 3)); tl.dispatchEvent(new Event("input")); });
  await page.waitForTimeout(2500);
  out.v11_back = { top: await topbar(page), panels: await panels(page), windows: await sliceWins(page) };
  await page.screenshot({ path: `${OUT}/c09_v11_narrow_scrolled_back.png` });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
// (B) v11: live change and a refused change
{
  const small = { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 300, n_tracks: 20 };
  const [page, id] = await open("v11_double_slit_2d", "narrow", 6000, small);
  await cmd(id, "speed", { value: 2e-18 }); await cmd(id, "play", {});
  await page.waitForTimeout(4000);
  await cmd(id, "set", { values: { slit_b: false } });
  await page.waitForTimeout(3000);
  out.v11_live = { top: await topbar(page), panels: await panels(page), plate: await S(page, () => { const v = document.querySelector(".s3d-view").__scene3d; return (v.state.desc.objects || []).filter((o) => o.id === "plate").map((o) => o.holes); }) };
  await cmd(id, "set", { values: { mark_deg: 90 } });
  await page.waitForTimeout(3000);
  out.v11_refused = { events: await S(page, () => document.body.innerText.match(/[^\n]*метк[^\n]*/gi)), panels: await panels(page) };
  await page.screenshot({ path: `${OUT}/c09_v11_live.png` });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
// (C) v10
{
  const [page, id] = await open("v10_fast_observer", "terrell", 10000);
  out.v10_t0 = { top: await topbar(page), panels: await panels(page), layers: await layers(page), checks: await allChecks(page),
                 img: await S(page, () => { const w = document.querySelector(".s3d-windows").__imagewin || [...document.querySelectorAll(".s3d-windows")].map((e) => e.__imagewin).find(Boolean); const c = w && w.current(); return c ? { shape: c.meta.shape, mode: c.meta.mode, t: c.meta.t } : null; }) };
  // the readout under the cursor at the image's centre and at a quarter
  const cv = await page.$(".imgwin canvas");
  const bb = await cv.boundingBox();
  const reads = [];
  for (const [fx, fy] of [[0.5, 0.5], [0.3, 0.5], [0.7, 0.45]]) { await page.mouse.move(bb.x + fx * bb.width, bb.y + fy * bb.height); await page.waitForTimeout(300); reads.push(await S(page, () => document.querySelector(".imgwin .sw-readout").innerText)); }
  out.v10_readout = reads;
  await page.screenshot({ path: `${OUT}/c09_v10_terrell_t0.png` });
  await cmd(id, "play", {}); await page.waitForTimeout(6000);
  await cmd(id, "set", { values: { obs_beta: 0.9, obs_theta: 90, obs_phi: 0 } });
  await page.waitForTimeout(4000);
  out.v10_boost = { top: await topbar(page), panels: await panels(page), failed: await failedChecks(page) };
  await page.screenshot({ path: `${OUT}/c09_v10_terrell_boost.png` });
  for (const mode of ["snapshot", "geometry", "doppler", "delay"]) {
    await cmd(id, "set", { values: { image: mode } }); await page.waitForTimeout(2500);
    out[`v10_mode_${mode}`] = { status: await S(page, () => document.querySelector(".imgwin .sw-status").innerText), panel: (await panels(page)).filter((t) => /Изображение/.test(t)) };
    await page.mouse.move(bb.x + 0.5 * bb.width, bb.y + 0.5 * bb.height); await page.waitForTimeout(300);
    out[`v10_mode_${mode}`].readout = await S(page, () => document.querySelector(".imgwin .sw-readout").innerText);
    await page.screenshot({ path: `${OUT}/c09_v10_mode_${mode}.png` });
  }
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
for (const preset of ["city", "sky", "train", "rest", "terrell_099", "snapshot"]) {
  const [page, id] = await open("v10_fast_observer", preset, 9000);
  await cmd(id, "play", {}); await page.waitForTimeout(6000);
  out[`v10_${preset}`] = { top: await topbar(page), failed: await failedChecks(page), checks: await allChecks(page) };
  await page.screenshot({ path: `${OUT}/c09_v10_${preset}.png` });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
console.log(JSON.stringify(out, null, 1));
console.log(errs.length ? errs.join("\n") : "no page errors");
await browser.close();
