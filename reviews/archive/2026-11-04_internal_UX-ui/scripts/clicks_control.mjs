// Control for U14: the same human click (button held 150 ms) on the first line of «События», once while the world
// records and once while it is paused (no rebuilds of the list), alternating, 8 times each.
import { browser, newRun, openRun, play, sleep, post } from "./common.mjs";
import fs from "fs";
const b = await browser();
const id = await newRun("v04_orbits", { preset: "default" });
const { page, ctx } = await openRun(b, id);
await post(`/api/runs/${id}/command`, { cmd: "speed", args: { value: 0.1 } });
await play(page);
await sleep(5000);
const out = { recording: [], paused: [] };
async function humanClick() {
  await page.keyboard.press("End"); await sleep(400);
  const r = await page.evaluate(() => { const e = document.querySelector(".events .ev"); if (!e) return null; e.scrollIntoView({ block: "center" }); const b = e.getBoundingClientRect(); if (b.bottom > innerHeight || b.top < 0) return null; return { x: b.left + 40, y: b.top + b.height / 2 }; });
  if (!r) return "no event line";
  await page.mouse.move(r.x, r.y); await page.mouse.down(); await sleep(150); await page.mouse.up();
  await sleep(500);
  return /история/.test(await page.textContent("#status")) ? "jumped" : "no jump";
}
for (let k = 0; k < 8; k++) {
  if (!/запись/.test(await page.textContent("#rec"))) await page.click("#rec");
  await sleep(1500);
  out.recording.push(await humanClick());
  await page.keyboard.press("End"); await sleep(300);
  await post(`/api/runs/${id}/command`, { cmd: "pause" });
  await sleep(1500);
  out.paused.push(await humanClick());
}
console.log(JSON.stringify(out));
fs.writeFileSync("/pw/out_clicks_control.json", JSON.stringify(out, null, 1));
await ctx.close(); await post(`/api/runs/${id}/stop`, {});
await b.close();
