// Review of the B1 corrections (reviewer's script): the 3-D scene with the slice planes hidden (is the light behind
// the screen visible as beams?), from the camera presets; the archived world's controls (can a plane still be
// edited?). Own server instance (port 8498); the run is stopped at the end.
import { createRequire } from "module";
import fs from "fs";
const require = createRequire("/pw/node_modules/x.js");
const { chromium } = require("playwright");
const BASE = "http://127.0.0.1:8498";
const OUT = "/rev/out";
const LOG = `${OUT}/07b_browser_views.txt`;
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
  const { id } = await api("/api/runs", { viz: "v08_wave_3d", preset: "double" });
  ids.push(id);
  const page = await browser.newPage({ viewport: { width: 1680, height: 1000 } });
  const sent = [];
  page.on("websocket", (ws) => ws.on("framesent", (f) => { if (typeof f.payload === "string") sent.push(f.payload); }));
  await page.goto(`${BASE}/run?id=${id}`);
  await page.waitForSelector(".s3d-view");
  for (let i = 0; i < 120; i++) { if (await page.evaluate(() => { const s = document.querySelector(".s3d-view").__scene3d; return s.planes().some((P) => P.data); })) break; await sleep(500); }
  await sleep(1500);
  const boxes = page.locator(".panel:has(h4:text('Слои сцены')) input[type=checkbox]");
  const labels = await page.locator(".panel:has(h4:text('Слои сцены')) label").allTextContents();
  log("layer labels:", labels);
  const iPlane = labels.findIndex((t) => t.includes("срез в 3D"));
  await boxes.nth(iPlane).uncheck();
  await sleep(400);
  for (const [btn, name] of [["Изо", "iso"], ["Сбоку", "side"], ["Сверху", "top"], ["С источника", "beam"]]) {
    await page.locator(".s3d-tools button", { hasText: btn }).first().click();
    await sleep(600);
    await page.locator(".s3d-view").screenshot({ path: `${OUT}/07m_cloud_${name}.png` });
  }
  // the volume look: density up
  await boxes.nth(iPlane).check();
  // the archived world: a new world, then world 1 from the record
  await api(`/api/runs/${id}/command`, { cmd: "new_world", args: { preset: "gauss" } });
  for (let i = 0; i < 120; i++) { if (await page.evaluate(() => document.querySelector("#world").options.length > 1)) break; await sleep(500); }
  await sleep(3000);
  await page.selectOption("#world", "0");
  await sleep(1500);
  await page.locator(".slicewin").nth(0).click();
  await sleep(500);
  const ctrls = await page.evaluate(() => {
    const p = [...document.querySelectorAll(".panel")].find((q) => q.querySelector("h4")?.textContent.startsWith("Срез"));
    return p ? [...p.querySelectorAll("input,button")].map((e) => e.disabled) : null;
  });
  const n0 = sent.length;
  // try to drag plane 1 of the archived world on screen and press Delete
  const pts = await page.evaluate(() => { const s = document.querySelector(".s3d-view").__scene3d; const P = s.planes()[0]; return [s.screenOf(P.origin), s.screenOf([P.origin[0] + 3, P.origin[1], P.origin[2]])]; });
  await page.mouse.move(pts[0][0], pts[0][1]); await page.mouse.down(); await page.mouse.move(pts[1][0], pts[1][1], { steps: 8 }); await page.mouse.up();
  await page.locator(".s3d-view").press("Delete");
  await sleep(800);
  log("archived world 1: plane panel controls disabled:", ctrls, "; commands sent after drag + Delete:", sent.slice(n0));
  await page.screenshot({ path: `${OUT}/07n_archived_selected.png` });
  await api(`/api/runs/${id}/stop`, {});
} catch (e) {
  log("FAILED:", String(e && e.stack || e));
} finally {
  for (const id of ids) { try { await api(`/api/runs/${id}/stop`, {}); } catch (e) { /* stopped */ } }
  await browser.close();
  log("runs stopped:", ids);
}
