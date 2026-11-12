// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Response check (written by the responder): B2-2 (nothing of the result at t = 0; the lab box grows), B2-7 (a diagonal plane's outline), v08 unchanged; own server on port 8499 (engine read-only, temporary runs folder).
const base = "http://127.0.0.1:8499";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const errs = [], out = {};
async function open(viz, preset, params) {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
  page.on("pageerror", (e) => errs.push(`${viz}/${preset} pageerror: ${e.stack}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`${viz}/${preset} ${m.text()}`); });
  const r = await post("/api/runs", { viz, preset, params, seed: 3 });
  await page.goto(base + "/run?id=" + r.id);
  await page.waitForTimeout(7000);
  return [page, r.id];
}
const cmd = (id, c, args) => post(`/api/runs/${id}/command`, { cmd: c, args });
const S = (page, f) => page.evaluate(f);
const text = (page) => S(page, () => document.body.innerText);
{ // B2-2: at t = 0 no duration, no proper time at the end, no largest gamma
  const [page, id] = await open("v09_thomas_3d", "thomas");
  const t0 = await text(page);
  out.t0_has_duration = /по часам корабля|наибольшая γ\s/.test(t0);
  out.t0_has_so_far = /наибольшая γ до сих пор/.test(t0);
  await page.screenshot({ path: "b2r_thomas_t0.png" });
  await cmd(id, "speed", { value: 1e12 }); await cmd(id, "play", {}); await page.waitForTimeout(5000);
  const t1 = await text(page);
  out.end_has_duration = /по часам корабля/.test(t1);
  out.end_accumulated = (t1.match(/накопленный угол \(по ходу расчёта\)\s*\n?\s*([^\n]*)/) || [])[1];
  // B2-7: a diagonal plane outlined with 4 corners
  await cmd(id, "view", { op: "plane", id: 2, normal: [1, -1, 0], origin: [0, 0, 0] }); await page.waitForTimeout(3000);
  out.diag_poly = await S(page, () => document.querySelector(".s3d-view").__scene3d.planes().filter((P) => P.id === 2).map((P) => P.poly.length));
  await page.screenshot({ path: "b2r_thomas_end.png" });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
{ // B2-2: the lab box grows
  const [page, id] = await open("v09_thomas_3d", "lab");
  out.lab_box0 = await S(page, () => document.querySelector(".s3d-view").__scene3d.state.box[1][0]);
  await cmd(id, "speed", { value: 1e12 }); await cmd(id, "play", {}); await page.waitForTimeout(5000);
  out.lab_box1 = await S(page, () => document.querySelector(".s3d-view").__scene3d.state.box[1][0]);
  await page.screenshot({ path: "b2r_lab_end.png" });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
{
  const [page, id] = await open("v08_wave_3d", "gauss");
  await page.waitForTimeout(8000);
  await page.click("text=＋ Срез"); await page.waitForTimeout(4000);
  out.v08_planes = await S(page, () => document.querySelector(".s3d-view").__scene3d.planes().map((P) => P.poly.length));
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
console.log(JSON.stringify(out));
console.log(errs.length ? errs.join("\n") : "no page errors");
await browser.close();
