// U-curve screenshots: the playground's orbits seen from above and zoomed in, at the default speed and at a tenth of it
// (the same orbits: the corners come from the sampling, one point per frame); the Kerr preset; v04 zoomed as a
// control. Also: a raw traceback in the hard-disk world after «＋ Атом» (U-err).
import { base, browser, newRun, play, sleep, post } from "./common.mjs";
import fs from "fs";
const b = await browser();
fs.mkdirSync("/pw/shots", { recursive: true });
async function open(id, w = 1600, h = 1000) {
  const ctx = await b.newContext({ viewport: { width: w, height: h } });
  const page = await ctx.newPage();
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка/.test(document.getElementById("status").textContent), null, { timeout: 120000 });
  return { page, ctx };
}
async function top3d(page, wheel) {
  await page.evaluate(() => { const bs = [...document.querySelectorAll(".s3d-tools button")]; const t = bs.find((x) => /Сверху/.test(x.textContent)); if (t) t.click(); });
  await sleep(300);
  const v = await page.$eval(".s3d-view", (e) => { const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height, l: r.left, t: r.top }; });
  await page.mouse.move(v.x, v.y);
  for (let i = 0; i < wheel; i++) { await page.mouse.wheel(0, -200); await sleep(60); }
  await sleep(500);
  return v;
}
const out = [];
for (const [name, viz, body, speed, wheel, secs] of [
  ["p01_inner_default", "p01_gravity", { preset: "inner" }, null, 6, 6],
  ["p01_inner_tenth", "p01_gravity", { preset: "inner" }, 3.15576e6, 6, 25],
  ["p01_hole_default", "p01_gravity", { preset: "hole_stars" }, null, 4, 6],
  ["p01_kerr_default", "p01_gravity", { preset: "kerr_orbits" }, null, 4, 15],
]) {
  const id = await newRun(viz, body);
  const { page, ctx } = await open(id);
  if (speed) await post(`/api/runs/${id}/command`, { cmd: "speed", args: { value: speed } });
  await play(page);
  await sleep(secs * 1000);
  await post(`/api/runs/${id}/command`, { cmd: "pause" });
  await sleep(500);
  const v = await top3d(page, wheel);
  const side = Math.min(v.w, v.h) * 0.8;
  await page.screenshot({ path: `/pw/shots/curve_${name}.jpg`, type: "jpeg", quality: 75, clip: { x: v.x - side / 2, y: v.y - side / 2, width: side, height: side } });
  out.push({ name, run: id, actual_speed: await page.textContent("#speedv"), fact: await page.textContent("#speedfact") });
  await ctx.close(); await post(`/api/runs/${id}/stop`, {});
}
{ // v04 zoomed 25x on the orbit: the control (240 samples per turn)
  const id = await newRun("v04_orbits", { preset: "default" });
  const { page, ctx } = await open(id);
  await play(page); await sleep(8000);
  await post(`/api/runs/${id}/command`, { cmd: "pause" }); await sleep(500);
  const c = await page.$eval(".center canvas", (e) => { const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; });
  // the orbit's point at r0 = 20 M on +x: zoom about it
  await page.mouse.move(c.x + c.w * 0.5 + 60, c.y + c.h * 0.55);
  for (let i = 0; i < 12; i++) { await page.mouse.wheel(0, -250); await sleep(60); }
  await sleep(500);
  await page.screenshot({ path: "/pw/shots/curve_v04_zoom.jpg", type: "jpeg", quality: 75, clip: { x: c.x, y: c.y, width: c.w, height: c.h } });
  out.push({ name: "v04_zoom", run: id });
  await ctx.close(); await post(`/api/runs/${id}/stop`, {});
}
{ // the hard-disk world: one atom from the palette, then ⏺
  const id = await newRun("p03_molecules", { params: { dim: "2d", model: "hard" } });
  const { page, ctx } = await open(id, 1280, 800);
  const all = await page.$$(".pg-buttons button");
  for (const x of all) if (/Атом/.test(await x.textContent())) { await x.click(); break; }
  await sleep(1500);
  if (!/запись/.test(await page.textContent("#rec"))) await page.click("#rec");
  await sleep(3000);
  await page.evaluate(() => { for (const p of document.querySelectorAll(".panel.closed")) p.classList.remove("closed"); });
  await page.screenshot({ path: "/pw/shots/err_p03_hard_atom.jpg", type: "jpeg", quality: 70 });
  const toasts = await page.$$eval(".toast", (ts) => ts.map((t) => t.textContent.slice(0, 600)));
  const evs = await page.$$eval(".events .ev", (ts) => ts.map((t) => t.textContent.slice(0, 300)));
  out.push({ name: "p03_hard_atom", run: id, status: await page.textContent("#status"), toasts, events: evs.slice(-4) });
  await ctx.close(); await post(`/api/runs/${id}/stop`, {});
}
console.log(JSON.stringify(out));
fs.writeFileSync("/pw/out_polyshot.json", JSON.stringify(out, null, 1));
await b.close();
