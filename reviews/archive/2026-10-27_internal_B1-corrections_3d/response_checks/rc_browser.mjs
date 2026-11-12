// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Response check (written by the responder): the browser checks of C2, C5, C10, C11 on the processed page, against
// an own server instance on port 8499 (engine mounted read-only, temporary runs folder). Output: rc_browser.txt.
import { chromium } from "playwright";
const base = "http://127.0.0.1:8499";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const errs = [];
const out = {};
async function open(preset) {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
  page.on("pageerror", (e) => errs.push(preset + " pageerror: " + e.message));
  page.on("console", (m) => { if (m.type() === "error") errs.push(preset + " " + m.text()); });
  const r = await post("/api/runs", { viz: "v08_wave_3d", preset, seed: 5 });
  await page.goto(base + "/run?id=" + r.id);
  await page.waitForTimeout(9000);
  return [page, r.id];
}
const cmd = (id, args) => post(`/api/runs/${id}/command`, { cmd: "view", args });
const sc = (page, f) => page.evaluate(f);
{
  const [page, id] = await open("double");
  // C5: turn plane 1, then add two planes
  await cmd(id, { op: "plane", id: 1, normal: [0.5, -0.866, 0] }); await page.waitForTimeout(4000);
  for (let i = 0; i < 2; i++) { await page.click("text=＋ Срез"); await page.waitForTimeout(4500); }
  out.normals = await sc(page, () => document.querySelector(".s3d-view").__scene3d.planes().map((P) => P.n));
  // C2: plane 3 transverse? set plane 3 to z = 15 with a centre at x = 5 (the run keeps the plane's own centre)
  await cmd(id, { op: "plane", id: 3, normal: [0, 0, 1], origin: [5, 0, 15] }); await page.waitForTimeout(4000);
  out.axes3 = await sc(page, () => document.querySelector(".s3d-windows").__slices.axes(3));
  await cmd(id, { op: "plane", id: 3, normal: [0, 0, -1], origin: [0, 0, 15] }); await page.waitForTimeout(4000);
  out.axes3_minus_z = await sc(page, () => document.querySelector(".s3d-windows").__slices.axes(3));
  out.axes1 = await sc(page, () => document.querySelector(".s3d-windows").__slices.axes(1));
  // C10: gizmo handles
  await page.click(".slicewin .sw-canvas"); await page.waitForTimeout(800);
  out.gizmo_translate = await sc(page, () => document.querySelector(".s3d-view").__scene3d.gizmoState());
  await page.keyboard.press("e"); await page.waitForTimeout(300);
  out.gizmo_rotate = await sc(page, () => document.querySelector(".s3d-view").__scene3d.gizmoState());
  await page.screenshot({ path: "rc_double.png" });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
{
  const [page, id] = await open("double_slices");
  out.reduced_outline = await sc(page, () => document.querySelector(".s3d-view").__scene3d.planes()[0].outline.material.color.getHexString());
  await page.screenshot({ path: "rc_slices.png" });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
console.log(JSON.stringify(out));
console.log(errs.length ? errs.join("\n") : "no page errors");
await browser.close();
