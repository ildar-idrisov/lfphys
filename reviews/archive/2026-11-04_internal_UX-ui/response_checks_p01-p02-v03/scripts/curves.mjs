// G1 response check (U2, U18): p01's orbits seen from above, zoomed, at the default speed (x1) and ten times faster
// (x10), and the Newtonian hole with its stars; on the server of PORT (the tree after the fix) or of the snapshot before.
import { base, browser, newRun, sleep, post, openRun } from "./common.mjs";
import fs from "fs";
const tag = process.argv[2] || "after";
const b = await browser();
fs.mkdirSync("/pw/shots", { recursive: true });
async function top3d(page, wheel) {
  await page.evaluate(() => { const bs = [...document.querySelectorAll(".s3d-tools button")]; const t = bs.find((x) => /Сверху/.test(x.textContent)); if (t) t.click(); });
  await sleep(400);
  const v = await page.$eval(".s3d-view", (e) => { const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height }; });
  await page.mouse.move(v.x, v.y);
  for (let i = 0; i < wheel; i++) { await page.mouse.wheel(0, -200); await sleep(60); }
  await sleep(700);
  return v;
}
const out = [];
for (const [name, body, factor, wheel, secs] of [
  ["inner_x1", { preset: "inner" }, 1, 6, 6],
  ["inner_x10", { preset: "inner" }, 10, 6, 6],
  ["hole_x1", { preset: "hole_stars" }, 1, 3, 6],
]) {
  const id = await newRun("p01_gravity", body);
  const { page, ctx, logs } = await openRun(b, id);
  if (factor !== 1) await post(`/api/runs/${id}/command`, { cmd: "speed", args: { value: 3.15576e7 * factor } });
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  await sleep(secs * 1000);
  await post(`/api/runs/${id}/command`, { cmd: "pause" });
  await sleep(800);
  const v = await top3d(page, wheel);
  const side = Math.min(v.w, v.h) * 0.85;
  await page.screenshot({ path: `/pw/shots/${tag}_${name}.jpg`, type: "jpeg", quality: 80, clip: { x: v.x - side / 2, y: v.y - side / 2, width: side, height: side } });
  out.push({ tag, name, run: id, speed: await page.textContent("#speedv").catch(() => null), logs: logs.slice(0, 5) });
  await ctx.close(); await post(`/api/runs/${id}/stop`, {});
}
console.log(JSON.stringify(out, null, 1));
fs.writeFileSync(`/pw/out_curves_${tag}.json`, JSON.stringify(out, null, 1));
await b.close();
